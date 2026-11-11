import logging
from datetime import datetime

import anthropic
import httpx2
import pytest

from conftest import FakeAnthropic, message, text_block, thinking_block, tool_use_block
from voxhub_assistant.agent import MAX_TOOL_ROUNDS, SPOKEN_ERRORS, ClaudeAgent

NOW = datetime(2026, 11, 10, 18, 30)


def make_agent(config, tools, responses):
    client = FakeAnthropic(responses)
    return ClaudeAgent(config, tools, client=client, now=lambda: NOW), client


async def collect(agent, text):
    return "".join([delta async for delta in agent.respond(text)])


async def test_plain_answer_and_request_shape(config, tools):
    agent, client = make_agent(config, tools, [message([text_block("It is half past six.")])])
    assert await collect(agent, "what time is it") == "It is half past six."

    request = client.requests[0]
    assert request["model"] == "claude-haiku-5-5"
    assert request["output_config"] == {"effort": "low"}
    assert "thinking" not in request and "temperature" not in request
    # Static prefix (tools + system) carries the cache breakpoint ...
    assert request["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "18:30" not in request["system"][0]["text"]
    # ... and the volatile timestamp lives in the user message, after it.
    assert request["messages"] == [
        {"role": "user", "content": "[Local time: Tuesday, 10 November 2026, 18:30]\nwhat time is it"}
    ]
    assert [tool["name"] for tool in request["tools"]][2] == "call_service"


async def test_tool_loop_tool_use_then_result_then_final_text(config, tools, ha):
    first = message(
        [
            thinking_block(),
            tool_use_block("toolu_1", "call_service",
                           {"domain": "light", "service": "turn_on", "entity_id": ["light.kitchen"]}),
        ],
        stop_reason="tool_use",
    )  # fmt: skip
    agent, client = make_agent(config, tools, [first, message([text_block("The kitchen light is on.")])])

    assert (await collect(agent, "turn on the kitchen light")).strip() == "The kitchen light is on."
    assert ha.calls == [("light", "turn_on", {"entity_id": ["light.kitchen"]})]

    second = client.requests[1]["messages"]
    assert len(second) == 3
    # The assistant turn is echoed back unchanged, thinking block included.
    assert second[1] == {"role": "assistant", "content": first.content}
    result = second[2]["content"][0]
    assert second[2]["role"] == "user"
    assert result["type"] == "tool_result" and result["tool_use_id"] == "toolu_1"
    assert "is_error" not in result and '"success": true' in result["content"]
    # The prefix must be byte-identical between the two requests (prompt caching).
    assert client.requests[0]["system"] == client.requests[1]["system"]
    assert client.requests[0]["tools"] == client.requests[1]["tools"]


async def test_parallel_tools_answered_in_one_message_and_errors_flagged(config, tools, ha):
    first = message(
        [
            text_block("One moment."),
            tool_use_block("toolu_a", "get_state", {"entity_id": "light.kitchen"}),
            tool_use_block("toolu_b", "call_service",
                           {"domain": "lock", "service": "unlock", "entity_id": ["lock.front_door"]}),
        ],
        stop_reason="tool_use",
    )  # fmt: skip
    agent, client = make_agent(config, tools, [first, message([text_block("I can't unlock doors.")])])

    reply = await collect(agent, "unlock the door and check the light")
    assert reply == "One moment.\nI can't unlock doors."  # newline = sentence boundary for TTS
    results = client.requests[1]["messages"][2]["content"]
    assert [r["tool_use_id"] for r in results] == ["toolu_a", "toolu_b"]
    assert "is_error" not in results[0]
    assert results[1]["is_error"] is True and "deny-list" in results[1]["content"]
    assert ha.calls == []  # the lock was never touched


async def test_memory_is_text_only_bounded_and_expires(config, tools):
    config.max_history_turns = 2
    responses = [message([thinking_block(), text_block(f"answer {i}")]) for i in range(4)]
    agent, client = make_agent(config, tools, responses)
    for i in range(3):
        await collect(agent, f"question {i}")

    third = client.requests[2]["messages"]
    assert [m["role"] for m in third] == ["user", "assistant", "user", "assistant", "user"]
    assert third[1]["content"] == "answer 0"  # plain text: no thinking/tool blocks across turns
    assert third[-1]["content"].endswith("question 2")

    agent._last_activity -= config.conversation_timeout + 1
    await collect(agent, "question 3")
    assert len(client.requests[3]["messages"]) == 1  # memory expired


def _status_error(cls, status):
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls("boom", response=httpx2.Response(status, request=request), body=None)


@pytest.mark.parametrize(
    ("error", "key"),
    [
        (lambda: _status_error(anthropic.AuthenticationError, 401), "auth"),
        (lambda: _status_error(anthropic.RateLimitError, 429), "rate_limit"),
        (lambda: _status_error(anthropic.InternalServerError, 500), "api"),
        (lambda: anthropic.APITimeoutError(httpx2.Request("POST", "https://x")), "timeout"),
        (lambda: anthropic.APIConnectionError(request=httpx2.Request("POST", "https://x")), "connection"),
    ],
)
async def test_api_errors_become_spoken_apologies(config, tools, error, key):
    agent, client = make_agent(config, tools, [error(), message([text_block("ok")])])
    assert (await collect(agent, "hello")).strip() == SPOKEN_ERRORS[key]
    # A failed turn is not remembered.
    await collect(agent, "hello again")
    assert len(client.requests[1]["messages"]) == 1


async def test_refusal_is_handled(config, tools):
    agent, _ = make_agent(config, tools, [message([], stop_reason="refusal")])
    assert (await collect(agent, "something")).strip() == SPOKEN_ERRORS["refusal"]


async def test_truncated_tool_call_is_not_executed(config, tools, ha):
    cut = message(
        [text_block("Sure."),
         tool_use_block("toolu_1", "call_service", {"domain": "light", "service": "turn_on"})],
        stop_reason="max_tokens",
    )  # fmt: skip
    agent, client = make_agent(config, tools, [cut])
    assert await collect(agent, "lights") == "Sure."
    assert ha.calls == [] and len(client.requests) == 1


async def test_runaway_tool_loop_is_bounded(config, tools):
    looping = [
        message([tool_use_block(f"toolu_{i}", "search_entities", {"query": "x"})], stop_reason="tool_use")
        for i in range(MAX_TOOL_ROUNDS)
    ]
    agent, client = make_agent(config, tools, looping)
    assert (await collect(agent, "loop")).strip() == SPOKEN_ERRORS["too_many_steps"]
    assert len(client.requests) == MAX_TOOL_ROUNDS


async def test_api_key_never_logged(config, tools, caplog):
    caplog.set_level(logging.DEBUG)
    agent, _ = make_agent(config, tools, [_status_error(anthropic.BadRequestError, 400)])
    await collect(agent, "hello")
    assert config.anthropic_api_key not in caplog.text
    assert config.anthropic_api_key not in repr(config)
