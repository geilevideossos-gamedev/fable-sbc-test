import json

import pytest

from voxhub_assistant.ha_client import HomeAssistant, HomeAssistantError, PolicyError, ServicePolicy
from voxhub_assistant.tools import ToolError, build_tools

POLICY = ServicePolicy.from_lists(["light", "switch", "cover", "scene"], ["lock", "alarm_control_panel"])


def test_allowed_call_passes():
    POLICY.check("light", "turn_on", ["light.kitchen", "light.hall"])


@pytest.mark.parametrize(
    ("domain", "service", "entities"),
    [
        ("lock", "unlock", ["lock.front_door"]),  # denied domain
        ("alarm_control_panel", "alarm_disarm", ["alarm_control_panel.home"]),
        ("camera", "turn_on", ["camera.porch"]),  # not on the allow-list
        ("homeassistant", "turn_off", ["light.kitchen"]),  # generic domain not allowed
        ("light", "turn_on", ["lock.front_door"]),  # allowed service, denied target
        ("light", "turn_on", ["light.kitchen", "camera.porch"]),  # one bad target
        ("light", "turn_off", []),  # no target = "everything"
        ("light", "turn_on", ["all"]),  # not an entity id
        ("light/../../config", "x", ["light.kitchen"]),  # path injection
        ("light", "turn_on?x=1", ["light.kitchen"]),
    ],
)
def test_rejected_calls(domain, service, entities):
    with pytest.raises(PolicyError):
        POLICY.check(domain, service, entities)


def test_deny_list_wins_over_allow_list():
    policy = ServicePolicy.from_lists(["lock", "light"], ["lock"])
    with pytest.raises(PolicyError, match="deny-list"):
        policy.check("lock", "unlock", ["lock.front_door"])
    with pytest.raises(PolicyError, match="deny-list"):
        policy.check("light", "turn_on", ["lock.front_door"])


async def test_call_service_tool_executes_allowed_call(tools, ha):
    result = json.loads(
        await tools.execute(
            "call_service",
            {
                "domain": "light",
                "service": "turn_on",
                "entity_id": ["light.kitchen"],
                "data": {"brightness_pct": 40, "entity_id": "lock.front_door", "area_id": "all"},
            },
        )  # fmt: skip
    )
    assert result["success"] is True
    # Targets smuggled through `data` are dropped; only validated entity ids are sent.
    assert ha.calls == [("light", "turn_on", {"brightness_pct": 40, "entity_id": ["light.kitchen"]})]


async def test_call_service_tool_accepts_single_string_target(tools, ha):
    await tools.execute("call_service", {"domain": "switch", "service": "toggle", "entity_id": "Switch.Fan"})
    assert ha.calls[0][2] == {"entity_id": ["switch.fan"]}


async def test_call_service_tool_blocks_lock_by_default(tools, ha):
    with pytest.raises(ToolError, match="deny-list"):
        await tools.execute(
            "call_service", {"domain": "lock", "service": "unlock", "entity_id": ["lock.front_door"]}
        )
    assert ha.calls == []


async def test_search_entities(tools):
    result = json.loads(await tools.execute("search_entities", {"query": "kitchen light"}))
    assert [e["entity_id"] for e in result["entities"]] == ["light.kitchen"]
    assert result["entities"][0]["area"] == "Kitchen"

    result = json.loads(await tools.execute("search_entities", {"query": "kitchen"}))
    assert {e["entity_id"] for e in result["entities"]} == {"light.kitchen", "sensor.kitchen_temperature"}

    result = json.loads(await tools.execute("search_entities", {"domain": "light"}))
    assert len(result["entities"]) == 2

    # camera is not an exposed domain
    result = json.loads(await tools.execute("search_entities", {"query": "porch"}))
    assert result["entities"] == []


async def test_get_state_and_exposure(tools):
    result = json.loads(await tools.execute("get_state", {"entity_id": "sensor.kitchen_temperature"}))
    assert result["state"] == "21.5"
    assert result["attributes"]["unit_of_measurement"] == "°C"
    with pytest.raises(ToolError, match="not exposed"):
        await tools.execute("get_state", {"entity_id": "camera.porch"})
    with pytest.raises(ToolError, match="not found"):
        await tools.execute("get_state", {"entity_id": "light.nope"})


async def test_weather_forecast(tools, ha):
    result = json.loads(await tools.execute("get_weather_forecast", {}))
    assert result["entity_id"] == "weather.home"
    assert len(result["forecast"]) == 8
    assert ha.calls == [("weather", "get_forecasts", {"entity_id": "weather.home", "type": "daily"})]


async def test_unknown_tool_and_bad_input(tools):
    with pytest.raises(ToolError):
        await tools.execute("format_disk", {})
    with pytest.raises(ToolError):
        await tools.execute("get_state", "light.kitchen")


def test_tool_definitions_are_deterministic():
    first = json.dumps(build_tools(["switch", "light"]))
    assert first == json.dumps(build_tools(["light", "switch"]))
    names = [tool["name"] for tool in build_tools(["light"])]
    assert names == ["search_entities", "get_state", "call_service", "get_weather_forecast"]


async def test_client_rejects_bad_names_without_network():
    ha = HomeAssistant(base_url="http://invalid.invalid", token="t")
    with pytest.raises(HomeAssistantError):
        await ha.call_service("light/..", "turn_on", {})
    with pytest.raises(HomeAssistantError):
        await ha.get_state("../config")
