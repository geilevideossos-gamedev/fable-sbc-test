"""Home Assistant Core REST API client (through the Supervisor proxy) and service policy."""

from __future__ import annotations

import logging
import os
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

SUPERVISOR_CORE_API = "http://supervisor/core/api"
_SLUG = re.compile(r"^[a-z0-9_]+$")
_ENTITY_ID = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
_AREA_TEMPLATE = "{% for s in states %}{{ s.entity_id }}|{{ area_name(s.entity_id) or '' }}\n{% endfor %}"


class HomeAssistantError(RuntimeError):
    """The Home Assistant API returned an error or is unreachable."""


class PolicyError(PermissionError):
    """A service call was rejected by the add-on's allow/deny lists."""


@dataclass(frozen=True)
class ServicePolicy:
    """Which service calls Claude may make. The deny-list always wins."""

    allowed: frozenset[str]
    denied: frozenset[str]

    @classmethod
    def from_lists(cls, allowed: Iterable[str], denied: Iterable[str]) -> ServicePolicy:
        return cls(frozenset(allowed), frozenset(denied))

    def check(self, domain: str, service: str, entity_ids: list[str]) -> None:
        """Raise PolicyError unless ``domain.service`` on ``entity_ids`` is permitted."""
        if not _SLUG.match(domain) or not _SLUG.match(service):
            raise PolicyError(f"'{domain}.{service}' is not a valid service name")
        self._check_domain(domain, f"service domain '{domain}'")
        if not entity_ids:
            raise PolicyError("entity_id is required; calls without a target are not allowed")
        for entity_id in entity_ids:
            if not _ENTITY_ID.match(entity_id):
                raise PolicyError(f"'{entity_id}' is not a valid entity id")
            self._check_domain(entity_id.split(".", 1)[0], f"entity '{entity_id}'")

    def _check_domain(self, domain: str, what: str) -> None:
        if domain in self.denied:
            raise PolicyError(f"{what} is blocked by the add-on configuration (deny-list)")
        if domain not in self.allowed:
            raise PolicyError(f"{what} is not in the add-on's list of allowed domains")


class HomeAssistant:
    """Minimal async client for the endpoints the assistant needs."""

    def __init__(
        self,
        base_url: str = SUPERVISOR_CORE_API,
        token: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token if token is not None else os.environ.get("SUPERVISOR_TOKEN", "")
        self._session = session
        self._areas: dict[str, str] = {}
        self._areas_at = 0.0

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with self._session.request(
                method, f"{self._base_url}{path}", headers=headers, **kwargs
            ) as response:
                if response.status == 404:
                    raise HomeAssistantError("not found")
                if response.status >= 400:
                    body = (await response.text())[:200]
                    raise HomeAssistantError(f"Home Assistant returned HTTP {response.status}: {body}")
                if "json" in response.headers.get("Content-Type", ""):
                    return await response.json()
                return await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise HomeAssistantError(f"Home Assistant is unreachable: {err!r}") from err

    async def get_config(self) -> dict[str, Any]:
        return await self._request("GET", "/config")

    async def get_states(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/states")

    async def get_state(self, entity_id: str) -> dict[str, Any]:
        if not _ENTITY_ID.match(entity_id):
            raise HomeAssistantError(f"'{entity_id}' is not a valid entity id")
        return await self._request("GET", f"/states/{entity_id}")

    async def call_service(
        self, domain: str, service: str, data: dict[str, Any], return_response: bool = False
    ) -> Any:
        if not _SLUG.match(domain) or not _SLUG.match(service):
            raise HomeAssistantError(f"'{domain}.{service}' is not a valid service name")
        params = {"return_response": ""} if return_response else None
        return await self._request("POST", f"/services/{domain}/{service}", json=data, params=params)

    async def get_areas(self, max_age: float = 300.0) -> dict[str, str]:
        """Map entity_id -> area name (via the template API). Empty when unavailable."""
        if self._areas and time.monotonic() - self._areas_at < max_age:
            return self._areas
        try:
            text = await self._request("POST", "/template", json={"template": _AREA_TEMPLATE})
        except HomeAssistantError as err:
            _LOGGER.debug("Area lookup failed: %s", err)
            return self._areas
        areas = {}
        for line in str(text).splitlines():
            entity_id, _, area = line.strip().partition("|")
            if entity_id and area:
                areas[entity_id] = area
        self._areas, self._areas_at = areas, time.monotonic()
        return areas
