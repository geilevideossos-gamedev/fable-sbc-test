from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from .hardware import Show

_LOGGER = logging.getLogger(__name__)

PERIPHERAL_URL = "ws://127.0.0.1:6055"
ERROR_SECONDS = 2.0
TIMER_RING_LIMIT = 900.0

PHASES = {
    "wake_word_detected": Show.LISTENING,
    "listening": Show.LISTENING,
    "thinking": Show.THINKING,
    "tts_speaking": Show.SPEAKING,
    "tts_finished": Show.IDLE,
    "idle": Show.IDLE,
    "timer_ticking": Show.IDLE,
    "timer_ringing": Show.TIMER,
    "media_player_playing": Show.IDLE,
}

Connector = Callable[[str], Awaitable[Any]]


class Bridge:
    def __init__(
        self,
        leds: Any,
        url: str = PERIPHERAL_URL,
        connector: Connector | None = None,
        clock: Callable[[], float] = time.monotonic,
        timer_ring_limit: float = TIMER_RING_LIMIT,
    ) -> None:
        self.leds = leds
        self.url = url
        self.connector = connector
        self.clock = clock
        self.timer_ring_limit = timer_ring_limit
        self.socket: Any = None
        self.linked = False
        self.ha_connected = False
        self.lva_muted = False
        self.hardware_muted = False
        self.muted_by_switch = False
        self.resync_delay = 1.0
        self.phase = Show.IDLE
        self.error_until = 0.0
        self.ringing_since = 0.0
        self.sent: list[str] = []
        self._refresh: asyncio.TimerHandle | None = None

    def show(self) -> Show:
        now = self.clock()
        if not self.linked or not self.ha_connected:
            return Show.DISCONNECTED
        if self.hardware_muted or self.lva_muted:
            return Show.MUTED
        if now < self.error_until:
            return Show.ERROR
        if self.phase is Show.TIMER and now - self.ringing_since > self.timer_ring_limit:
            self.phase = Show.IDLE
        return self.phase

    def update(self) -> None:
        self.leds.set(self.show())
        if self._refresh is not None:
            self._refresh.cancel()
            self._refresh = None
        now = self.clock()
        wake = None
        if now < self.error_until:
            wake = self.error_until - now
        elif self.phase is Show.TIMER:
            wake = max(0.0, self.ringing_since + self.timer_ring_limit - now)
        if wake is not None:
            self._refresh = asyncio.get_running_loop().call_later(wake + 0.01, self.update)

    async def send(self, command: str) -> None:
        if self.socket is None:
            return
        try:
            await self.socket.send(json.dumps({"command": command}))
            self.sent.append(command)
        except Exception as err:
            _LOGGER.debug("Could not send %s: %r", command, err)

    async def assert_mute(self) -> None:
        if not self.ha_connected or self.socket is None:
            return
        if self.hardware_muted and not self.lva_muted:
            self.muted_by_switch = True
            await self.send("mute_mic")
        elif not self.hardware_muted and self.lva_muted and self.muted_by_switch:
            await self.send("unmute_mic")

    def on_hardware_mute(self, muted: bool) -> None:
        previous = self.hardware_muted
        self.hardware_muted = muted
        self.update()
        if muted != previous:
            asyncio.get_running_loop().create_task(self.assert_mute())

    def connected(self) -> None:
        if not self.ha_connected:
            self.ha_connected = True
            asyncio.get_running_loop().create_task(self.assert_mute())

    def resync(self) -> None:
        socket = self.socket
        if socket is not None:
            asyncio.get_running_loop().create_task(socket.close())

    async def handle(self, message: dict[str, Any]) -> None:
        event = message.get("event")
        data = message.get("data") or {}
        if event == "snapshot":
            self.ha_connected = bool(data.get("ha_connected"))
            self.lva_muted = bool(data.get("muted"))
            self.phase = Show.IDLE
            self.error_until = 0.0
            self.update()
            await self.assert_mute()
            return
        if event == "muted":
            self.lva_muted = bool(data.get("muted"))
            if not self.lva_muted:
                self.muted_by_switch = False
            self.update()
            await self.assert_mute()
            return
        if event == "zeroconf" and data.get("status") == "connected":
            self.ha_connected = True
            self.update()
            await self.assert_mute()
            return
        if event == "disconnected":
            self.ha_connected = False
            self.phase = Show.IDLE
            self.error_until = 0.0
            self.update()
            asyncio.get_running_loop().call_later(self.resync_delay, self.resync)
            return
        if event == "pipeline_error":
            self.error_until = self.clock() + ERROR_SECONDS
            self.update()
            return
        if event in PHASES:
            self.connected()
            if event == "timer_ringing" and self.phase is not Show.TIMER:
                self.ringing_since = self.clock()
            self.phase = PHASES[event]
            self.update()

    async def connect(self) -> Any:
        if self.connector is not None:
            return await self.connector(self.url)
        import websockets

        return await websockets.connect(self.url, open_timeout=10, max_size=1024 * 1024)

    async def session(self) -> None:
        socket = await self.connect()
        self.socket = socket
        self.linked = True
        _LOGGER.info("Connected to the voice satellite at %s", self.url)
        try:
            while True:
                raw = await socket.recv()
                try:
                    message = json.loads(raw)
                except (TypeError, ValueError):
                    continue
                if isinstance(message, dict):
                    await self.handle(message)
        finally:
            self.socket = None
            self.linked = False
            self.update()
            try:
                await socket.close()
            except Exception as err:
                _LOGGER.debug("Closing the peripheral connection failed: %r", err)

    async def run(self) -> None:
        delay = 1.0
        self.update()
        while True:
            try:
                await self.session()
                delay = 1.0
            except asyncio.CancelledError:
                raise
            except Exception as err:
                _LOGGER.debug("Voice satellite not reachable at %s: %r", self.url, err)
                delay = min(delay * 2, 10.0)
            await asyncio.sleep(delay)

    def close(self) -> None:
        if self._refresh is not None:
            self._refresh.cancel()
            self._refresh = None
