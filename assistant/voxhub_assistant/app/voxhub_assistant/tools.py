"""Tools Claude can call to observe and control the home."""

from __future__ import annotations

import json
import logging
from typing import Any

from .ha_client import HomeAssistant, HomeAssistantError, PolicyError, ServicePolicy

_LOGGER = logging.getLogger(__name__)

MAX_SEARCH_RESULTS = 40
_MAX_ATTRIBUTES = 25
_MAX_ATTRIBUTE_CHARS = 200


def build_tools(allowed_service_domains: list[str]) -> list[dict[str, Any]]:
    """Tool definitions. Deterministic for a given configuration, so the prompt cache
    prefix (tools + system prompt) stays byte-identical between requests."""
    allowed = ", ".join(sorted(allowed_service_domains)) or "none"
    return [
        {
            "name": "search_entities",
            "description": (
                "Find Home Assistant entities (devices, sensors, scenes...) by name, room or "
                "domain. Returns entity ids with friendly name, area and current state. Call "
                "this first whenever you do not already know the exact entity id."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Words from the name or room, e.g. 'kitchen light'. "
                        "Leave empty to list everything in the domain.",
                    },
                    "domain": {
                        "type": "string",
                        "description": "Optional domain filter, e.g. 'light', 'climate', 'sensor'.",
                    },
                },
            },
        },
        {
            "name": "get_state",
            "description": "Get the current state and attributes of one entity "
            "(brightness, temperature, media title, weather conditions...).",
            "input_schema": {
                "type": "object",
                "properties": {"entity_id": {"type": "string", "description": "e.g. 'light.kitchen'"}},
                "required": ["entity_id"],
            },
        },
        {
            "name": "call_service",
            "description": (
                "Control devices by calling a Home Assistant service, e.g. light.turn_on, "
                "cover.close_cover, climate.set_temperature, scene.turn_on. "
                f"Allowed domains: {allowed}. Other domains are rejected."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Service domain, e.g. 'light'"},
                    "service": {"type": "string", "description": "Service name, e.g. 'turn_on'"},
                    "entity_id": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "One or more target entity ids.",
                    },
                    "data": {
                        "type": "object",
                        "description": 'Extra service data, e.g. {"brightness_pct": 40} '
                        'or {"temperature": 21}.',
                    },
                },
                "required": ["domain", "service", "entity_id"],
            },
        },
        {
            "name": "get_weather_forecast",
            "description": "Get the weather forecast from a Home Assistant weather entity.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Weather entity; omit to use the first one available.",
                    },
                    "type": {"type": "string", "enum": ["daily", "hourly"]},
                },
            },
        },
    ]


class ToolError(Exception):
    """A tool failed; the message is returned to Claude as an error result."""


class HomeTools:
    """Executes tool calls against Home Assistant, enforcing exposure and service policy."""

    def __init__(self, ha: HomeAssistant, policy: ServicePolicy, exposed_domains: list[str]) -> None:
        self.ha = ha
        self.policy = policy
        self.exposed = frozenset(exposed_domains)

    async def execute(self, name: str, arguments: Any) -> str:
        """Run a tool and return its result as a JSON string. Raises ToolError on failure."""
        if not isinstance(arguments, dict):
            raise ToolError("tool input must be a JSON object")
        handler = getattr(self, f"_tool_{name}", None)
        if handler is None:
            raise ToolError(f"unknown tool '{name}'")
        try:
            result = await handler(arguments)
        except (PolicyError, HomeAssistantError) as err:
            raise ToolError(str(err)) from err
        return json.dumps(result, ensure_ascii=False, default=str)

    def _is_exposed(self, entity_id: str) -> bool:
        return entity_id.split(".", 1)[0] in self.exposed

    async def _tool_search_entities(self, args: dict[str, Any]) -> dict[str, Any]:
        words = str(args.get("query") or "").lower().split()
        domain = str(args.get("domain") or "").lower().strip()
        areas = await self.ha.get_areas()
        rows: list[tuple[int, dict[str, Any]]] = []
        for state in await self.ha.get_states():
            entity_id = state.get("entity_id", "")
            if not self._is_exposed(entity_id) or (domain and not entity_id.startswith(domain + ".")):
                continue
            row = _summary(state, areas.get(entity_id, ""))
            haystack = f"{entity_id} {row['name']} {row.get('area', '')}".lower().replace("_", " ")
            hits = sum(word in haystack for word in words)
            if not words or hits:
                rows.append((hits, row))
        if words and any(hits == len(words) for hits, _ in rows):
            rows = [item for item in rows if item[0] == len(words)]  # prefer full matches
        rows.sort(key=lambda item: (-item[0], item[1]["entity_id"]))
        entities = [row for _, row in rows[:MAX_SEARCH_RESULTS]]
        result: dict[str, Any] = {"entities": entities}
        if len(rows) > MAX_SEARCH_RESULTS:
            result["note"] = f"{len(rows)} matches; showing {MAX_SEARCH_RESULTS}. Narrow the search."
        return result

    async def _tool_get_state(self, args: dict[str, Any]) -> dict[str, Any]:
        entity_id = str(args.get("entity_id") or "").strip().lower()
        if not self._is_exposed(entity_id):
            raise ToolError(f"entity '{entity_id}' is not exposed to the assistant")
        state = await self.ha.get_state(entity_id)
        attributes = {
            key: value
            for key, value in list(state.get("attributes", {}).items())[:_MAX_ATTRIBUTES]
            if len(str(value)) <= _MAX_ATTRIBUTE_CHARS
        }
        return {
            "entity_id": entity_id,
            "state": state.get("state"),
            "attributes": attributes,
            "last_changed": state.get("last_changed"),
        }

    async def _tool_call_service(self, args: dict[str, Any]) -> dict[str, Any]:
        domain = str(args.get("domain") or "").strip().lower()
        service = str(args.get("service") or "").strip().lower()
        targets = args.get("entity_id") or []
        if isinstance(targets, str):
            targets = [targets]
        if not isinstance(targets, list):
            raise ToolError("entity_id must be a list of entity ids")
        entity_ids = [str(t).strip().lower() for t in targets]
        data = args.get("data") or {}
        if not isinstance(data, dict):
            raise ToolError("data must be an object")
        self.policy.check(domain, service, entity_ids)
        # Targets come only from the validated list, never from free-form data.
        payload = {k: v for k, v in data.items() if k not in ("entity_id", "area_id", "device_id")}
        payload["entity_id"] = entity_ids
        _LOGGER.info("Calling service %s.%s on %s", domain, service, entity_ids)
        await self.ha.call_service(domain, service, payload)
        return {"success": True, "called": f"{domain}.{service}", "entity_id": entity_ids}

    async def _tool_get_weather_forecast(self, args: dict[str, Any]) -> dict[str, Any]:
        if "weather" not in self.exposed:
            raise ToolError("weather entities are not exposed to the assistant")
        entity_id = str(args.get("entity_id") or "").strip().lower()
        if not entity_id:
            weather = [s["entity_id"] for s in await self.ha.get_states()
                       if s.get("entity_id", "").startswith("weather.")]  # fmt: skip
            if not weather:
                raise ToolError("no weather entity is configured in Home Assistant")
            entity_id = sorted(weather)[0]
        if not entity_id.startswith("weather."):
            raise ToolError(f"'{entity_id}' is not a weather entity")
        kind = args.get("type") if args.get("type") in ("daily", "hourly") else "daily"
        response = await self.ha.call_service(
            "weather", "get_forecasts", {"entity_id": entity_id, "type": kind}, return_response=True
        )
        forecasts = (response or {}).get("service_response", {}).get(entity_id, {}).get("forecast", [])
        return {"entity_id": entity_id, "type": kind, "forecast": forecasts[: 8 if kind == "daily" else 12]}


def _summary(state: dict[str, Any], area: str) -> dict[str, Any]:
    attributes = state.get("attributes", {})
    row: dict[str, Any] = {
        "entity_id": state.get("entity_id", ""),
        "name": attributes.get("friendly_name") or state.get("entity_id", ""),
        "state": state.get("state"),
    }
    if unit := attributes.get("unit_of_measurement"):
        row["unit"] = unit
    if area:
        row["area"] = area
    return row
