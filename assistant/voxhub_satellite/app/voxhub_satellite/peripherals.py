from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import signal
import sys
from collections.abc import Sequence

from .bridge import Bridge
from .hardware import Leds, MuteSwitch


async def serve(url: str, leds_enabled: bool = True, mute_enabled: bool = True) -> None:
    leds = Leds(leds_enabled)
    bridge = Bridge(leds, url)
    mute = MuteSwitch(mute_enabled, bridge.on_hardware_mute)
    bridge.hardware_muted = mute.muted
    task = asyncio.create_task(bridge.run())
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, task.cancel)
    try:
        await task
    except asyncio.CancelledError:
        pass
    finally:
        mute.close()
        bridge.close()
        with contextlib.suppress(Exception):
            leds.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="voxhub-peripherals")
    parser.add_argument("--url", default="ws://127.0.0.1:6055")
    parser.add_argument("--no-leds", action="store_true")
    parser.add_argument("--no-mute-switch", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(serve(args.url, not args.no_leds, not args.no_mute_switch))
    return 0


if __name__ == "__main__":
    sys.exit(main())
