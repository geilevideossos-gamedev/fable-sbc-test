from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import signal
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bridge import Bridge
from .guard import DEFAULT_PROTECTED_DOMAINS, Guard
from .hardware import Leds, MuteSwitch
from .launch import LVA_DIR, Settings, apply_levels, lva_command, wait_for_audio

_LOGGER = logging.getLogger("voxhub_satellite")

OPTIONS_PATH = Path("/data/options.json")


@dataclass
class Options:
    settings: Settings
    leds: bool = True
    mute_switch: bool = True
    guard: bool = True
    protected_domains: list[str] = field(default_factory=lambda: list(DEFAULT_PROTECTED_DOMAINS))
    guard_interval: float = 300.0
    log_level: str = "info"

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> Options:
        settings = Settings(
            name=str(raw.get("name") or "VoxHub Hub"),
            wake_word=str(raw.get("wake_word") or "okay_nabu"),
            mic_gain=float(raw.get("mic_gain", 4.0)),
            mic_auto_gain=int(raw.get("mic_auto_gain", 0)),
            mic_noise_suppression=int(raw.get("mic_noise_suppression", 0)),
            volume_percent=int(raw.get("volume_percent", 100)),
            preferences_file="/data/preferences.json",
            download_dir="/data/downloads",
            input_device=str(raw.get("input_device") or ""),
            output_device=str(raw.get("output_device") or ""),
            thinking_sound=bool(raw.get("thinking_sound", False)),
            debug=str(raw.get("log_level", "info")) == "debug",
        ).validate()
        configured = raw.get("protected_domains", list(DEFAULT_PROTECTED_DOMAINS)) or []
        domains = [str(item).strip().lower() for item in configured if str(item).strip()]
        return cls(
            settings=settings,
            leds=bool(raw.get("leds", True)),
            mute_switch=bool(raw.get("mute_switch", True)),
            guard=bool(raw.get("guard", True)),
            protected_domains=domains,
            guard_interval=float(raw.get("guard_interval", 300)),
            log_level=str(raw.get("log_level", "info")),
        )

    @classmethod
    def load(cls, path: Path = OPTIONS_PATH) -> Options:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raw = {}
        if not isinstance(raw, dict):
            raise ValueError(f"{path} must contain a JSON object")
        return cls.parse(raw)


async def keep_running(command: list[str]) -> None:
    delay = 5.0
    while True:
        _LOGGER.info("Starting Linux Voice Assistant")
        process = await asyncio.create_subprocess_exec(*command, cwd=str(LVA_DIR))
        try:
            code = await process.wait()
        except asyncio.CancelledError:
            if process.returncode is None:
                process.terminate()
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(process.wait(), 10)
                if process.returncode is None:
                    process.kill()
            raise
        _LOGGER.warning("Linux Voice Assistant exited with code %s; restarting in %.0f s", code, delay)
        await asyncio.sleep(delay)
        delay = min(delay * 2, 60.0)


async def run(options: Options) -> None:
    settings = options.settings
    loop = asyncio.get_running_loop()
    source, sink = settings.input_device, settings.output_device
    if not source or not sink:
        found_source, found_sink = await loop.run_in_executor(None, wait_for_audio)
        source, sink = source or found_source, sink or found_sink
    await loop.run_in_executor(None, apply_levels, settings, source, sink)
    command = lva_command(settings, source, sink)
    _LOGGER.info("Microphone %s, speaker %s, wake word %s", source, sink, settings.wake_word)
    await loop.run_in_executor(None, lambda: Path(settings.download_dir).mkdir(parents=True, exist_ok=True))

    leds = Leds(options.leds)
    bridge = Bridge(leds, f"ws://127.0.0.1:{settings.peripheral_port}")
    mute = MuteSwitch(options.mute_switch, bridge.on_hardware_mute)
    bridge.hardware_muted = mute.muted
    tasks = [asyncio.create_task(keep_running(command)), asyncio.create_task(bridge.run())]
    token = os.environ.get("SUPERVISOR_TOKEN", "")
    if options.guard and token:
        guard = Guard(token, options.protected_domains, options.guard_interval)
        tasks.append(asyncio.create_task(guard.run()))
        _LOGGER.info("Exposure guard on: %s are never exposed to Assist", ", ".join(guard.protected_domains))
    elif options.guard:
        _LOGGER.warning("SUPERVISOR_TOKEN is missing: the exposure guard cannot run")
    else:
        _LOGGER.warning("Exposure guard switched off: locks and alarm panels can be exposed to Assist")
    stop = asyncio.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    waiter = asyncio.create_task(stop.wait())
    try:
        done, _ = await asyncio.wait([waiter, *tasks], return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task is not waiter and task.exception() is not None:
                _LOGGER.error("Stopped: %r", task.exception())
    finally:
        for task in [waiter, *tasks]:
            task.cancel()
        await asyncio.gather(waiter, *tasks, return_exceptions=True)
        mute.close()
        bridge.close()
        leds.close()


def main() -> int:
    try:
        options = Options.load()
    except (ValueError, TypeError) as err:
        print(f"Configuration error: {err}", file=sys.stderr)
        return 2
    logging.basicConfig(
        level=getattr(logging, options.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(run(options))
    return 0


if __name__ == "__main__":
    sys.exit(main())
