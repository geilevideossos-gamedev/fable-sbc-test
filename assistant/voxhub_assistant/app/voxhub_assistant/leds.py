"""Optional hardware extras: status LEDs (sysfs gpio-leds) and the mute switch (evdev).

Both are fail-soft: on hardware without them, or when the container may not write to
/sys or read /dev/input, they log once and turn into no-ops.
"""

from __future__ import annotations

import asyncio
import contextlib
import fcntl
import logging
import os
import struct
from collections.abc import Callable
from enum import Enum
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

LED_ROOT = Path("/sys/class/leds")
GREEN = "voxhub:green:status"
BLUE = "voxhub:blue:status"


class State(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    MUTED = "muted"
    ERROR = "error"


# state -> (green, blue, blink blue)
_PATTERNS: dict[State, tuple[bool, bool, bool]] = {
    State.IDLE: (True, False, False),
    State.LISTENING: (False, True, False),
    State.THINKING: (False, True, True),
    State.SPEAKING: (True, True, False),
    State.MUTED: (False, False, False),  # the red mute LED is driven in hardware
    State.ERROR: (False, False, False),
}


class Leds:
    def __init__(self, enabled: bool = True, root: Path = LED_ROOT) -> None:
        self._root = root
        self.enabled = enabled and (root / GREEN).is_dir() and (root / BLUE).is_dir()
        if enabled and not self.enabled:
            _LOGGER.info("Status LEDs not found under %s; LED feedback disabled", root)
        self._blink: asyncio.Task[None] | None = None
        self.state = State.IDLE

    def set(self, state: State) -> None:
        self.state = state
        if not self.enabled:
            return
        if self._blink:
            self._blink.cancel()
            self._blink = None
        green, blue, blink = _PATTERNS[state]
        self._write(GREEN, green)
        self._write(BLUE, blue)
        if blink:
            self._blink = asyncio.get_running_loop().create_task(self._blink_blue())

    async def _blink_blue(self) -> None:
        on = True
        while self.enabled:
            await asyncio.sleep(0.3)
            on = not on
            self._write(BLUE, on)

    def _write(self, led: str, on: bool) -> None:
        try:
            (self._root / led / "brightness").write_text("1" if on else "0")
        except OSError as err:
            _LOGGER.warning("Cannot write LED %s (%s); LED feedback disabled", led, err)
            self.enabled = False

    def off(self) -> None:
        if self._blink:
            self._blink.cancel()
        if self.enabled:
            self._write(GREEN, False)
            self._write(BLUE, False)


# Linux input event constants (include/uapi/linux/input-event-codes.h)
EV_SW = 0x05
SW_MUTE_DEVICE = 0x0E
_EVENT = struct.Struct("llHHi")  # struct input_event on 64-bit: timeval, type, code, value
_EVIOCGSW_2 = (2 << 30) | (2 << 16) | (ord("E") << 8) | 0x1B  # _IOC(_IOC_READ, 'E', 0x1b, 2)


def parse_switch_events(data: bytes) -> bool | None:
    """Return the latest SW_MUTE_DEVICE value in a buffer of input events, if any."""
    muted: bool | None = None
    for offset in range(0, len(data) - _EVENT.size + 1, _EVENT.size):
        _, _, kind, code, value = _EVENT.unpack_from(data, offset)
        if kind == EV_SW and code == SW_MUTE_DEVICE:
            muted = bool(value)
    return muted


class MuteSwitch:
    """Tracks the hardware mute slide switch exposed as a gpio-keys switch."""

    def __init__(
        self,
        enabled: bool = True,
        device_name: str = "voxhub-switches",
        on_change: Callable[[bool], None] | None = None,
    ) -> None:
        self.muted = False
        self._on_change = on_change
        self._fd: int | None = None
        if not enabled:
            return
        path = self._find(device_name)
        if path is None:
            _LOGGER.info("Input device '%s' not found; mute switch ignored", device_name)
            return
        try:
            self._fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            bits = fcntl.ioctl(self._fd, _EVIOCGSW_2, bytes(2))
            self.muted = bool(int.from_bytes(bits, "little") >> SW_MUTE_DEVICE & 1)
            asyncio.get_running_loop().add_reader(self._fd, self._readable)
            _LOGGER.info("Mute switch on %s (muted=%s)", path, self.muted)
        except OSError as err:
            _LOGGER.info("Cannot read mute switch at %s (%s); ignored", path, err)
            self.close()

    @staticmethod
    def _find(device_name: str) -> str | None:
        for name_file in sorted(Path("/sys/class/input").glob("event*/device/name")):
            with contextlib.suppress(OSError):
                if name_file.read_text().strip() == device_name:
                    return f"/dev/input/{name_file.parent.parent.name}"
        return None

    def _readable(self) -> None:
        assert self._fd is not None
        try:
            muted = parse_switch_events(os.read(self._fd, _EVENT.size * 16))
        except BlockingIOError:
            return
        except OSError:
            self.close()
            return
        if muted is not None and muted != self.muted:
            self.muted = muted
            _LOGGER.info("Hardware mute %s", "on" if muted else "off")
            if self._on_change:
                self._on_change(muted)

    def close(self) -> None:
        if self._fd is not None:
            with contextlib.suppress(RuntimeError, OSError):
                asyncio.get_running_loop().remove_reader(self._fd)
            with contextlib.suppress(OSError):
                os.close(self._fd)
            self._fd = None
