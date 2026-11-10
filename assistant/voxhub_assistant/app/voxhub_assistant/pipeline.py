"""The voice loop: wake word -> record -> STT -> Claude -> TTS -> speaker.

The pipeline is half-duplex. There is no echo cancellation on the hub, so microphone
audio captured while the assistant thinks or speaks is discarded (``mic.flush()``) before
listening resumes.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable

from .agent import ClaudeAgent
from .audio import AudioError, Microphone, Speaker, tone
from .config import Config
from .leds import Leds, MuteSwitch, State
from .sentences import SentenceSplitter
from .vad import Endpointer, EndpointState, rms
from .wakeword import WakeWord, WakeWordError
from .wyoming_clients import SpeechServiceError, TtsAudio, synthesize, transcribe

_LOGGER = logging.getLogger(__name__)

TONE_RATE = 22050
WAKE_TONE = tone(880, 90, TONE_RATE) + tone(1320, 90, TONE_RATE)
ERROR_TONE = tone(330, 160, TONE_RATE) + tone(220, 240, TONE_RATE)
ECHO_TAIL_SECONDS = 0.25  # let the room and the amp settle before listening again

Transcriber = Callable[[bytes], Awaitable[str]]
Synthesizer = Callable[[str], Awaitable[TtsAudio]]


class Assistant:
    def __init__(
        self,
        config: Config,
        mic: Microphone,
        speaker: Speaker,
        wake: WakeWord,
        agent: ClaudeAgent,
        leds: Leds,
        mute: MuteSwitch | None = None,
        transcriber: Transcriber | None = None,
        synthesizer: Synthesizer | None = None,
    ) -> None:
        self.config = config
        self.mic = mic
        self.speaker = speaker
        self.wake = wake
        self.agent = agent
        self.leds = leds
        self.mute = mute
        self._transcribe = transcriber or (lambda pcm: transcribe(config.stt_uri, pcm, config.language))
        self._synthesize = synthesizer or (lambda text: synthesize(config.tts_uri, text, config.tts_voice))
        self._noise_floor = 0.0

    @property
    def _muted(self) -> bool:
        return bool(self.mute and self.mute.muted)

    def on_mute_change(self, muted: bool) -> None:
        if self.leds.state in (State.IDLE, State.MUTED):
            self.leds.set(State.MUTED if muted else State.IDLE)

    async def run(self) -> None:
        """Run forever, restarting audio capture or the wake word client when they fail."""
        while True:
            try:
                await self.mic.start()
                while True:
                    await self.run_once()
            except (AudioError, WakeWordError) as err:
                _LOGGER.error("%s; retrying in 5 seconds", err)
            except Exception:  # keep the add-on alive on unexpected errors
                _LOGGER.exception("Unexpected error in the voice loop; retrying in 5 seconds")
            self.leds.set(State.ERROR)
            await self.mic.stop()
            await asyncio.sleep(5)

    async def run_once(self) -> None:
        """Wait for the wake word, then handle one conversation (plus follow-ups)."""
        self.leds.set(State.MUTED if self._muted else State.IDLE)
        self.mic.flush()
        name = await self.wake.wait(self.mic, self._track_noise)
        _LOGGER.info("Wake word detected: %s", name)
        if self.config.wake_sound:
            await self._play_tone(WAKE_TONE)
        no_speech = self.config.no_speech_timeout
        while await self.handle_turn(no_speech) and self.config.follow_up and not self._muted:
            no_speech = self.config.follow_up_seconds

    async def handle_turn(self, no_speech_seconds: float) -> bool:
        """Record one utterance and answer it. Returns True if the assistant replied."""
        started = time.monotonic()
        self.leds.set(State.LISTENING)
        utterance = await self.record(no_speech_seconds)
        if not utterance:
            _LOGGER.info("No speech heard")
            return False
        self.leds.set(State.THINKING)
        try:
            text = await self._transcribe(utterance)
            _LOGGER.info("Heard %.1f s of audio, transcript has %d characters",
                         len(utterance) / 32000, len(text))  # fmt: skip
            _LOGGER.debug("Transcript: %s", text)
            if not text:
                return False
            await self.speak(self.agent.respond(text))
        except SpeechServiceError as err:
            _LOGGER.error("%s", err)
            await self._play_tone(ERROR_TONE)
            return False
        _LOGGER.debug("Turn took %.1f s", time.monotonic() - started)
        return True

    async def record(self, no_speech_seconds: float) -> bytes:
        """Capture until the speaker stops talking. Returns b'' if nobody spoke."""
        self.mic.flush()
        endpointer = Endpointer(
            silence_seconds=self.config.silence_seconds,
            max_seconds=self.config.max_utterance_seconds,
            no_speech_seconds=no_speech_seconds,
            sensitivity=self.config.vad_sensitivity,
            noise_floor=self._noise_floor,
        )
        while not endpointer.finished:
            endpointer.feed(await self.mic.read())
        return endpointer.audio if endpointer.state is EndpointState.DONE else b""

    async def speak(self, deltas: AsyncIterator[str]) -> None:
        """Speak streamed text sentence by sentence: synthesis of the next sentence runs
        while the current one is playing."""
        queue: asyncio.Queue[TtsAudio | None] = asyncio.Queue()

        async def produce() -> None:
            splitter = SentenceSplitter()
            try:
                async for delta in deltas:
                    for sentence in splitter.feed(delta):
                        queue.put_nowait(await self._synthesize(sentence))
                for sentence in splitter.flush():
                    queue.put_nowait(await self._synthesize(sentence))
            finally:
                queue.put_nowait(None)

        producer = asyncio.create_task(produce())
        try:
            while (audio := await queue.get()) is not None:
                self.leds.set(State.SPEAKING)
                await self.speaker.write(audio.pcm, audio.rate, audio.width, audio.channels)
            await self.speaker.drain()
            await producer
        finally:
            producer.cancel()
            await asyncio.sleep(ECHO_TAIL_SECONDS)
            self.mic.flush()

    async def _play_tone(self, pcm: bytes) -> None:
        try:
            await self.speaker.play(pcm, TONE_RATE)
        except AudioError as err:
            _LOGGER.warning("Could not play tone: %s", err)
        self.mic.flush()

    def _track_noise(self, pcm: bytes) -> None:
        level = rms(pcm)
        self._noise_floor = level if self._noise_floor <= 0 else self._noise_floor * 0.95 + level * 0.05
