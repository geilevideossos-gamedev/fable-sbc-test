"""Wake word detection: Wyoming openWakeWord add-on (default) or in-process openWakeWord."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

import numpy as np
from wyoming.audio import AudioChunk, AudioStart
from wyoming.client import AsyncClient
from wyoming.wake import Detect, Detection

from .audio import CHANNELS, RATE, WIDTH, Microphone

_LOGGER = logging.getLogger(__name__)

ChunkCallback = Callable[[bytes], None]


class WakeWordError(RuntimeError):
    """The wake word engine is unavailable."""


class WakeWord(Protocol):
    async def wait(self, mic: Microphone, on_chunk: ChunkCallback | None = None) -> str:
        """Consume microphone audio until the wake word is heard; return its name."""
        ...


class WyomingWakeWord:
    """Streams audio to a Wyoming wake word server such as the openWakeWord add-on."""

    def __init__(self, uri: str, name: str) -> None:
        self.uri = uri
        self.name = Path(name).stem if name.endswith((".onnx", ".tflite")) else name

    async def wait(self, mic: Microphone, on_chunk: ChunkCallback | None = None) -> str:
        try:
            async with AsyncClient.from_uri(self.uri) as client:
                await client.write_event(Detect(names=[self.name]).event())
                await client.write_event(AudioStart(rate=RATE, width=WIDTH, channels=CHANNELS).event())
                sender = asyncio.create_task(self._send(client, mic, on_chunk))
                receiver = asyncio.create_task(self._receive(client))
                try:
                    done, _ = await asyncio.wait({sender, receiver}, return_when=asyncio.FIRST_COMPLETED)
                finally:
                    for task in (sender, receiver):
                        task.cancel()
                    await asyncio.gather(sender, receiver, return_exceptions=True)
                return next(iter(done)).result() or self.name
        except OSError as err:
            raise WakeWordError(f"wake word service unavailable at {self.uri}: {err!r}") from err

    @staticmethod
    async def _send(client: AsyncClient, mic: Microphone, on_chunk: ChunkCallback | None) -> str:
        while True:
            pcm = await mic.read()
            if on_chunk:
                on_chunk(pcm)
            chunk = AudioChunk(rate=RATE, width=WIDTH, channels=CHANNELS, audio=pcm)
            await client.write_event(chunk.event())

    async def _receive(self, client: AsyncClient) -> str:
        while True:
            event = await client.read_event()
            if event is None:
                raise WakeWordError("wake word service closed the connection")
            if Detection.is_type(event.type):
                return Detection.from_event(event).name or self.name


class LocalWakeWord:
    """Runs openWakeWord in this process. Needs the optional ``openwakeword`` package.

    ``name`` is a bundled model name ("hey_jarvis") or a path to a custom .onnx/.tflite
    model, typically somewhere under /share.
    """

    def __init__(self, name: str, threshold: float = 0.5) -> None:
        self.name = name
        self.threshold = threshold
        self._model: Any = None

    def _load(self) -> Any:
        try:
            import openwakeword
            from openwakeword.model import Model
        except ImportError as err:
            raise WakeWordError(
                "openwakeword is not installed in this image; use wake_word_engine: wyoming"
            ) from err
        is_file = self.name.endswith((".onnx", ".tflite"))
        if is_file and not Path(self.name).is_file():
            raise WakeWordError(f"wake word model not found: {self.name}")
        framework = "tflite" if self.name.endswith(".tflite") else "onnx"
        if not is_file and hasattr(openwakeword, "utils"):
            openwakeword.utils.download_models([self.name])  # no-op when already cached
        return Model(wakeword_models=[self.name], inference_framework=framework)

    async def wait(self, mic: Microphone, on_chunk: ChunkCallback | None = None) -> str:
        loop = asyncio.get_running_loop()
        if self._model is None:
            self._model = await loop.run_in_executor(None, self._load)
        self._model.reset()
        while True:
            pcm = await mic.read()
            if on_chunk:
                on_chunk(pcm)
            samples = np.frombuffer(pcm, dtype="<i2")
            scores: dict[str, float] = await loop.run_in_executor(None, self._model.predict, samples)
            name, score = max(scores.items(), key=lambda item: item[1])
            if score >= self.threshold:
                _LOGGER.debug("Wake word %s scored %.2f", name, score)
                return name
