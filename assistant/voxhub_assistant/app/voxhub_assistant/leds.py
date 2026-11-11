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
GREEN = "voxhub-green"
BLUE = "voxhub-blue"


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
EV_KEY = 0x01
EV_SW = 0x05
SW_MUTE_DEVICE = 0x0E  # custom voxhub overlay: gpio-keys switch
KEY_MICMUTE = 248  # stock "gpio-key" overlay: key held down while muted
_EVENT = struct.Struct("llHHi")  # struct input_event on 64-bit: timeval, type, code, value


def _eviocg(nr: int, length: int) -> int:
    return (2 << 30) | (length << 16) | (ord("E") << 8) | nr  # _IOC(_IOC_READ, 'E', nr, length)


def parse_switch_events(data: bytes) -> bool | None:
    """Return the latest mute state in a buffer of input events, if any."""
    muted: bool | None = None
    for offset in range(0, len(data) - _EVENT.size + 1, _EVENT.size):
        _, _, kind, code, value = _EVENT.unpack_from(data, offset)
        if (kind, code) in ((EV_SW, SW_MUTE_DEVICE), (EV_KEY, KEY_MICMUTE)):
            muted = bool(value)
    return muted


def _has_bit(hex_words: str, bit: int) -> bool:
    """Test a bit in a sysfs capability bitmap (space separated hex words, MSW first)."""
    try:
        value = int("".join(w.zfill(16) for w in hex_words.split()) or "0", 16)
    except ValueError:
        return False
    return bool(value >> bit & 1)


class MuteSwitch:
    """Tracks the hardware mute slide switch (gpio-keys: SW_MUTE_DEVICE or KEY_MICMUTE)."""

    def __init__(
        self,
        enabled: bool = True,
        on_change: Callable[[bool], None] | None = None,
        sysfs: Path = Path("/sys/class/input"),
    ) -> None:
        self.muted = False
        self._on_change = on_change
        self._fd: int | None = None
        if not enabled:
            return
        found = self._find(sysfs)
        if found is None:
            _LOGGER.info("No mute switch input device found; mute switch ignored")
            return
        path, is_switch = found
        try:
            self._fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            if is_switch:
                bits = fcntl.ioctl(self._fd, _eviocg(0x1B, 2), bytes(2))
                self.muted = _bit(bits, SW_MUTE_DEVICE)
            else:
                bits = fcntl.ioctl(self._fd, _eviocg(0x18, 96), bytes(96))
                self.muted = _bit(bits, KEY_MICMUTE)
            asyncio.get_running_loop().add_reader(self._fd, self._readable)
            _LOGGER.info("Mute switch on %s (muted=%s)", path, self.muted)
        except OSError as err:
            _LOGGER.info("Cannot read mute switch at %s (%s); ignored", path, err)
            self.close()

    @staticmethod
    def _find(sysfs: Path) -> tuple[str, bool] | None:
        """Locate the input device by capability, so it works with either overlay."""
        for dev in sorted(sysfs.glob("event*/device")):
            with contextlib.suppress(OSError):
                if _has_bit((dev / "capabilities" / "sw").read_text(), SW_MUTE_DEVICE):
                    return f"/dev/input/{dev.parent.name}", True
                name = (dev / "name").read_text().strip()
                if _has_bit((dev / "capabilities" / "key").read_text(), KEY_MICMUTE) and (
                    "button" in name or "voxhub" in name or "gpio" in name
                ):
                    return f"/dev/input/{dev.parent.name}", False
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


def _bit(bits: bytes, bit: int) -> bool:
    return bool(int.from_bytes(bits, "little") >> bit & 1)
