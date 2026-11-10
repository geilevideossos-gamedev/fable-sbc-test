import asyncio

import numpy as np

from conftest import FakeAnthropic, message, text_block
from voxhub_assistant.agent import ClaudeAgent
from voxhub_assistant.audio import AudioError
from voxhub_assistant.leds import Leds, State
from voxhub_assistant.pipeline import Assistant
from voxhub_assistant.wyoming_clients import SpeechServiceError, TtsAudio

RATE = 16000
CHUNK = 2560


def chunks(pcm: bytes) -> list[bytes]:
    return [pcm[i : i + CHUNK] for i in range(0, len(pcm) - CHUNK + 1, CHUNK)]


def silence(seconds: float) -> bytes:
    return bytes(int(RATE * seconds) * 2)


def speech(seconds: float) -> bytes:
    t = np.arange(int(RATE * seconds)) / RATE
    return (np.sin(2 * np.pi * 200 * t) * 5000).astype("<i2").tobytes()


class FakeMic:
    def __init__(self, pcm: bytes) -> None:
        self.pending = chunks(pcm)
        self.flushes = 0

    async def start(self) -> None: ...
    async def stop(self) -> None: ...

    def flush(self) -> None:
        self.flushes += 1

    async def read(self) -> bytes:
        await asyncio.sleep(0)
        if not self.pending:
            raise AudioError("out of test audio")
        return self.pending.pop(0)


class FakeSpeaker:
    def __init__(self) -> None:
        self.written: list[tuple[bytes, int]] = []
        self.drains = 0

    async def write(self, pcm, rate, width=2, channels=1):
        self.written.append((pcm, rate))

    async def drain(self):
        self.drains += 1

    async def play(self, pcm, rate, width=2, channels=1):
        self.written.append((pcm, rate))


class FakeWake:
    def __init__(self, after_chunks: int = 3) -> None:
        self.after = after_chunks

    async def wait(self, mic, on_chunk=None) -> str:
        for _ in range(self.after):
            pcm = await mic.read()
            if on_chunk:
                on_chunk(pcm)
        return "hey_jarvis"


def build(config, tools, mic_pcm, responses, transcript="turn on the light", tts_fail=False):
    spoken: list[str] = []
    heard: list[bytes] = []

    async def transcriber(pcm: bytes) -> str:
        heard.append(pcm)
        return transcript

    async def synthesizer(text: str) -> TtsAudio:
        if tts_fail:
            raise SpeechServiceError("piper down")
        spoken.append(text)
        return TtsAudio(text.encode(), 22050, 2, 1)

    config.wake_sound = False
    mic, speaker = FakeMic(mic_pcm), FakeSpeaker()
    agent = ClaudeAgent(config, tools, client=FakeAnthropic(responses))
    assistant = Assistant(
        config, mic, speaker, FakeWake(), agent, Leds(enabled=False),  # type: ignore[arg-type]
        transcriber=transcriber, synthesizer=synthesizer,
    )  # fmt: skip
    return assistant, mic, speaker, spoken, heard


async def test_full_turn_wake_record_stt_claude_tts(config, tools, monkeypatch):
    monkeypatch.setattr("voxhub_assistant.pipeline.ECHO_TAIL_SECONDS", 0)
    audio = silence(0.5) + speech(1.0) + silence(1.5)
    reply = message([text_block("The kitchen light is on. Anything else I can do?")])
    assistant, mic, speaker, spoken, heard = build(config, tools, audio, [reply])

    await assistant.run_once()

    assert len(heard) == 1 and 1.0 < len(heard[0]) / 2 / RATE < 2.2
    assert spoken == ["The kitchen light is on.", "Anything else I can do?"]  # sentence by sentence
    assert [rate for _, rate in speaker.written] == [22050, 22050]
    assert speaker.drains == 1
    assert mic.flushes >= 3  # before wake, before recording, after speaking (half-duplex)
    assert assistant.leds.state is State.SPEAKING


async def test_no_speech_after_wake_word_returns_to_idle(config, tools):
    config.no_speech_timeout = 1.0
    assistant, _, speaker, spoken, heard = build(config, tools, silence(3.0), [])
    await assistant.run_once()
    assert heard == [] and spoken == [] and speaker.written == []


async def test_empty_transcript_skips_claude(config, tools):
    audio = silence(0.4) + speech(0.8) + silence(1.5)
    assistant, _, _, spoken, heard = build(config, tools, audio, [], transcript="")
    assert await assistant.handle_turn(5.0) is False
    assert len(heard) == 1 and spoken == []


async def test_follow_up_listens_again_without_wake_word(config, tools, monkeypatch):
    monkeypatch.setattr("voxhub_assistant.pipeline.ECHO_TAIL_SECONDS", 0)
    config.follow_up = True
    config.follow_up_seconds = 1.0
    turn = speech(0.8) + silence(1.2)
    audio = silence(0.4) + turn + turn + silence(2.0)
    replies = [
        message([text_block("First answer is here.")]),
        message([text_block("Second answer is here.")]),
    ]
    assistant, _, _, spoken, heard = build(config, tools, audio, replies)

    await assistant.run_once()

    assert len(heard) == 2
    assert spoken == ["First answer is here.", "Second answer is here."]


async def test_tts_failure_plays_error_tone_instead_of_crashing(config, tools, monkeypatch):
    monkeypatch.setattr("voxhub_assistant.pipeline.ECHO_TAIL_SECONDS", 0)
    audio = silence(0.4) + speech(0.8) + silence(1.5)
    assistant, _, speaker, _, _ = build(
        config, tools, audio, [message([text_block("Hello there, friend.")])], tts_fail=True
    )
    assert await assistant.handle_turn(5.0) is False
    assert len(speaker.written) == 1  # the error tone
