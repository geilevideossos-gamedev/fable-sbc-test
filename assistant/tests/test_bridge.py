import asyncio
import json

import pytest

from voxhub_satellite.bridge import Bridge
from voxhub_satellite.hardware import Show


class FakeLeds:
    def __init__(self):
        self.shows = []

    def set(self, show):
        self.shows.append(show)

    @property
    def now(self):
        return self.shows[-1]


class FakeSocket:
    def __init__(self):
        self.incoming = asyncio.Queue()
        self.sent = []
        self.closed = False

    async def recv(self):
        item = await self.incoming.get()
        if item is None:
            raise ConnectionError("closed")
        return item

    async def send(self, raw):
        self.sent.append(json.loads(raw)["command"])

    async def close(self):
        self.closed = True

    def push(self, event, data=None):
        message = {"event": event}
        if data is not None:
            message["data"] = data
        self.incoming.put_nowait(json.dumps(message))


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


async def settle():
    for _ in range(20):
        await asyncio.sleep(0)


@pytest.fixture
async def linked():
    socket = FakeSocket()
    leds = FakeLeds()
    clock = Clock()

    async def connector(url):
        return socket

    bridge = Bridge(leds, connector=connector, clock=clock, timer_ring_limit=60)
    task = asyncio.create_task(bridge.session())
    await settle()
    yield bridge, socket, leds, clock
    socket.incoming.put_nowait(None)
    await asyncio.gather(task, return_exceptions=True)
    bridge.close()


async def test_disconnected_until_snapshot(linked):
    bridge, socket, leds, _ = linked
    assert bridge.show() is Show.DISCONNECTED
    socket.push("snapshot", {"muted": False, "ha_connected": False})
    await settle()
    assert leds.now is Show.DISCONNECTED
    socket.push("zeroconf", {"status": "connected"})
    await settle()
    assert leds.now is Show.IDLE


async def test_pipeline_phases(linked):
    bridge, socket, leds, _ = linked
    socket.push("snapshot", {"muted": False, "ha_connected": True})
    for event, show in (
        ("wake_word_detected", Show.LISTENING),
        ("listening", Show.LISTENING),
        ("stt_text", Show.LISTENING),
        ("thinking", Show.THINKING),
        ("tts_text", Show.THINKING),
        ("tts_speaking", Show.SPEAKING),
        ("tts_finished", Show.IDLE),
    ):
        socket.push(event, {"text": "x"} if event.endswith("_text") else None)
        await settle()
        assert leds.now is show, event


async def test_error_is_shown_briefly(linked):
    bridge, socket, leds, clock = linked
    socket.push("snapshot", {"muted": False, "ha_connected": True})
    socket.push("pipeline_error")
    socket.push("tts_finished")
    socket.push("idle")
    await settle()
    assert leds.now is Show.ERROR
    clock.now += 3
    bridge.update()
    assert leds.now is Show.IDLE


async def test_timer_ringing_falls_back_to_idle(linked):
    bridge, socket, leds, clock = linked
    socket.push("snapshot", {"muted": False, "ha_connected": True})
    socket.push("timer_ringing", {"id": "t", "seconds_left": 0})
    await settle()
    assert leds.now is Show.TIMER
    clock.now += 61
    bridge.update()
    assert leds.now is Show.IDLE


async def test_hardware_mute_is_reported_and_reasserted(linked):
    bridge, socket, leds, _ = linked
    bridge.on_hardware_mute(True)
    assert leds.now is Show.DISCONNECTED
    socket.push("snapshot", {"muted": False, "ha_connected": True})
    await settle()
    assert socket.sent == ["mute_mic"]
    assert leds.now is Show.MUTED
    socket.push("muted", {"muted": True})
    await settle()
    socket.push("muted", {"muted": False})
    await settle()
    assert socket.sent == ["mute_mic", "mute_mic"]
    socket.push("muted", {"muted": True})
    await settle()
    bridge.on_hardware_mute(False)
    await settle()
    assert socket.sent[-1] == "unmute_mic"
    socket.push("muted", {"muted": False})
    socket.push("idle")
    await settle()
    assert leds.now is Show.IDLE


async def test_software_mute_from_home_assistant_is_kept(linked):
    bridge, socket, leds, _ = linked
    socket.push("snapshot", {"muted": False, "ha_connected": True})
    socket.push("muted", {"muted": True})
    await settle()
    assert leds.now is Show.MUTED
    assert socket.sent == []


async def test_reconnect_reasserts_mute(linked):
    bridge, socket, leds, _ = linked
    socket.push("snapshot", {"muted": False, "ha_connected": False})
    await settle()
    bridge.on_hardware_mute(True)
    await settle()
    assert socket.sent == []
    socket.push("zeroconf", {"status": "connected"})
    await settle()
    assert socket.sent == ["mute_mic"]
    assert leds.now is Show.MUTED
    socket.push("disconnected")
    await settle()
    assert leds.now is Show.DISCONNECTED
    socket.push("zeroconf", {"status": "connected"})
    await settle()
    assert socket.sent == ["mute_mic", "mute_mic"]
    assert leds.now is Show.MUTED


async def test_invalid_messages_are_ignored(linked):
    bridge, socket, leds, _ = linked
    socket.incoming.put_nowait("not json")
    socket.incoming.put_nowait(json.dumps(["list"]))
    socket.push("snapshot", {"muted": False, "ha_connected": True})
    await settle()
    assert leds.now is Show.IDLE


async def test_lost_connection_shows_disconnected():
    socket = FakeSocket()
    leds = FakeLeds()

    async def connector(url):
        return socket

    bridge = Bridge(leds, connector=connector)
    task = asyncio.create_task(bridge.session())
    socket.push("snapshot", {"muted": False, "ha_connected": True})
    await settle()
    assert leds.now is Show.IDLE
    socket.incoming.put_nowait(None)
    with pytest.raises(ConnectionError):
        await task
    assert leds.now is Show.DISCONNECTED
    assert socket.closed


async def test_run_retries(monkeypatch):
    attempts = []

    async def failing(url):
        attempts.append(url)
        raise OSError("refused")

    real_sleep = asyncio.sleep
    delays = []

    async def fake_sleep(seconds):
        delays.append(seconds)
        if len(delays) == 4:
            raise asyncio.CancelledError
        await real_sleep(0)

    monkeypatch.setattr("voxhub_satellite.bridge.asyncio.sleep", fake_sleep)
    bridge = Bridge(FakeLeds(), connector=failing)
    with pytest.raises(asyncio.CancelledError):
        await bridge.run()
    assert len(attempts) == 4
    assert delays == [2.0, 4.0, 8.0, 10.0]
