"""Shared fakes: no hardware, network or API key is needed to run the suite."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from voxhub_assistant.config import Config
from voxhub_assistant.ha_client import HomeAssistantError, ServicePolicy
from voxhub_assistant.tools import HomeTools

STATES = [
    {"entity_id": "light.kitchen", "state": "off",
     "attributes": {"friendly_name": "Kitchen Light"}},
    {"entity_id": "light.living_room_lamp", "state": "on",
     "attributes": {"friendly_name": "Living Room Lamp", "brightness": 128}},
    {"entity_id": "sensor.kitchen_temperature", "state": "21.5",
     "attributes": {"friendly_name": "Kitchen Temperature", "unit_of_measurement": "°C"}},
    {"entity_id": "lock.front_door", "state": "locked",
     "attributes": {"friendly_name": "Front Door"}},
    {"entity_id": "weather.home", "state": "sunny", "attributes": {"friendly_name": "Home"}},
    {"entity_id": "camera.porch", "state": "idle", "attributes": {"friendly_name": "Porch"}},
]  # fmt: skip


class FakeHA:
    """Stands in for HomeAssistant; records service calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def get_states(self) -> list[dict[str, Any]]:
        return STATES

    async def get_state(self, entity_id: str) -> dict[str, Any]:
        for state in STATES:
            if state["entity_id"] == entity_id:
                return state
        raise HomeAssistantError("not found")

    async def get_areas(self) -> dict[str, str]:
        return {"light.kitchen": "Kitchen", "sensor.kitchen_temperature": "Kitchen"}

    async def call_service(self, domain, service, data, return_response=False):
        self.calls.append((domain, service, data))
        if return_response:
            return {"service_response": {data["entity_id"]: {"forecast": [{"temperature": 20}] * 20}}}
        return []


def text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def tool_use_block(tool_id: str, name: str, tool_input: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input=tool_input)


def thinking_block() -> SimpleNamespace:
    return SimpleNamespace(type="thinking", thinking="", signature="sig")


def message(content: list[Any], stop_reason: str = "end_turn") -> SimpleNamespace:
    usage = SimpleNamespace(input_tokens=10, output_tokens=5, cache_read_input_tokens=0)
    return SimpleNamespace(content=content, stop_reason=stop_reason, usage=usage)


class _FakeStream:
    def __init__(self, response: Any) -> None:
        self._response = response

    async def __aenter__(self) -> _FakeStream:
        if isinstance(self._response, Exception):
            raise self._response
        return self

    async def __aexit__(self, *exc: Any) -> bool:
        return False

    @property
    async def text_stream(self):
        for block in self._response.content:
            if block.type == "text":
                # Split into small deltas, like the real stream does.
                for i in range(0, len(block.text), 7):
                    yield block.text[i : i + 7]

    async def get_final_message(self) -> Any:
        return self._response


class FakeAnthropic:
    """Mimics ``AsyncAnthropic().messages.stream(...)`` with scripted responses."""

    def __init__(self, responses: list[Any]) -> None:
        self._responses = list(responses)
        self.requests: list[dict[str, Any]] = []
        self.messages = self

    def stream(self, **kwargs: Any) -> _FakeStream:
        # Snapshot: the agent keeps appending to the same messages list.
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return _FakeStream(self._responses.pop(0))


@pytest.fixture
def config() -> Config:
    return Config.from_options({"anthropic_api_key": "sk-ant-test-not-real"})


@pytest.fixture
def ha() -> FakeHA:
    return FakeHA()


@pytest.fixture
def tools(ha: FakeHA, config: Config) -> HomeTools:
    policy = ServicePolicy.from_lists(config.allowed_service_domains, config.denied_service_domains)
    return HomeTools(ha, policy, config.exposed_domains)  # type: ignore[arg-type]
