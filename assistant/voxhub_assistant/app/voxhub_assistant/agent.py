"""Claude agent: streaming Messages API with a manual tool loop and rolling memory."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import anthropic

from .config import Config
from .tools import HomeTools, ToolError, build_tools

_LOGGER = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 6

SYSTEM_PROMPT = """\
You are {name}, a voice assistant living in a small smart speaker in the user's home. \
You are connected to their Home Assistant installation and can look up and control their \
devices with the tools provided.

Everything you write is converted to speech and played through a small loudspeaker, and \
the user's words reach you through speech recognition. That shapes how you should answer:

- Keep answers short and conversational: usually one or two sentences. Give more detail \
only when asked for it.
- Write plain spoken language. No markdown, lists, headings, emoji, URLs or code, because \
a speech synthesizer would read the symbols aloud. Write numbers, units and times the way \
a person would say them.
- Speech recognition makes mistakes. If a request is slightly garbled, go with the most \
sensible interpretation; if it is truly unclear, ask one short clarifying question.
- Reply in the language the user speaks. The configured default language is "{language}".

Controlling the home:

- When you do not know the exact entity id, call search_entities first, then act. Do not \
guess entity ids. If several devices match and the right one is not obvious, ask which one.
- Do the action rather than describing how to do it, then confirm in a few words, for \
example "The kitchen light is on." Do not narrate what you are about to do before calling \
a tool.
- Only say something happened if the tool call succeeded. If a tool reports an error or the \
action is blocked by the add-on's safety settings (door locks and alarm panels are blocked \
by default), say so briefly and plainly.
- For questions about sensors, climate, media or weather, read the current state with the \
tools instead of answering from memory.

Each user message starts with a bracketed line giving the current local date and time; use \
it for time questions and do not read it back. For general knowledge questions, answer \
briefly from your own knowledge.{extra}"""

SPOKEN_ERRORS = {
    "auth": "Sorry, my Anthropic API key was rejected. Please check the add-on configuration.",
    "rate_limit": "Sorry, I'm being rate limited right now. Please try again in a moment.",
    "timeout": "Sorry, that took too long. Please try again.",
    "connection": "Sorry, I can't reach the internet right now.",
    "api": "Sorry, something went wrong while talking to Claude.",
    "refusal": "Sorry, I can't help with that.",
    "too_many_steps": "Sorry, that needed more steps than I can handle. Please try something simpler.",
}


@dataclass
class _Turn:
    user: str
    assistant: str


class ClaudeAgent:
    """Turns a transcript into a spoken reply, calling Home Assistant tools as needed."""

    def __init__(
        self,
        config: Config,
        tools: HomeTools,
        client: Any | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.config = config
        self.tools = tools
        # The SDK retries 429/5xx/connection errors itself; one retry keeps voice latency bounded.
        self.client = client or anthropic.AsyncAnthropic(
            api_key=config.anthropic_api_key, timeout=config.request_timeout, max_retries=1
        )
        self._now = now or (lambda: datetime.now().astimezone())
        self._history: list[_Turn] = []
        self._last_activity = 0.0
        extra = f"\n\n{config.system_prompt_extra.strip()}" if config.system_prompt_extra.strip() else ""
        # Static system prompt + static tool list: one cache breakpoint on the system block
        # caches both (render order is tools, then system). Volatile data such as the
        # current time goes into the user message, after the breakpoint.
        self._system = [
            {
                "type": "text",
                "text": SYSTEM_PROMPT.format(
                    name=config.assistant_name, language=config.language, extra=extra
                ),
                "cache_control": {"type": "ephemeral"},
            }
        ]
        self._tool_defs = build_tools(config.allowed_service_domains)

    def reset(self) -> None:
        self._history.clear()

    def _messages(self, text: str) -> list[dict[str, Any]]:
        if time.monotonic() - self._last_activity > self.config.conversation_timeout:
            self._history.clear()
        messages: list[dict[str, Any]] = []
        for turn in self._history:
            messages.append({"role": "user", "content": turn.user})
            messages.append({"role": "assistant", "content": turn.assistant})
        stamp = self._now().strftime("%A, %d %B %Y, %H:%M")
        messages.append({"role": "user", "content": f"[Local time: {stamp}]\n{text}"})
        return messages

    def _remember(self, user: str, assistant: str) -> None:
        # Only plain text is kept between turns. Thinking and tool blocks are replayed
        # unchanged inside a turn (required by the API) but never across turns, so
        # trimming old turns can never invalidate a preserved thinking block.
        self._last_activity = time.monotonic()
        if self.config.max_history_turns <= 0 or not assistant:
            return
        self._history.append(_Turn(user, assistant))
        del self._history[: -self.config.max_history_turns]

    async def respond(self, text: str) -> AsyncIterator[str]:
        """Yield the reply as text deltas. Failures are yielded as a spoken apology."""
        messages = self._messages(text)
        spoken: list[str] = []
        error: str | None = None
        try:
            async for delta in self._run(messages):
                spoken.append(delta)
                yield delta
        except anthropic.AuthenticationError:
            error = "auth"
        except anthropic.PermissionDeniedError:
            error = "auth"
        except anthropic.RateLimitError:
            error = "rate_limit"
        except anthropic.APITimeoutError:
            error = "timeout"
        except anthropic.APIConnectionError:
            error = "connection"
        except anthropic.APIStatusError as err:
            _LOGGER.error("Claude API error %s (request %s)", err.status_code, err.request_id)
            error = "api"
        except _AgentStop as stop:
            error = stop.reason
        if error:
            _LOGGER.warning("Claude turn failed: %s", error)
            yield "\n" + SPOKEN_ERRORS[error]
        else:
            self._remember(text, "".join(spoken).strip())

    async def _run(self, messages: list[dict[str, Any]]) -> AsyncIterator[str]:
        for _ in range(MAX_TOOL_ROUNDS):
            async with self.client.messages.stream(
                model=self.config.effective_model,
                max_tokens=self.config.max_tokens,
                system=self._system,
                tools=self._tool_defs,
                output_config={"effort": self.config.effort},
                messages=messages,
            ) as stream:
                async for delta in stream.text_stream:
                    yield delta
                response = await stream.get_final_message()

            usage = response.usage
            _LOGGER.debug(
                "Claude stop=%s in=%s out=%s cache_read=%s",
                response.stop_reason,
                usage.input_tokens,
                usage.output_tokens,
                getattr(usage, "cache_read_input_tokens", None),
            )
            if response.stop_reason == "refusal":
                raise _AgentStop("refusal")
            tool_uses = [block for block in response.content if block.type == "tool_use"]
            if response.stop_reason != "tool_use" or not tool_uses:
                return  # end_turn, or max_tokens (a cut-off tool call is never executed)

            # Echo the assistant turn back unchanged (thinking blocks included) and answer
            # every tool_use in a single user message.
            messages.append({"role": "assistant", "content": response.content})
            results = await asyncio.gather(*(self._call_tool(block) for block in tool_uses))
            messages.append({"role": "user", "content": list(results)})
            yield "\n"  # sentence boundary between pre-tool and post-tool text
        raise _AgentStop("too_many_steps")

    async def _call_tool(self, block: Any) -> dict[str, Any]:
        result: dict[str, Any] = {"type": "tool_result", "tool_use_id": block.id}
        try:
            result["content"] = await self.tools.execute(block.name, block.input)
            _LOGGER.debug("Tool %s ok", block.name)
        except ToolError as err:
            _LOGGER.info("Tool %s failed: %s", block.name, err)
            result.update(content=str(err), is_error=True)
        except Exception:  # a tool bug must not kill the voice loop
            _LOGGER.exception("Tool %s crashed", block.name)
            result.update(content="internal error while running the tool", is_error=True)
        return result


class _AgentStop(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
