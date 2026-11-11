"""Wyoming STT/TTS/wake clients against in-process fake servers on the loopback interface."""

import asyncio
import contextlib

import pytest
from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import async_read_event, async_write_event
from wyoming.tts import Synthesize
from wyoming.wake import Detect, Detection

from test_pipeline import FakeMic, silence
from voxhub_assistant.wakeword import LocalWakeWord, WakeWordError, WyomingWakeWord
from voxhub_assistant.wyoming_clients import SpeechServiceError, synthesize, transcribe


@contextlib.asynccontextmanager
async def serve(handler):
    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        yield f"tcp://127.0.0.1:{port}"
    finally:
        server.close()


async def test_transcribe_sends_audio_and_returns_text():
    seen = {}

    async def whisper(reader, writer):
        audio = b""
        while (event := await async_read_event(reader)) is not None:
            if Transcribe.is_type(event.type):
                seen["language"] = Transcribe.from_event(event).language
            elif AudioChunk.is_type(event.type):
                chunk = AudioChunk.from_event(event)
                seen["rate"] = chunk.rate
                audio += chunk.audio
            elif AudioStop.is_type(event.type):
                seen["bytes"] = len(audio)
                await async_write_event(Transcript(text=" turn on the light ").event(), writer)
                break
        writer.close()

    async with serve(whisper) as uri:
        assert await transcribe(uri, bytes(32000), "en") == "turn on the light"
    assert seen == {"language": "en", "rate": 16000, "bytes": 32000}


async def test_synthesize_collects_audio_and_passes_voice():
    seen = {}

    async def piper(reader, writer):
        event = await async_read_event(reader)
        request = Synthesize.from_event(event)
        seen["text"], seen["voice"] = request.text, request.voice.name
        await async_write_event(AudioStart(rate=22050, width=2, channels=1).event(), writer)
        for _ in range(3):
            chunk = AudioChunk(rate=22050, width=2, channels=1, audio=b"\x01\x00" * 100)
            await async_write_event(chunk.event(), writer)
        await async_write_event(AudioStop().event(), writer)
        writer.close()

    async with serve(piper) as uri:
        audio = await synthesize(uri, "Hello there.", "en_US-lessac-medium")
    assert (audio.rate, audio.width, audio.channels, len(audio.pcm)) == (22050, 2, 1, 600)
    assert seen == {"text": "Hello there.", "voice": "en_US-lessac-medium"}


async def test_unreachable_services_raise_speech_service_error():
    with pytest.raises(SpeechServiceError):
        await transcribe("tcp://127.0.0.1:1", b"\0\0", timeout=2)
    with pytest.raises(SpeechServiceError):
        await synthesize("tcp://127.0.0.1:1", "hi", timeout=2)


async def test_closed_connection_raises():
    async def broken(reader, writer):
        writer.close()

    async with serve(broken) as uri:
        with pytest.raises(SpeechServiceError):
            await synthesize(uri, "hi", timeout=2)


async def test_wyoming_wake_word_detects_after_streaming_audio():
    seen = {"chunks": 0}

    async def openwakeword(reader, writer):
        while (event := await async_read_event(reader)) is not None:
            if Detect.is_type(event.type):
                seen["names"] = Detect.from_event(event).names
            elif AudioChunk.is_type(event.type):
                seen["chunks"] += 1
                if seen["chunks"] == 5:
                    await async_write_event(Detection(name="hey_jarvis").event(), writer)
        writer.close()

    levels = []
    async with serve(openwakeword) as uri:
        wake = WyomingWakeWord(uri, "/share/openwakeword/hey_jarvis.tflite")
        name = await asyncio.wait_for(wake.wait(FakeMic(silence(5.0)), levels.append), timeout=5)
    assert name == "hey_jarvis"
    assert seen["names"] == ["hey_jarvis"]  # custom model path is reduced to its name
    assert seen["chunks"] >= 5 and len(levels) >= 5


async def test_wake_word_service_unavailable():
    with pytest.raises(WakeWordError):
        await WyomingWakeWord("tcp://127.0.0.1:1", "hey_jarvis").wait(FakeMic(silence(1.0)))


async def test_local_wake_word_with_fake_model():
    class FakeModel:
        def __init__(self):
            self.calls = 0

        def reset(self):
            self.calls = 0

        def predict(self, samples):
            assert samples.dtype.kind == "i" and len(samples) == 1280
            self.calls += 1
            return {"hey_jarvis": 0.9 if self.calls >= 4 else 0.01}

    wake = LocalWakeWord("hey_jarvis", threshold=0.5)
    wake._model = FakeModel()
    assert await wake.wait(FakeMic(silence(2.0))) == "hey_jarvis"
    assert wake._model.calls == 4


async def test_local_wake_word_missing_package_is_a_clear_error(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "openwakeword", None)
    with pytest.raises(WakeWordError, match="not installed"):
        await LocalWakeWord("hey_jarvis").wait(FakeMic(silence(1.0)))
