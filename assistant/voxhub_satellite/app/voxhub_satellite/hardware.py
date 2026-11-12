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

LED_ROOT = Path(os.environ.get("VOXHUB_LED_ROOT", "/sys/class/leds"))
INPUT_ROOT = Path(os.environ.get("VOXHUB_INPUT_ROOT", "/sys/class/input"))
GREEN = "voxhub-green"
BLUE = "voxhub-blue"

EV_KEY = 0x01
EV_SW = 0x05
SW_MUTE_DEVICE = 0x0E
KEY_MICMUTE = 248
EVENT = struct.Struct("llHHi")


class Show(Enum):
    OFF = "off"
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    MUTED = "muted"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    TIMER = "timer"


PATTERNS: dict[Show, tuple[tuple[bool, bool, float], ...]] = {
    Show.OFF: ((False, False, 0.0),),
    Show.IDLE: ((True, False, 0.0),),
    Show.LISTENING: ((False, True, 0.0),),
    Show.THINKING: ((False, True, 0.3), (False, False, 0.3)),
    Show.SPEAKING: ((True, True, 0.0),),
    Show.MUTED: ((False, False, 0.0),),
    Show.ERROR: ((True, True, 0.15), (False, False, 0.15)),
    Show.DISCONNECTED: ((True, False, 1.0), (False, False, 1.0)),
    Show.TIMER: ((True, False, 0.4), (False, True, 0.4)),
}


class Leds:
    def __init__(self, enabled: bool = True, root: Path = LED_ROOT) -> None:
        self.root = root
        self.enabled = enabled and (root / GREEN).is_dir() and (root / BLUE).is_dir()
        if enabled and not self.enabled:
            _LOGGER.info("Status LEDs %s / %s not found under %s; LED feedback disabled", GREEN, BLUE, root)
        self.show = Show.OFF
        self._task: asyncio.Task[None] | None = None

    def set(self, show: Show) -> None:
        if show is self.show and (self._task is None or not self._task.done()):
            return
        self.show = show
        if self._task is not None:
            self._task.cancel()
            self._task = None
        if not self.enabled:
            return
        steps = PATTERNS[show]
        self._apply(steps[0][0], steps[0][1])
        if len(steps) > 1:
            self._task = asyncio.get_running_loop().create_task(self._animate(steps))

    async def _animate(self, steps: tuple[tuple[bool, bool, float], ...]) -> None:
        index = 0
        while self.enabled:
            green, blue, seconds = steps[index]
            self._apply(green, blue)
            await asyncio.sleep(seconds)
            index = (index + 1) % len(steps)

    def _apply(self, green: bool, blue: bool) -> None:
        self._write(GREEN, green)
        self._write(BLUE, blue)

    def _write(self, led: str, on: bool) -> None:
        if not self.enabled:
            return
        try:
            (self.root / led / "brightness").write_text("1" if on else "0")
        except OSError as err:
            _LOGGER.warning("Cannot write LED %s (%s); LED feedback disabled", led, err)
            self.enabled = False

    def close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self._apply(False, False)


def parse_events(data: bytes) -> bool | None:
    muted: bool | None = None
    for offset in range(0, len(data) - EVENT.size + 1, EVENT.size):
        _, _, kind, code, value = EVENT.unpack_from(data, offset)
        if (kind, code) in ((EV_SW, SW_MUTE_DEVICE), (EV_KEY, KEY_MICMUTE)) and value in (0, 1):
            muted = bool(value)
    return muted


def has_bit(words: str, bit: int) -> bool:
    try:
        value = int("".join(word.zfill(16) for word in words.split()) or "0", 16)
    except ValueError:
        return False
    return bool(value >> bit & 1)


def ioctl_read(nr: int, length: int) -> int:
    return (2 << 30) | (length << 16) | (ord("E") << 8) | nr


def find_mute_device(root: Path = INPUT_ROOT) -> tuple[str, bool] | None:
    for device in sorted(root.glob("event*/device")):
        with contextlib.suppress(OSError):
            if has_bit((device / "capabilities" / "sw").read_text(), SW_MUTE_DEVICE):
                return f"/dev/input/{device.parent.name}", True
            name = (device / "name").read_text().strip().lower()
            if has_bit((device / "capabilities" / "key").read_text(), KEY_MICMUTE) and any(
                word in name for word in ("voxhub", "button", "gpio", "key")
            ):
                return f"/dev/input/{device.parent.name}", False
    return None


class MuteSwitch:
    def __init__(
        self,
        enabled: bool = True,
        on_change: Callable[[bool], None] | None = None,
        root: Path = INPUT_ROOT,
    ) -> None:
        self.muted = False
        self.available = False
        self.on_change = on_change
        self._fd: int | None = None
        if not enabled:
            return
        found = find_mute_device(root)
        if found is None:
            _LOGGER.info("No mute switch input device found; the hardware mute is not reported")
            return
        path, is_switch = found
        try:
            self._fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            if is_switch:
                bits = fcntl.ioctl(self._fd, ioctl_read(0x1B, 2), bytes(2))
                self.muted = bool(int.from_bytes(bits, "little") >> SW_MUTE_DEVICE & 1)
            else:
                bits = fcntl.ioctl(self._fd, ioctl_read(0x18, 96), bytes(96))
                self.muted = bool(int.from_bytes(bits, "little") >> KEY_MICMUTE & 1)
            asyncio.get_running_loop().add_reader(self._fd, self._readable)
            self.available = True
            _LOGGER.info("Mute switch on %s, muted=%s", path, self.muted)
        except OSError as err:
            _LOGGER.info("Cannot read the mute switch at %s (%s); hardware mute not reported", path, err)
            self.close()

    def _readable(self) -> None:
        if self._fd is None:
            return
        try:
            muted = parse_events(os.read(self._fd, EVENT.size * 16))
        except BlockingIOError:
            return
        except OSError:
            self.close()
            return
        if muted is not None and muted != self.muted:
            self.muted = muted
            _LOGGER.info("Hardware mute %s", "on" if muted else "off")
            if self.on_change is not None:
                self.on_change(muted)

    def close(self) -> None:
        if self._fd is not None:
            with contextlib.suppress(RuntimeError, OSError, ValueError):
                asyncio.get_running_loop().remove_reader(self._fd)
            with contextlib.suppress(OSError):
                os.close(self._fd)
            self._fd = None
        self.available = False
