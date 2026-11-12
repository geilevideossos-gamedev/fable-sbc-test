import asyncio
import json

import pytest

from voxhub_satellite.guard import Connection, Guard, GuardError, plan


def state(entity_id, members=None):
    attributes = {"friendly_name": entity_id}
    if members is not None:
        attributes["entity_id"] = members
    return {"entity_id": entity_id, "state": "on", "attributes": attributes}


def entry(entity_id, should_expose=None):
    options = {} if should_expose is None else {"conversation": {"should_expose": should_expose}}
    return {"entity_id": entity_id, "options": options}


class FakeHomeAssistant:
    def __init__(self, states, entries, legacy_exposed=None, related=None, token="token"):
        self.states = states
        self.entries = {item["entity_id"]: item for item in entries}
        self.legacy_exposed = dict(legacy_exposed or {})
        self.related = related or {}
        self.token = token
        self.calls = []
        self.incoming = asyncio.Queue()
        self.outgoing = asyncio.Queue()
        self.authenticated = False
        self.closed = False
        self.outgoing.put_nowait(json.dumps({"type": "auth_required", "ha_version": "2026.11.1"}))

    async def connector(self, url):
        self.url = url
        return self

    async def recv(self):
        message = await self.outgoing.get()
        if message is None:
            raise ConnectionError("closed")
        return message

    async def send(self, raw):
        message = json.loads(raw)
        if not self.authenticated:
            if message.get("access_token") == self.token:
                self.authenticated = True
                self.outgoing.put_nowait(json.dumps({"type": "auth_ok"}))
            else:
                self.outgoing.put_nowait(json.dumps({"type": "auth_invalid", "message": "Invalid access"}))
            return
        self.calls.append(message)
        handler = getattr(self, "_" + message["type"].replace("/", "_"), None)
        if handler is None:
            self._reply(message, error={"code": "unknown_command", "message": message["type"]})
        else:
            self._reply(message, result=handler(message))

    def _reply(self, message, result=None, error=None):
        reply = {"id": message["id"], "type": "result", "success": error is None}
        if error is None:
            reply["result"] = result
        else:
            reply["error"] = error
        self.outgoing.put_nowait(json.dumps(reply))

    async def close(self):
        self.closed = True
        self.outgoing.put_nowait(None)

    def event(self):
        self.outgoing.put_nowait(
            json.dumps({"id": 1, "type": "event", "event": {"event_type": "entity_registry_updated"}})
        )

    def exposed_now(self, entity_id):
        if entity_id in self.entries:
            return self.entries[entity_id]["options"].get("conversation", {}).get("should_expose")
        return self.legacy_exposed.get(entity_id)

    def _subscribe_events(self, message):
        return None

    def _get_states(self, message):
        return self.states

    def _config_entity_registry_list(self, message):
        return list(self.entries.values())

    def _homeassistant_expose_entity_list(self, message):
        result = {}
        for entity_id in self.entries:
            if self.exposed_now(entity_id):
                result[entity_id] = {"conversation": True}
        for entity_id, value in self.legacy_exposed.items():
            if value:
                result[entity_id] = {"conversation": True}
        return {"exposed_entities": result}

    def _homeassistant_expose_entity(self, message):
        changed = []
        for entity_id in message["entity_ids"]:
            if self.exposed_now(entity_id) != message["should_expose"]:
                changed.append(entity_id)
            if entity_id in self.entries:
                self.entries[entity_id]["options"]["conversation"] = {
                    "should_expose": message["should_expose"]
                }
            else:
                self.legacy_exposed[entity_id] = message["should_expose"]
        return {"changed_entity_ids": changed}

    def _search_related(self, message):
        return self.related.get(message["item_id"], {})

    def _call_service(self, message):
        return {"context": {}}


def test_plan_protected_domains_and_members():
    states = [
        state("lock.front_door"),
        state("alarm_control_panel.home"),
        state("light.kitchen"),
        state("scene.leaving", ["light.kitchen", "lock.front_door"]),
        state("scene.evening", ["light.kitchen"]),
        state("group.outer", ["scene.leaving"]),
    ]
    registry = {
        "lock.front_door": entry("lock.front_door", True),
        "alarm_control_panel.home": entry("alarm_control_panel.home", False),
        "light.kitchen": entry("light.kitchen", True),
        "scene.leaving": entry("scene.leaving", None),
        "scene.evening": entry("scene.evening", True),
        "group.outer": entry("group.outer", True),
    }
    result = plan(states, registry, {}, {}, ["lock", "alarm_control_panel"])
    assert set(result) == {"lock.front_door", "scene.leaving", "group.outer"}
    assert "never available" in result["lock.front_door"]
    assert result["scene.leaving"] == "it can control lock.front_door"
    assert result["group.outer"] == "it can control scene.leaving"


def test_plan_script_references_and_legacy_entities():
    states = [
        state("lock.back"),
        state("script.goodnight"),
        state("script.lights"),
        state("scene.yaml_only", ["lock.back"]),
    ]
    registry = {
        "lock.back": entry("lock.back", False),
        "script.goodnight": entry("script.goodnight", True),
        "script.lights": entry("script.lights", True),
    }
    references = {"script.goodnight": {"light.hall", "lock.back"}, "script.lights": {"light.hall"}}
    result = plan(states, registry, {}, references, ["lock"])
    assert set(result) == {"script.goodnight", "scene.yaml_only"}
    assert plan(states, registry, {}, references, ["lock"], {"scene.yaml_only"}).keys() == {
        "script.goodnight"
    }
    assert plan(
        states,
        registry,
        {"scene.yaml_only": {"conversation": True}},
        references,
        ["lock"],
        {"scene.yaml_only"},
    ).keys() == {"script.goodnight", "scene.yaml_only"}


def test_plan_without_protected_domains_changes_nothing():
    states = [state("lock.front_door"), state("scene.leaving", ["lock.front_door"])]
    registry = {"lock.front_door": entry("lock.front_door", True)}
    assert plan(states, registry, {}, {}, []) == {}


async def test_check_unexposes_and_notifies():
    home = FakeHomeAssistant(
        states=[
            state("lock.front_door"),
            state("light.kitchen"),
            state("script.goodnight"),
            state("alarm_control_panel.home"),
            state("scene.leaving", ["lock.front_door"]),
        ],
        entries=[
            entry("lock.front_door", True),
            entry("light.kitchen", True),
            entry("script.goodnight", True),
            entry("alarm_control_panel.home", None),
        ],
        legacy_exposed={"scene.leaving": True},
        related={"script.goodnight": {"entity": ["alarm_control_panel.home", "light.kitchen"]}},
    )
    connection = await Connection.open("ws://test", "token", home.connector)
    guard = Guard("token", connector=home.connector)
    reported = await guard.check(connection)
    assert home.exposed_now("lock.front_door") is False
    assert home.exposed_now("alarm_control_panel.home") is False
    assert home.exposed_now("script.goodnight") is False
    assert home.exposed_now("scene.leaving") is False
    assert home.exposed_now("light.kitchen") is True
    assert set(reported) == {"lock.front_door", "script.goodnight", "scene.leaving"}
    notifications = [call for call in home.calls if call["type"] == "call_service"]
    assert len(notifications) == 1
    assert "lock.front_door" in notifications[0]["service_data"]["message"]
    assert "- `alarm_control_panel.home`" not in notifications[0]["service_data"]["message"]
    assert (
        "- `script.goodnight`: it can control alarm_control_panel.home"
        in notifications[0]["service_data"]["message"]
    )
    expose_calls = [call for call in home.calls if call["type"] == "homeassistant/expose_entity"]
    assert len(expose_calls) == 1 and expose_calls[0]["assistants"] == ["conversation"]
    assert await guard.check(connection) == {}
    assert len([call for call in home.calls if call["type"] == "homeassistant/expose_entity"]) == 1
    await connection.close()


async def test_check_with_nothing_exposed_sends_no_writes():
    home = FakeHomeAssistant(states=[state("light.kitchen")], entries=[entry("light.kitchen", True)])
    connection = await Connection.open("ws://test", "token", home.connector)
    assert await Guard("token").check(connection) == {}
    assert [call["type"] for call in home.calls] == [
        "get_states",
        "config/entity_registry/list",
        "homeassistant/expose_entity/list",
    ]
    await connection.close()


async def test_rejected_token():
    home = FakeHomeAssistant(states=[], entries=[], token="other")
    with pytest.raises(GuardError, match="refused the token"):
        await Connection.open("ws://test", "token", home.connector)
    assert home.closed


async def test_failed_command_raises():
    home = FakeHomeAssistant(states=[], entries=[])
    connection = await Connection.open("ws://test", "token", home.connector)
    with pytest.raises(GuardError, match="unknown_command"):
        await connection.call("no/such/command")
    await connection.close()


async def test_watch_reacts_to_registry_events():
    home = FakeHomeAssistant(states=[state("lock.front_door")], entries=[entry("lock.front_door", False)])
    connection = await Connection.open("ws://test", "token", home.connector)
    guard = Guard("token", interval=30)
    task = asyncio.create_task(guard.watch(connection))
    for _ in range(100):
        if guard.passes == 1:
            break
        await asyncio.sleep(0.01)
    assert guard.passes == 1
    home.entries["lock.front_door"]["options"]["conversation"]["should_expose"] = True
    home.event()
    for _ in range(300):
        if guard.passes == 2:
            break
        await asyncio.sleep(0.01)
    assert guard.passes == 2
    assert home.exposed_now("lock.front_door") is False
    await home.close()
    with pytest.raises(GuardError):
        await asyncio.wait_for(task, 5)
    await connection.close()


async def test_run_retries_until_home_assistant_answers(monkeypatch):
    attempts = []

    async def failing(url):
        attempts.append(url)
        raise OSError("connection refused")

    sleeps = []

    async def fake_sleep(seconds):
        sleeps.append(seconds)
        if len(sleeps) >= 3:
            raise asyncio.CancelledError

    monkeypatch.setattr("voxhub_satellite.guard.asyncio.sleep", fake_sleep)
    with pytest.raises(asyncio.CancelledError):
        await Guard("token", connector=failing).run()
    assert len(attempts) == 3
    assert sleeps == [5.0, 10.0, 20.0]


async def test_disabled_guard_returns_at_once():
    await asyncio.wait_for(Guard("token", protected_domains=[]).run(), 1)
