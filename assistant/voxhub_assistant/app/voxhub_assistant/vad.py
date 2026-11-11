"""Energy-based voice activity detection and utterance end-pointing.

Deliberately dependency-light (numpy only): after a wake word the task is merely
"find the end of one utterance in a quiet-ish room", which an adaptive energy gate does
well, and it avoids native VAD wheels on aarch64. Whisper tolerates trailing silence.
"""

from __future__ import annotations

from enum import Enum

import numpy as np

FRAME_MS = 20


class EndpointState(Enum):
    WAITING = "waiting"  # no speech yet
    SPEAKING = "speaking"
    DONE = "done"  # utterance complete
    TIMEOUT = "timeout"  # nobody spoke


def rms(pcm: bytes) -> float:
    """Root-mean-square level of 16-bit little-endian mono PCM."""
    samples = np.frombuffer(pcm[: len(pcm) & ~1], dtype="<i2")
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))


class Endpointer:
    """Feed 16-bit mono PCM; reports when the speaker has finished.

    A frame is speech when its RMS exceeds ``max(min_rms, noise_floor * sensitivity)``.
    The noise floor adapts on non-speech frames only.
    """

    def __init__(
        self,
        rate: int = 16000,
        silence_seconds: float = 0.8,
        max_seconds: float = 15.0,
        no_speech_seconds: float = 6.0,
        sensitivity: float = 2.5,
        noise_floor: float = 0.0,
        min_rms: float = 120.0,
        min_speech_seconds: float = 0.12,
        preroll_seconds: float = 0.3,
    ) -> None:
        self.frame_bytes = rate * FRAME_MS // 1000 * 2
        self._silence_frames = _frames(silence_seconds)
        self._max_frames = _frames(max_seconds)
        self._no_speech_frames = _frames(no_speech_seconds)
        self._min_speech_frames = _frames(min_speech_seconds)
        self._preroll_frames = _frames(preroll_seconds)
        self.sensitivity = sensitivity
        self.min_rms = min_rms
        self.noise_floor = noise_floor
        self.state = EndpointState.WAITING
        self._pending = b""
        self._frames: list[bytes] = []
        self._speech_run = 0
        self._silence_run = 0
        self._total = 0

    @property
    def audio(self) -> bytes:
        return b"".join(self._frames)

    @property
    def finished(self) -> bool:
        return self.state in (EndpointState.DONE, EndpointState.TIMEOUT)

    def feed(self, pcm: bytes) -> EndpointState:
        self._pending += pcm
        while len(self._pending) >= self.frame_bytes and not self.finished:
            frame, self._pending = self._pending[: self.frame_bytes], self._pending[self.frame_bytes :]
            self._process(frame)
        return self.state

    def _process(self, frame: bytes) -> None:
        level = rms(frame)
        is_speech = level > max(self.min_rms, self.noise_floor * self.sensitivity)
        self._frames.append(frame)
        self._total += 1

        if self.state is EndpointState.WAITING:
            if is_speech:
                self._speech_run += 1
                if self._speech_run >= self._min_speech_frames:
                    self.state = EndpointState.SPEAKING
                    keep = self._speech_run + self._preroll_frames
                    self._frames = self._frames[-keep:]
                    self._total = len(self._frames)
            else:
                self._speech_run = 0
                self._adapt(level)
                if self._total >= self._no_speech_frames:
                    self.state = EndpointState.TIMEOUT
        elif self.state is EndpointState.SPEAKING:
            self._silence_run = 0 if is_speech else self._silence_run + 1
            if self._silence_run >= self._silence_frames or self._total >= self._max_frames:
                self.state = EndpointState.DONE

    def _adapt(self, level: float) -> None:
        if self.noise_floor <= 0:
            self.noise_floor = level
        else:
            self.noise_floor += (level - self.noise_floor) * 0.05


def _frames(seconds: float) -> int:
    return max(1, round(seconds * 1000 / FRAME_MS))
