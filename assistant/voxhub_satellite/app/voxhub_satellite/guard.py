from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import Awaitable, Callable, Iterable
from typing import Any

_LOGGER = logging.getLogger(__name__)

SUPERVISOR_WEBSOCKET = "ws://supervisor/core/websocket"
ASSISTANT = "conversation"
DEFAULT_PROTECTED_DOMAINS = ("lock", "alarm_control_panel")
NOTIFICATION_ID = "voxhub_guard"


class GuardError(RuntimeError):
    pass


Connector = Callable[[str], Awaitable[Any]]


class Connection:
    def __init__(self, socket: Any) -> None:
        self._socket = socket
        self._next_id = 1
        self._pending: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self.events: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        self._reader: asyncio.Task[None] | None = None

    @classmethod
    async def open(cls, url: str, token: str, connector: Connector | None = None) -> Connection:
        if connector is None:
            import websockets

            async def connector(address: str) -> Any:
                return await websockets.connect(address, max_size=64 * 1024 * 1024, open_timeout=20)

        socket = await connector(url)
        try:
            hello = json.loads(await socket.recv())
            if hello.get("type") != "auth_required":
                raise GuardError(f"unexpected greeting from Home Assistant: {hello.get('type')}")
            await socket.send(json.dumps({"type": "auth", "access_token": token}))
            reply = json.loads(await socket.recv())
            if reply.get("type") != "auth_ok":
                raise GuardError(
                    f"Home Assistant refused the token: {reply.get('message', reply.get('type'))}"
                )
        except BaseException:
            await socket.close()
            raise
        connection = cls(socket)
        connection._reader = asyncio.create_task(connection._read())
        return connection

    async def _read(self) -> None:
        try:
            while True:
                message = json.loads(await self._socket.recv())
                if message.get("type") == "event":
                    self.events.put_nowait(message.get("event", {}))
                    continue
                future = self._pending.pop(message.get("id"), None)
                if future is not None and not future.done():
                    future.set_result(message)
        except asyncio.CancelledError:
            raise
        except Exception as err:
            _LOGGER.debug("Home Assistant connection ended: %r", err)
        finally:
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(GuardError("connection to Home Assistant closed"))
            self._pending.clear()
            self.events.put_nowait(None)

    async def call(self, kind: str, timeout: float = 60.0, **payload: Any) -> Any:
        if self._reader is not None and self._reader.done():
            raise GuardError("connection to Home Assistant closed")
        message_id = self._next_id
        self._next_id += 1
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._pending[message_id] = future
        await self._socket.send(json.dumps({"id": message_id, "type": kind, **payload}))
        try:
            reply = await asyncio.wait_for(future, timeout)
        finally:
            self._pending.pop(message_id, None)
        if not reply.get("success", False):
            error = reply.get("error") or {}
            raise GuardError(f"{kind} failed: {error.get('code', '')} {error.get('message', '')}".strip())
        return reply.get("result")

    async def close(self) -> None:
        if self._reader is not None:
            self._reader.cancel()
            await asyncio.gather(self._reader, return_exceptions=True)
        await self._socket.close()


def domain_of(entity_id: str) -> str:
    return entity_id.split(".", 1)[0]


def members_of(state: dict[str, Any]) -> set[str]:
    value = state.get("attributes", {}).get("entity_id")
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return {item for item in value if isinstance(item, str)}
    return set()


def is_exposed(
    entity_id: str,
    registry: dict[str, dict[str, Any]],
    exposed: dict[str, dict[str, Any]],
    forced: set[str] | frozenset[str] = frozenset(),
) -> bool:
    entry = registry.get(entity_id)
    if entry is not None:
        setting = ((entry.get("options") or {}).get(ASSISTANT) or {}).get("should_expose")
        return True if setting is None else bool(setting)
    if exposed.get(entity_id, {}).get(ASSISTANT):
        return True
    return entity_id not in forced


TOKEN = re.compile(r"(?=\b([a-z_][a-z0-9_]*)\.([a-z0-9_]+)\b)")


def references_in(config: Any) -> set[str]:
    found: set[str] = set()
    stack = [config]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            stack.extend(item.keys())
            stack.extend(item.values())
        elif isinstance(item, (list, tuple)):
            stack.extend(item)
        elif isinstance(item, str):
            found.update(f"{domain}.{name}" for domain, name in TOKEN.findall(item.lower()))
    return found


def plan(
    states: Iterable[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
    exposed: dict[str, dict[str, Any]],
    references: dict[str, set[str]],
    protected_domains: Iterable[str],
    forced: set[str] | frozenset[str] = frozenset(),
) -> dict[str, str]:
    protected = set(protected_domains)
    known = {state.get("entity_id", "") for state in states} | set(registry) | set(exposed)
    reasons: dict[str, str] = {
        entity_id: f"{domain_of(entity_id)} entities are never available to the voice assistant"
        for entity_id in sorted(known)
        if domain_of(entity_id) in protected
    }
    members: dict[str, set[str]] = {}
    for state in states:
        found = members_of(state)
        if found:
            members[state["entity_id"]] = found
    for entity_id, referenced in references.items():
        members.setdefault(entity_id, set()).update(referenced)
    changed = True
    while changed:
        changed = False
        for entity_id in sorted(members):
            if entity_id in reasons:
                continue
            known = sorted(member for member in members[entity_id] if member in reasons)
            calls = sorted(member for member in members[entity_id] if domain_of(member) in protected)
            if known:
                reasons[entity_id] = f"it can control {known[0]}"
                changed = True
            elif calls:
                reasons[entity_id] = f"it uses {calls[0]}"
                changed = True
    return {
        entity_id: reason
        for entity_id, reason in reasons.items()
        if is_exposed(entity_id, registry, exposed, forced)
    }


def is_exposed_explicitly(entry: dict[str, Any]) -> bool:
    return ((entry.get("options") or {}).get(ASSISTANT) or {}).get("should_expose") is True


class Guard:
    def __init__(
        self,
        token: str,
        protected_domains: Iterable[str] = DEFAULT_PROTECTED_DOMAINS,
        interval: float = 300.0,
        url: str = SUPERVISOR_WEBSOCKET,
        connector: Connector | None = None,
        notify: bool = True,
    ) -> None:
        self.token = token
        self.protected_domains = tuple(
            sorted({domain.strip().lower() for domain in protected_domains if domain.strip()})
        )
        self.interval = interval
        self.url = url
        self.connector = connector
        self.notify = notify
        self.passes = 0
        self.unexposed: list[str] = []
        self.forced: set[str] = set()

    async def run(self) -> None:
        if not self.protected_domains:
            _LOGGER.warning("Exposure guard disabled: no protected domains configured")
            return
        delay = 5.0
        while True:
            try:
                connection = await Connection.open(self.url, self.token, self.connector)
            except Exception as err:
                _LOGGER.warning(
                    "Exposure guard cannot reach Home Assistant (%s); retrying in %.0f s", err, delay
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 300.0)
                continue
            delay = 5.0
            try:
                await self.watch(connection)
            except Exception as err:
                _LOGGER.warning("Exposure guard lost Home Assistant (%s); reconnecting", err)
            finally:
                await connection.close()
            await asyncio.sleep(delay)

    async def watch(self, connection: Connection) -> None:
        await connection.call("subscribe_events", event_type="entity_registry_updated")
        await self.check(connection)
        while True:
            try:
                event = await asyncio.wait_for(connection.events.get(), self.interval)
            except asyncio.TimeoutError:
                await self.check(connection)
                continue
            if event is None:
                raise GuardError("connection closed")
            await asyncio.sleep(1.0)
            while not connection.events.empty():
                if connection.events.get_nowait() is None:
                    raise GuardError("connection closed")
            await self.check(connection)

    async def related_entities(self, connection: Connection, kind: str, entity_id: str) -> set[str]:
        try:
            related = await connection.call("search/related", item_type=kind, item_id=entity_id)
        except GuardError as err:
            _LOGGER.debug("search/related failed for %s: %s", entity_id, err)
            return set()
        found: set[str] = set()
        if isinstance(related, dict):
            for key in ("entity", "group"):
                found.update(item for item in related.get(key, []) if isinstance(item, str))
        found.discard(entity_id)
        return found

    async def script_references(self, connection: Connection, entity_id: str) -> set[str]:
        try:
            result = await connection.call("script/config", entity_id=entity_id)
        except GuardError as err:
            _LOGGER.debug("script/config failed for %s: %s", entity_id, err)
            return await self.related_entities(connection, "script", entity_id)
        found = references_in((result or {}).get("config"))
        found.discard(entity_id)
        return found

    async def check(self, connection: Connection) -> dict[str, str]:
        states = await connection.call("get_states")
        entries = await connection.call("config/entity_registry/list")
        exposed = (await connection.call("homeassistant/expose_entity/list") or {}).get(
            "exposed_entities", {}
        )
        registry = {entry["entity_id"]: entry for entry in entries or [] if "entity_id" in entry}
        references: dict[str, set[str]] = {}
        for state in states:
            entity_id = state.get("entity_id", "")
            if domain_of(entity_id) == "script":
                references[entity_id] = await self.script_references(connection, entity_id)
            elif domain_of(entity_id) == "scene" and is_exposed(entity_id, registry, exposed, self.forced):
                references[entity_id] = await self.related_entities(connection, "scene", entity_id)
        violations = plan(states, registry, exposed, references, self.protected_domains, self.forced)
        self.passes += 1
        if not violations:
            _LOGGER.debug("Exposure guard pass %d: nothing to change", self.passes)
            return violations
        await connection.call(
            "homeassistant/expose_entity",
            assistants=[ASSISTANT],
            entity_ids=sorted(violations),
            should_expose=False,
        )
        self.forced.update(entity_id for entity_id in violations if entity_id not in registry)
        reported = {
            entity_id: reason
            for entity_id, reason in violations.items()
            if entity_id in registry
            and is_exposed_explicitly(registry[entity_id])
            or exposed.get(entity_id, {}).get(ASSISTANT)
        }
        for entity_id, reason in sorted(violations.items()):
            if entity_id in reported:
                _LOGGER.warning("Exposure guard: %s is no longer exposed to Assist (%s)", entity_id, reason)
            else:
                _LOGGER.info("Exposure guard: %s is kept unexposed (%s)", entity_id, reason)
            self.unexposed.append(entity_id)
        violations = reported
        if self.notify and violations:
            lines = "\n".join(
                f"- `{entity_id}`: {reason}" for entity_id, reason in sorted(violations.items())
            )
            try:
                await connection.call(
                    "call_service",
                    domain="persistent_notification",
                    service="create",
                    service_data={
                        "notification_id": NOTIFICATION_ID,
                        "title": "VoxHub: removed from the voice assistant",
                        "message": "The VoxHub exposure guard keeps locks and alarm panels away from Assist, "
                        "so that Claude can never unlock or disarm anything. These entities were "
                        f"exposed and have been un-exposed again:\n\n{lines}",
                    },
                )
            except GuardError as err:
                _LOGGER.debug("Could not create the notification: %s", err)
        return violations
