"""Data update coordinator for Free Sleep."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import FreeSleepApiClient, FreeSleepApiError
from .const import (
    DOMAIN,
    UPDATE_INTERVAL_BASE_CONTROL,
    UPDATE_INTERVAL_DEVICE_STATUS,
    UPDATE_INTERVAL_VITALS,
)

_LOGGER = logging.getLogger(__name__)


class FreeSleepDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Free Sleep data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: FreeSleepApiClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_DEVICE_STATUS),
        )
        self.api = api
        self._vitals_counter = 0
        self._base_counter = 0
        self._settings_loaded = False
        self._schedules_loaded = False

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Always fetch device status (5 second interval)
            device_status = await self.api.async_get_device_status()

            data = {
                "device_status": device_status,
            }

            # Fetch settings on first load only (or when explicitly refreshed)
            if not self._settings_loaded:
                try:
                    settings = await self.api.async_get_settings()
                    data["settings"] = settings
                    self._settings_loaded = True
                except FreeSleepApiError as err:
                    _LOGGER.debug("Could not fetch settings: %s", err)

            # Fetch schedules on first load only (or when explicitly refreshed)
            if not self._schedules_loaded:
                try:
                    schedules = await self.api.async_get_schedules()
                    data["schedules"] = schedules
                    self._schedules_loaded = True
                except FreeSleepApiError as err:
                    _LOGGER.debug("Could not fetch schedules: %s", err)

            # Fetch base control every 10 seconds (every 2nd update)
            self._base_counter += 1
            if self._base_counter >= (UPDATE_INTERVAL_BASE_CONTROL / UPDATE_INTERVAL_DEVICE_STATUS):
                self._base_counter = 0
                try:
                    base_control = await self.api.async_get_base_control()
                    data["base_control"] = base_control
                except FreeSleepApiError as err:
                    _LOGGER.debug("Could not fetch base control (may not be configured): %s", err)

            # Fetch vitals summary every 60 seconds (every 12th update)
            self._vitals_counter += 1
            if self._vitals_counter >= (UPDATE_INTERVAL_VITALS / UPDATE_INTERVAL_DEVICE_STATUS):
                self._vitals_counter = 0
                try:
                    # Try to fetch vitals for both sides
                    vitals_left = await self.api.async_get_vitals_summary(side="left")
                    vitals_right = await self.api.async_get_vitals_summary(side="right")
                    data["vitals"] = {
                        "left": vitals_left,
                        "right": vitals_right,
                    }
                except FreeSleepApiError as err:
                    _LOGGER.debug("Could not fetch vitals (may not be enabled): %s", err)

            return data

        except FreeSleepApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def async_refresh_settings(self) -> None:
        """Force refresh settings on next update."""
        self._settings_loaded = False
        await self.async_request_refresh()

    async def async_refresh_schedules(self) -> None:
        """Force refresh schedules on next update."""
        self._schedules_loaded = False
        await self.async_request_refresh()

