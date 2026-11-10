"""Entry point: ``python3 -m voxhub_assistant``."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
import sys

from . import __version__
from .agent import ClaudeAgent
from .audio import Microphone, Speaker
from .config import Config, ConfigError
from .ha_client import HomeAssistant, ServicePolicy
from .leds import Leds, MuteSwitch
from .pipeline import Assistant
from .tools import HomeTools
from .wakeword import LocalWakeWord, WakeWord, WyomingWakeWord

_LOGGER = logging.getLogger("voxhub_assistant")


async def run(config: Config) -> None:
    ha = HomeAssistant()
    policy = ServicePolicy.from_lists(config.allowed_service_domains, config.denied_service_domains)
    agent = ClaudeAgent(config, HomeTools(ha, policy, config.exposed_domains))
    wake: WakeWord
    if config.wake_word_engine == "local":
        wake = LocalWakeWord(config.wake_word, config.wake_word_threshold)
    else:
        wake = WyomingWakeWord(config.wake_word_uri, config.wake_word)
    mic = Microphone(config.mic_command, config.input_device, config.mic_gain)
    speaker = Speaker(config.speaker_command, config.output_device, config.volume)
    leds = Leds(config.leds)
    assistant = Assistant(config, mic, speaker, wake, agent, leds)
    mute = MuteSwitch(config.mute_switch, on_change=assistant.on_mute_change)
    assistant.mute = mute

    _LOGGER.info(
        "VoxHub Assistant %s: model=%s wake=%s (%s) stt=%s tts=%s",
        __version__, config.effective_model, config.wake_word, config.wake_word_engine,
        config.stt_uri, config.tts_uri,
    )  # fmt: skip
    task = asyncio.create_task(assistant.run())
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, task.cancel)
    try:
        await task
    except asyncio.CancelledError:
        _LOGGER.info("Shutting down")
    finally:
        mute.close()
        leds.off()
        await mic.stop()
        await speaker.stop()
        await ha.close()
        with contextlib.suppress(Exception):
            await agent.client.close()


def main() -> int:
    try:
        config = Config.load()
        config.require_api_key()
    except ConfigError as err:
        print(f"Configuration error: {err}", file=sys.stderr)
        return 2
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # The SDK's HTTP client logs request lines at INFO; keep the add-on log quiet.
    for noisy in ("httpx", "httpx2", "httpcore", "httpcore2", "anthropic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    asyncio.run(run(config))
    return 0


if __name__ == "__main__":
    sys.exit(main())
