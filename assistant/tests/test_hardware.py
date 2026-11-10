"""LEDs, mute switch parsing and audio subprocess wrappers, all without hardware."""

import asyncio
import struct
import sys

import pytest

from voxhub_assistant.audio import CHUNK_BYTES, AudioError, Microphone, Speaker
from voxhub_assistant.leds import BLUE, EV_SW, GREEN, SW_MUTE_DEVICE, Leds, MuteSwitch, State
from voxhub_assistant.leds import parse_switch_events as parse


def read_led(root, led):
    return (root / led / "brightness").read_text()


@pytest.fixture
def led_root(tmp_path):
    for led in (GREEN, BLUE):
        (tmp_path / led).mkdir()
        (tmp_path / led / "brightness").write_text("0")
    return tmp_path


async def test_led_patterns(led_root):
    leds = Leds(True, led_root)
    assert leds.enabled
    leds.set(State.IDLE)
    assert (read_led(led_root, GREEN), read_led(led_root, BLUE)) == ("1", "0")
    leds.set(State.LISTENING)
    assert (read_led(led_root, GREEN), read_led(led_root, BLUE)) == ("0", "1")
    leds.set(State.SPEAKING)
    assert (read_led(led_root, GREEN), read_led(led_root, BLUE)) == ("1", "1")
    leds.set(State.THINKING)  # starts a blink task
    await asyncio.sleep(0)
    leds.off()
    assert (read_led(led_root, GREEN), read_led(led_root, BLUE)) == ("0", "0")


async def test_leds_fail_soft(tmp_path, led_root):
    missing = Leds(True, tmp_path / "nope")
    assert not missing.enabled
    missing.set(State.LISTENING)  # no-op, no exception
    assert missing.state is State.LISTENING

    leds = Leds(True, led_root)
    (led_root / GREEN / "brightness").unlink()
    (led_root / GREEN / "brightness").mkdir()  # writing now fails (read-only sysfs stand-in)
    leds.set(State.IDLE)
    assert not leds.enabled


def test_parse_switch_events():
    event = struct.Struct("llHHi")
    mute_on = event.pack(0, 0, EV_SW, SW_MUTE_DEVICE, 1)
    mute_off = event.pack(0, 0, EV_SW, SW_MUTE_DEVICE, 0)
    other = event.pack(0, 0, 1, 30, 1)  # a key press
    assert parse(mute_on) is True
    assert parse(mute_on + other + mute_off) is False
    assert parse(other) is None
    assert parse(b"") is None


async def test_mute_switch_absent_is_ignored():
    switch = MuteSwitch(True, device_name="no-such-device-voxhub-test")
    assert switch.muted is False
    switch.close()
    assert MuteSwitch(False).muted is False


async def test_microphone_reads_chunks_from_subprocess():
    script = f"import sys; sys.stdout.buffer.write(bytes({CHUNK_BYTES} * 3))"
    mic = Microphone(command=f"{sys.executable} -c '{script}'", gain=2.0)
    await mic.start()
    for _ in range(3):
        assert len(await asyncio.wait_for(mic.read(), 5)) == CHUNK_BYTES
    with pytest.raises(AudioError):  # process ended
        await asyncio.wait_for(mic.read(), 5)
    with pytest.raises(AudioError):  # and it stays failed until restarted
        await asyncio.wait_for(mic.read(), 5)
    await mic.stop()


async def test_microphone_missing_binary():
    with pytest.raises(AudioError):
        await Microphone(command="/nonexistent/parec-voxhub-test").start()


async def test_microphone_drops_oldest_when_nobody_reads():
    mic = Microphone()
    for i in range(40):
        mic._put(bytes([i]))
    assert mic._queue.qsize() == 25
    assert await mic.read() == bytes([15])
    mic.flush()
    assert mic._queue.empty()


async def test_speaker_pipes_volume_scaled_audio(tmp_path):
    out = tmp_path / "out.raw"
    script = f'import sys; open(r"{out}", "ab").write(sys.stdin.buffer.read())'
    speaker = Speaker(command=f"{sys.executable} -c '{script}' {{rate}} {{channels}} {{format}}", volume=0.5)
    pcm = struct.pack("<4h", 1000, -1000, 2000, 30000)
    await speaker.write(pcm, 22050)
    await speaker.write(pcm, 22050)  # same format: same process
    await speaker.drain()
    assert struct.unpack("<8h", out.read_bytes()) == (500, -500, 1000, 15000) * 2


async def test_speaker_missing_binary():
    with pytest.raises(AudioError):
        await Speaker(command="/nonexistent/pacat-voxhub-test").play(b"\0\0", 16000)
