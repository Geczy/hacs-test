"""API client for Free Sleep."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.exceptions import HomeAssistantError

from .const import (
    ENDPOINT_BASE_CONTROL,
    ENDPOINT_BASE_CONTROL_PRESET,
    ENDPOINT_DEVICE_STATUS,
    ENDPOINT_DISMISS_PRIME,
    ENDPOINT_SCHEDULES,
    ENDPOINT_SETTINGS,
    ENDPOINT_SNOOZE,
    ENDPOINT_VERSION,
    ENDPOINT_VITALS_SUMMARY,
)

_LOGGER = logging.getLogger(__name__)

API_TIMEOUT = 10


class FreeSleepApiError(HomeAssistantError):
    """Exception to indicate API error."""


class FreeSleepApiClient:
    """Free Sleep API Client."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._host = host.rstrip("/")
        self._session = session

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make a request to the API."""
        url = f"{self._host}{endpoint}"

        try:
            async with async_timeout.timeout(API_TIMEOUT):
                if method == "GET":
                    async with self._session.get(url) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method == "POST":
                    async with self._session.post(url, json=data) as response:
                        response.raise_for_status()
                        # POST endpoints may return 204 No Content
                        if response.status == 204:
                            return None
                        return await response.json()
        except asyncio.TimeoutError as err:
            raise FreeSleepApiError(f"Timeout connecting to {url}") from err
        except aiohttp.ClientError as err:
            raise FreeSleepApiError(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise FreeSleepApiError(f"Unexpected error: {err}") from err

    async def async_get_device_status(self) -> dict[str, Any]:
        """Get device status."""
        return await self._request("GET", ENDPOINT_DEVICE_STATUS)

    async def async_update_device_status(
        self, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update device status."""
        return await self._request("POST", ENDPOINT_DEVICE_STATUS, data)

    async def async_get_settings(self) -> dict[str, Any]:
        """Get settings."""
        return await self._request("GET", ENDPOINT_SETTINGS)

    async def async_update_settings(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update settings."""
        return await self._request("POST", ENDPOINT_SETTINGS, data)

    async def async_get_schedules(self) -> dict[str, Any]:
        """Get schedules."""
        return await self._request("GET", ENDPOINT_SCHEDULES)

    async def async_update_schedules(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update schedules."""
        return await self._request("POST", ENDPOINT_SCHEDULES, data)

    async def async_get_vitals_summary(
        self,
        side: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        """Get vitals summary."""
        params = []
        if side:
            params.append(f"side={side}")
        if start_time:
            params.append(f"startTime={start_time}")
        if end_time:
            params.append(f"endTime={end_time}")

        endpoint = ENDPOINT_VITALS_SUMMARY
        if params:
            endpoint += f"?{'&'.join(params)}"

        return await self._request("GET", endpoint)

    async def async_get_base_control(self) -> dict[str, Any]:
        """Get base control status."""
        return await self._request("GET", ENDPOINT_BASE_CONTROL)

    async def async_set_base_position(
        self, head: int, feet: int, feed_rate: int = 50
    ) -> dict[str, Any]:
        """Set base position."""
        data = {"head": head, "feet": feet, "feedRate": feed_rate}
        return await self._request("POST", ENDPOINT_BASE_CONTROL, data)

    async def async_set_base_preset(self, preset: str) -> dict[str, Any]:
        """Set base preset."""
        data = {"preset": preset}
        return await self._request("POST", ENDPOINT_BASE_CONTROL_PRESET, data)

    async def async_snooze_alarm(self, side: str) -> None:
        """Snooze alarm."""
        data = {"side": side}
        await self._request("POST", ENDPOINT_SNOOZE, data)

    async def async_dismiss_prime_notification(self) -> None:
        """Dismiss prime notification."""
        await self._request("POST", ENDPOINT_DISMISS_PRIME)

    async def async_get_version(self) -> dict[str, Any]:
        """Get version information."""
        return await self._request("GET", ENDPOINT_VERSION)

    async def async_prime_pod(self) -> None:
        """Prime the pod."""
        data = {"isPriming": True}
        await self._request("POST", ENDPOINT_DEVICE_STATUS, data)

