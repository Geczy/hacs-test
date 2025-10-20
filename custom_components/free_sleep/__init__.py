"""The Free Sleep integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FreeSleepApiClient
from .const import (
    BASE_PRESETS,
    DOMAIN,
    SERVICE_DISABLE_AWAY_MODE,
    SERVICE_ENABLE_AWAY_MODE,
    SERVICE_PRIME_POD,
    SERVICE_SET_ALARM,
    SERVICE_SET_BASE_POSITION,
    SERVICE_SET_BASE_PRESET,
    SERVICE_SET_SCHEDULE,
    SIDE_LEFT,
    SIDE_RIGHT,
)
from .coordinator import FreeSleepDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.COVER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Free Sleep from a config entry."""
    host = entry.data[CONF_HOST]

    session = async_get_clientsession(hass)
    api = FreeSleepApiClient(host, session)
    coordinator = FreeSleepDataUpdateCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_set_schedule(call: ServiceCall) -> None:
        """Handle set schedule service."""
        side = call.data.get("side")
        day = call.data.get("day")
        schedule = call.data.get("schedule")

        await api.async_update_schedules({
            side: {
                day: schedule
            }
        })
        await coordinator.async_refresh_schedules()

    async def handle_set_alarm(call: ServiceCall) -> None:
        """Handle set alarm service."""
        side = call.data.get("side")
        day = call.data.get("day")
        alarm = call.data.get("alarm")

        await api.async_update_schedules({
            side: {
                day: {
                    "alarm": alarm
                }
            }
        })
        await coordinator.async_refresh_schedules()

    async def handle_set_base_position(call: ServiceCall) -> None:
        """Handle set base position service."""
        head = call.data.get("head")
        feet = call.data.get("feet")
        feed_rate = call.data.get("feed_rate", 50)

        await api.async_set_base_position(head, feet, feed_rate)
        await coordinator.async_request_refresh()

    async def handle_set_base_preset(call: ServiceCall) -> None:
        """Handle set base preset service."""
        preset = call.data.get("preset")

        await api.async_set_base_preset(preset)
        await coordinator.async_request_refresh()

    async def handle_enable_away_mode(call: ServiceCall) -> None:
        """Handle enable away mode service."""
        side = call.data.get("side")
        away_start = call.data.get("away_start")
        away_return = call.data.get("away_return")

        await api.async_update_settings({
            side: {
                "awayMode": True,
                "awayStart": away_start,
                "awayReturn": away_return,
            }
        })
        await coordinator.async_refresh_settings()

    async def handle_disable_away_mode(call: ServiceCall) -> None:
        """Handle disable away mode service."""
        side = call.data.get("side")

        await api.async_update_settings({
            side: {
                "awayMode": False,
                "awayStart": None,
                "awayReturn": None,
            }
        })
        await coordinator.async_refresh_settings()

    async def handle_prime_pod(call: ServiceCall) -> None:
        """Handle prime pod service."""
        await api.async_prime_pod()
        await coordinator.async_request_refresh()

    # Register services only once for the first config entry
    if not hass.services.has_service(DOMAIN, SERVICE_SET_SCHEDULE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_SCHEDULE,
            handle_set_schedule,
            schema=vol.Schema({
                vol.Required("side"): vol.In([SIDE_LEFT, SIDE_RIGHT]),
                vol.Required("day"): vol.In([
                    "monday", "tuesday", "wednesday", "thursday",
                    "friday", "saturday", "sunday"
                ]),
                vol.Required("schedule"): dict,
            }),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_ALARM):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_ALARM,
            handle_set_alarm,
            schema=vol.Schema({
                vol.Required("side"): vol.In([SIDE_LEFT, SIDE_RIGHT]),
                vol.Required("day"): vol.In([
                    "monday", "tuesday", "wednesday", "thursday",
                    "friday", "saturday", "sunday"
                ]),
                vol.Required("alarm"): dict,
            }),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_BASE_POSITION):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_BASE_POSITION,
            handle_set_base_position,
            schema=vol.Schema({
                vol.Required("head"): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
                vol.Required("feet"): vol.All(vol.Coerce(int), vol.Range(min=0, max=45)),
                vol.Optional("feed_rate", default=50): vol.All(
                    vol.Coerce(int), vol.Range(min=30, max=100)
                ),
            }),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_BASE_PRESET):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_BASE_PRESET,
            handle_set_base_preset,
            schema=vol.Schema({
                vol.Required("preset"): vol.In(list(BASE_PRESETS.keys())),
            }),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_ENABLE_AWAY_MODE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_ENABLE_AWAY_MODE,
            handle_enable_away_mode,
            schema=vol.Schema({
                vol.Required("side"): vol.In([SIDE_LEFT, SIDE_RIGHT]),
                vol.Optional("away_start"): cv.datetime,
                vol.Optional("away_return"): cv.datetime,
            }),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_DISABLE_AWAY_MODE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_DISABLE_AWAY_MODE,
            handle_disable_away_mode,
            schema=vol.Schema({
                vol.Required("side"): vol.In([SIDE_LEFT, SIDE_RIGHT]),
            }),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_PRIME_POD):
        hass.services.async_register(
            DOMAIN,
            SERVICE_PRIME_POD,
            handle_prime_pod,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

