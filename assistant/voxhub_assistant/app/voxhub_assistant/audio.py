"""Audio I/O through PulseAudio command line clients (parec / pacat).

Inside an add-on the Supervisor provides a PulseAudio socket (PULSE_SERVER) when
``audio: true`` is set. Spawning ``parec``/``pacat`` keeps native audio libraries out of
the Python process, lets PulseAudio do the resampling (48 kHz stereo I2S -> 16 kHz mono)
and survives sound server restarts by simply respawning the subprocess.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import shlex

import numpy as np

_LOGGER = logging.getLogger(__name__)

RATE = 16000
WIDTH = 2
CHANNELS = 1
CHUNK_SAMPLES = 1280  # 80 ms: the frame size openWakeWord expects
CHUNK_BYTES = CHUNK_SAMPLES * WIDTH

DEFAULT_MIC_COMMAND = "parec --raw --format=s16le --rate=16000 --channels=1 --latency-msec=80"
DEFAULT_SPEAKER_COMMAND = (
    "pacat --playback --raw --format={format} --rate={rate} --channels={channels} --latency-msec=100"
)
_PULSE_FORMATS = {1: "u8", 2: "s16le", 4: "s32le"}


class AudioError(RuntimeError):
    """The capture or playback subprocess failed."""


def apply_gain(pcm: bytes, gain: float) -> bytes:
    """Scale 16-bit PCM by ``gain`` with clipping (software mic gain / speaker volume)."""
    if gain == 1.0 or not pcm:
        return pcm
    samples = np.frombuffer(pcm[: len(pcm) & ~1], dtype="<i2").astype(np.float32) * gain
    return np.clip(samples, -32768, 32767).astype("<i2").tobytes()


def tone(frequency: float, milliseconds: int, rate: int = 22050, level: float = 0.3) -> bytes:
    """A short sine beep with a fade in/out, as 16-bit mono PCM."""
    count = rate * milliseconds // 1000
    wave = np.sin(2 * np.pi * frequency * np.arange(count) / rate)
    fade = min(count // 2, rate // 100)
    envelope = np.ones(count)
    if fade:
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)
    return (wave * envelope * level * 32767).astype("<i2").tobytes()


class Microphone:
    """Continuous 16 kHz mono capture. Chunks are queued; the oldest are dropped when
    nobody is reading (e.g. while the assistant thinks or speaks)."""

    def __init__(self, command: str = "", device: str = "", gain: float = 1.0) -> None:
        self._argv = shlex.split(command or DEFAULT_MIC_COMMAND)
        if device and not command:
            self._argv.append(f"--device={device}")
        self.gain = gain
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=25)
        self._proc: asyncio.subprocess.Process | None = None
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        await self.stop()
        self._queue = asyncio.Queue(maxsize=25)
        _LOGGER.debug("Starting capture: %s", self._argv)
        try:
            self._proc = await asyncio.create_subprocess_exec(
                *self._argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
            )
        except OSError as err:
            raise AudioError(f"cannot start capture command {self._argv[0]}: {err}") from err
        self._task = asyncio.create_task(self._reader(self._proc))

    async def _reader(self, proc: asyncio.subprocess.Process) -> None:
        assert proc.stdout is not None
        try:
            while True:
                chunk = await proc.stdout.readexactly(CHUNK_BYTES)
                self._put(apply_gain(chunk, self.gain))
        except (asyncio.IncompleteReadError, ConnectionError):
            _LOGGER.warning("Capture process ended (exit code %s)", proc.returncode)
        finally:
            self._put(None)

    def _put(self, item: bytes | None) -> None:
        if self._queue.full():
            with contextlib.suppress(asyncio.QueueEmpty):
                self._queue.get_nowait()
        self._queue.put_nowait(item)

    async def read(self) -> bytes:
        """Return the next 80 ms chunk. Raises AudioError when capture has stopped."""
        chunk = await self._queue.get()
        if chunk is None:
            self._put(None)  # stay failed until restarted
            raise AudioError("microphone capture stopped")
        return chunk

    def flush(self) -> None:
        """Discard buffered audio (half-duplex: drop whatever was heard while speaking)."""
        kept = None
        while not self._queue.empty():
            if self._queue.get_nowait() is None:
                kept = True
        if kept:
            self._put(None)

    async def stop(self) -> None:
        await _terminate(self._proc)
        self._proc = None
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None


class Speaker:
    """Raw PCM playback with software volume. One player process per audio format; it is
    kept open across sentences and closed by :meth:`drain`."""

    def __init__(self, command: str = "", device: str = "", volume: float = 0.7) -> None:
        self._template = command or DEFAULT_SPEAKER_COMMAND
        self._device = device if not command else ""
        self.volume = volume
        self._proc: asyncio.subprocess.Process | None = None
        self._format: tuple[int, int, int] | None = None

    async def write(self, pcm: bytes, rate: int, width: int = 2, channels: int = 1) -> None:
        fmt = (rate, width, channels)
        if self._proc is None or self._format != fmt or self._proc.returncode is not None:
            await self.drain()
            argv = shlex.split(
                self._template.format(rate=rate, channels=channels, format=_PULSE_FORMATS.get(width, "s16le"))
            )
            if self._device:
                argv.append(f"--device={self._device}")
            _LOGGER.debug("Starting playback: %s", argv)
            try:
                self._proc = await asyncio.create_subprocess_exec(
                    *argv, stdin=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
                )
            except OSError as err:
                raise AudioError(f"cannot start playback command {argv[0]}: {err}") from err
            self._format = fmt
        assert self._proc.stdin is not None
        try:
            self._proc.stdin.write(apply_gain(pcm, self.volume) if width == 2 else pcm)
            await self._proc.stdin.drain()
        except (ConnectionError, OSError) as err:
            self._proc = None
            raise AudioError(f"playback failed: {err}") from err

    async def drain(self) -> None:
        """Close the player's input and wait until everything queued has been played."""
        proc, self._proc, self._format = self._proc, None, None
        if proc is None:
            return
        with contextlib.suppress(ConnectionError, OSError):
            assert proc.stdin is not None
            proc.stdin.close()
        try:
            await asyncio.wait_for(proc.wait(), timeout=120)
        except asyncio.TimeoutError:
            await _terminate(proc)

    async def play(self, pcm: bytes, rate: int, width: int = 2, channels: int = 1) -> None:
        await self.write(pcm, rate, width, channels)
        await self.drain()

    async def stop(self) -> None:
        await _terminate(self._proc)
        self._proc = None


async def _terminate(proc: asyncio.subprocess.Process | None) -> None:
    if proc is None or proc.returncode is not None:
        return
    with contextlib.suppress(ProcessLookupError):
        proc.terminate()
    try:
        await asyncio.wait_for(proc.wait(), timeout=2)
    except asyncio.TimeoutError:
        with contextlib.suppress(ProcessLookupError):
            proc.kill()
