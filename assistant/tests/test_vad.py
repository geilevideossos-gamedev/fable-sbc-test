import numpy as np

from voxhub_assistant.audio import apply_gain, tone
from voxhub_assistant.vad import Endpointer, EndpointState, rms

RATE = 16000
rng = np.random.default_rng(1234)


def noise(seconds: float, level: float = 30.0) -> bytes:
    return (rng.normal(0, level, int(RATE * seconds))).astype("<i2").tobytes()


def speech(seconds: float, level: float = 4000.0) -> bytes:
    t = np.arange(int(RATE * seconds)) / RATE
    wave = np.sin(2 * np.pi * 220 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t))
    return (wave * level).astype("<i2").tobytes()


def run(endpointer: Endpointer, pcm: bytes, chunk: int = 2560):
    """Feed in 80 ms chunks; return (state, seconds consumed)."""
    for offset in range(0, len(pcm), chunk):
        if endpointer.feed(pcm[offset : offset + chunk]) in (EndpointState.DONE, EndpointState.TIMEOUT):
            return endpointer.state, (offset + chunk) / 2 / RATE
    return endpointer.state, len(pcm) / 2 / RATE


def test_rms():
    assert rms(b"") == 0.0
    assert rms(np.full(160, 1000, dtype="<i2").tobytes()) == 1000.0


def test_endpoint_after_trailing_silence():
    endpointer = Endpointer(silence_seconds=0.8)
    state, used = run(endpointer, noise(0.5) + speech(1.5) + noise(3.0))
    assert state is EndpointState.DONE
    # Ends about 0.8 s after speech stops at t=2.0 s, not at the end of the buffer.
    assert 2.7 <= used <= 3.1
    # Recording keeps a short pre-roll, all speech and the trailing silence.
    assert 2.3 <= len(endpointer.audio) / 2 / RATE <= 2.9


def test_short_pause_does_not_end_utterance():
    endpointer = Endpointer(silence_seconds=0.8)
    state, used = run(endpointer, noise(0.3) + speech(1.0) + noise(0.4) + speech(1.0) + noise(2.0))
    assert state is EndpointState.DONE
    assert used >= 3.4


def test_timeout_when_nobody_speaks():
    endpointer = Endpointer(no_speech_seconds=2.0)
    state, used = run(endpointer, noise(5.0))
    assert state is EndpointState.TIMEOUT
    assert 1.9 <= used <= 2.2
    assert endpointer.finished


def test_max_duration_cuts_endless_speech():
    endpointer = Endpointer(max_seconds=3.0)
    state, used = run(endpointer, speech(10.0))
    assert state is EndpointState.DONE
    assert used <= 3.3


def test_click_is_not_speech():
    endpointer = Endpointer(no_speech_seconds=2.0)
    state, _ = run(endpointer, noise(0.5) + speech(0.04, 20000) + noise(3.0))
    assert state is EndpointState.TIMEOUT


def test_adapts_to_loud_background_noise():
    # A steady 600 RMS hum is far above min_rms but must not count as speech.
    endpointer = Endpointer(no_speech_seconds=2.0, noise_floor=600.0)
    assert run(endpointer, noise(4.0, 600.0))[0] is EndpointState.TIMEOUT
    endpointer = Endpointer(noise_floor=600.0)
    assert run(endpointer, noise(0.5, 600.0) + speech(1.0, 8000) + noise(2.0, 600.0))[0] is EndpointState.DONE


def test_gain_scales_and_clips():
    quiet = np.array([100, -200, 20000], dtype="<i2").tobytes()
    assert np.frombuffer(apply_gain(quiet, 2.0), dtype="<i2").tolist() == [200, -400, 32767]
    assert apply_gain(quiet, 1.0) is quiet
    assert np.abs(np.frombuffer(apply_gain(quiet, 0.5), dtype="<i2")).max() == 10000


def test_tone_has_expected_length():
    assert len(tone(880, 100, 22050)) == 2205 * 2
