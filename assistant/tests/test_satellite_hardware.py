import asyncio
import os
import struct

from voxhub_satellite.hardware import (
    BLUE,
    EV_KEY,
    EV_SW,
    GREEN,
    KEY_MICMUTE,
    SW_MUTE_DEVICE,
    Leds,
    MuteSwitch,
    Show,
    find_mute_device,
    has_bit,
    parse_events,
)


def make_leds(tmp_path):
    for led in (GREEN, BLUE):
        (tmp_path / led).mkdir()
        (tmp_path / led / "brightness").write_text("0")
    return tmp_path


def lit(root):
    return ((root / GREEN / "brightness").read_text(), (root / BLUE / "brightness").read_text())


def event(kind, code, value):
    return struct.pack("llHHi", 0, 0, kind, code, value)


async def test_steady_patterns(tmp_path):
    root = make_leds(tmp_path)
    leds = Leds(True, root)
    assert leds.enabled
    expected = {
        Show.IDLE: ("1", "0"),
        Show.LISTENING: ("0", "1"),
        Show.SPEAKING: ("1", "1"),
        Show.MUTED: ("0", "0"),
    }
    for show, values in expected.items():
        leds.set(show)
        assert lit(root) == values
    leds.close()
    assert lit(root) == ("0", "0")


async def test_blinking_pattern(tmp_path, monkeypatch):
    root = make_leds(tmp_path)
    leds = Leds(True, root)
    seen = set()
    real_sleep = asyncio.sleep

    async def quick(seconds):
        seen.add(lit(root))
        await real_sleep(0)

    monkeypatch.setattr("voxhub_satellite.hardware.asyncio.sleep", quick)
    leds.set(Show.THINKING)
    for _ in range(10):
        await real_sleep(0)
    assert seen == {("0", "1"), ("0", "0")}
    leds.set(Show.IDLE)
    assert lit(root) == ("1", "0")
    leds.close()


async def test_missing_leds_are_ignored(tmp_path):
    leds = Leds(True, tmp_path)
    assert not leds.enabled
    leds.set(Show.ERROR)
    leds.close()


async def test_unwritable_led_disables_feedback(tmp_path):
    root = make_leds(tmp_path)
    leds = Leds(True, root)
    (root / GREEN / "brightness").unlink()
    (root / GREEN / "brightness").mkdir()
    leds.set(Show.IDLE)
    assert not leds.enabled


def test_parse_events():
    assert parse_events(b"") is None
    assert parse_events(event(EV_KEY, KEY_MICMUTE, 1)) is True
    assert parse_events(event(EV_KEY, KEY_MICMUTE, 1) + event(EV_KEY, KEY_MICMUTE, 0)) is False
    assert parse_events(event(EV_SW, SW_MUTE_DEVICE, 1)) is True
    assert parse_events(event(EV_KEY, KEY_MICMUTE, 2)) is None
    assert parse_events(event(EV_KEY, 30, 1)) is None


def test_has_bit():
    assert has_bit("4000", SW_MUTE_DEVICE)
    assert has_bit("100000000000000 0 0 0", KEY_MICMUTE)
    assert not has_bit("0", KEY_MICMUTE)
    assert not has_bit("zz", 1)


def fake_input(root, number, name, key="0", sw="0"):
    device = root / f"event{number}" / "device"
    (device / "capabilities").mkdir(parents=True)
    (device / "name").write_text(name + "\n")
    (device / "capabilities" / "key").write_text(key + "\n")
    (device / "capabilities" / "sw").write_text(sw + "\n")


def test_find_mute_device(tmp_path):
    fake_input(tmp_path, 0, "vc4-hdmi", key="100000000000000 0 0 0")
    assert find_mute_device(tmp_path) is None
    fake_input(tmp_path, 1, "voxhub-mute", key="100000000000000 0 0 0")
    assert find_mute_device(tmp_path) == ("/dev/input/event1", False)
    fake_input(tmp_path, 2, "voxhub-switches", sw="4000")
    assert find_mute_device(tmp_path) == ("/dev/input/event1", False)


async def test_mute_switch_reads_events(tmp_path, monkeypatch):
    read_fd, write_fd = os.pipe()
    fake_input(tmp_path, 3, "voxhub-mute", key="100000000000000 0 0 0")
    monkeypatch.setattr("voxhub_satellite.hardware.os.open", lambda path, flags: read_fd)
    monkeypatch.setattr("voxhub_satellite.hardware.fcntl.ioctl", lambda fd, req, buffer: bytes(len(buffer)))
    changes = []
    switch = MuteSwitch(True, changes.append, tmp_path)
    assert switch.available and not switch.muted
    os.write(write_fd, event(EV_KEY, KEY_MICMUTE, 1))
    for _ in range(50):
        if changes:
            break
        await asyncio.sleep(0.01)
    assert changes == [True] and switch.muted
    os.write(write_fd, event(EV_KEY, KEY_MICMUTE, 0))
    for _ in range(50):
        if len(changes) == 2:
            break
        await asyncio.sleep(0.01)
    assert changes == [True, False]
    switch.close()
    os.close(write_fd)


async def test_mute_switch_absent(tmp_path):
    switch = MuteSwitch(True, None, tmp_path)
    assert not switch.available and not switch.muted
    switch.close()
