import numpy as np
import pytest

from voxhub_assistant.audio import DcBlocker, apply_gain, tone
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


def offset(pcm: bytes, level: int) -> bytes:
    return (
        (np.frombuffer(pcm, dtype="<i2").astype(np.int32) + level).clip(-32768, 32767).astype("<i2").tobytes()
    )


def blocked(pcm: bytes, chunk: int = 2560) -> bytes:
    blocker = DcBlocker()
    return b"".join(blocker.process(pcm[i : i + chunk]) for i in range(0, len(pcm), chunk))


def test_dc_level_hides_speech_from_the_endpointer_unless_blocked():
    recording = offset(noise(0.5) + speech(1.5) + noise(3.0), 662)
    assert run(Endpointer(silence_seconds=0.8), recording)[0] is not EndpointState.DONE
    state, used = run(Endpointer(silence_seconds=0.8), blocked(recording))
    assert state is EndpointState.DONE
    assert 2.5 < used < 3.2
    for level in (166, 1324, -662):
        shifted = blocked(offset(noise(0.5) + speech(1.5) + noise(3.0), level))
        assert run(Endpointer(silence_seconds=0.8), shifted)[0] is EndpointState.DONE
    silent = blocked(offset(noise(4.0), 662))
    assert run(Endpointer(no_speech_seconds=2.0), silent)[0] is EndpointState.TIMEOUT


def test_dc_blocker_removes_offset_and_keeps_speech():
    steady = np.frombuffer(blocked(np.full(RATE, 662, dtype="<i2").tobytes()), dtype="<i2")
    assert np.abs(steady).max() == 0
    step = np.concatenate([np.zeros(RATE // 2), np.full(RATE // 2, 662)]).astype("<i2").tobytes()
    settled = np.frombuffer(blocked(step), dtype="<i2")[RATE // 2 + int(0.081 * RATE) :]
    assert np.abs(settled).max() <= 1
    voice = speech(1.0)
    assert 0.99 < rms(blocked(offset(voice, 662))[RATE // 2 :]) / rms(voice[RATE // 2 :]) < 1.01
    assert blocked(voice, 2560) == blocked(voice, 320) == DcBlocker().process(voice)
    assert DcBlocker().process(b"") == b""


def recursion(pcm: bytes, pole: float) -> list[int]:
    samples = np.frombuffer(pcm, dtype="<i2").astype(np.float64)
    out, last_in, last_out = [], samples[0], 0.0
    for sample in samples:
        last_out = sample - last_in + pole * last_out
        last_in = sample
        out.append(last_out)
    return np.clip(np.rint(out), -32768, 32767).astype(int).tolist()


def test_dc_blocker_handles_long_buffers_and_other_poles():
    long = offset(noise(1.0) + speech(10.0) + noise(1.0), 662)
    whole = DcBlocker().process(long)
    assert whole == blocked(long)
    assert np.abs(np.frombuffer(whole, dtype="<i2")[-RATE // 2 :]).max() < 200
    short = offset(speech(0.5), -300)
    for pole in (0.5, 0.9, 0.995, 0.9999):
        assert np.frombuffer(DcBlocker(pole).process(short), dtype="<i2").tolist() == recursion(short, pole)
    for pole in (0.0, 1.0, -0.5, 1.5):
        with pytest.raises(ValueError):
            DcBlocker(pole)


def test_dc_blocker_applies_gain_before_rounding():
    ramp = (np.arange(RATE) % 7).astype("<i2").tobytes()
    plain = np.frombuffer(DcBlocker().process(ramp), dtype="<i2")
    louder = np.frombuffer(DcBlocker().process(ramp, 8.0), dtype="<i2")
    assert np.abs(louder - 8 * plain).max() <= 4
    assert len(set((louder % 8).tolist())) > 1
    assert DcBlocker().process(offset(speech(0.2), 662), 1.0) == DcBlocker().process(offset(speech(0.2), 662))


def test_gain_scales_and_clips():
    quiet = np.array([100, -200, 20000], dtype="<i2").tobytes()
    assert np.frombuffer(apply_gain(quiet, 2.0), dtype="<i2").tolist() == [200, -400, 32767]
    assert apply_gain(quiet, 1.0) is quiet
    assert np.abs(np.frombuffer(apply_gain(quiet, 0.5), dtype="<i2")).max() == 10000


def test_tone_has_expected_length():
    assert len(tone(880, 100, 22050)) == 2205 * 2
