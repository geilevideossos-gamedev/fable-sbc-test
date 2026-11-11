"""Speech-to-text and text-to-speech over the Wyoming protocol (Whisper / Piper add-ons)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass

from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncClient
from wyoming.error import Error
from wyoming.tts import Synthesize, SynthesizeVoice

from .audio import CHANNELS, RATE, WIDTH

_SEND_CHUNK = 4096


class SpeechServiceError(RuntimeError):
    """A Wyoming STT/TTS service failed or is unreachable."""


@dataclass
class TtsAudio:
    pcm: bytes
    rate: int
    width: int
    channels: int


async def transcribe(uri: str, pcm: bytes, language: str = "", timeout: float = 60.0) -> str:
    """Send 16 kHz mono PCM to a Wyoming ASR server and return the transcript."""
    try:
        async with asyncio.timeout(timeout), AsyncClient.from_uri(uri) as client:
            await client.write_event(Transcribe(language=language or None).event())
            await client.write_event(AudioStart(rate=RATE, width=WIDTH, channels=CHANNELS).event())
            for offset in range(0, len(pcm), _SEND_CHUNK):
                chunk = AudioChunk(
                    rate=RATE, width=WIDTH, channels=CHANNELS, audio=pcm[offset : offset + _SEND_CHUNK]
                )
                await client.write_event(chunk.event())
            await client.write_event(AudioStop().event())
            while True:
                event = await client.read_event()
                if event is None:
                    raise SpeechServiceError("speech-to-text connection closed unexpectedly")
                if Transcript.is_type(event.type):
                    return (Transcript.from_event(event).text or "").strip()
                if Error.is_type(event.type):
                    raise SpeechServiceError(f"speech-to-text error: {Error.from_event(event).text}")
    except (OSError, asyncio.TimeoutError) as err:
        raise SpeechServiceError(f"speech-to-text unavailable at {uri}: {err!r}") from err


async def synthesize_stream(
    uri: str, text: str, voice: str = "", timeout: float = 60.0
) -> AsyncIterator[TtsAudio]:
    """Yield audio chunks from a Wyoming TTS server as they are produced."""
    request = Synthesize(text=text, voice=SynthesizeVoice(name=voice) if voice else None)
    try:
        async with asyncio.timeout(timeout), AsyncClient.from_uri(uri) as client:
            await client.write_event(request.event())
            while True:
                event = await client.read_event()
                if event is None:
                    raise SpeechServiceError("text-to-speech connection closed unexpectedly")
                if AudioChunk.is_type(event.type):
                    chunk = AudioChunk.from_event(event)
                    yield TtsAudio(chunk.audio, chunk.rate, chunk.width, chunk.channels)
                elif AudioStop.is_type(event.type):
                    return
                elif Error.is_type(event.type):
                    raise SpeechServiceError(f"text-to-speech error: {Error.from_event(event).text}")
    except (OSError, asyncio.TimeoutError) as err:
        raise SpeechServiceError(f"text-to-speech unavailable at {uri}: {err!r}") from err


async def synthesize(uri: str, text: str, voice: str = "", timeout: float = 60.0) -> TtsAudio:
    """Synthesize ``text`` and return the whole utterance as one buffer."""
    parts: list[TtsAudio] = []
    async for part in synthesize_stream(uri, text, voice, timeout):
        parts.append(part)
    if not parts:
        raise SpeechServiceError("text-to-speech returned no audio")
    first = parts[0]
    return TtsAudio(b"".join(p.pcm for p in parts), first.rate, first.width, first.channels)
