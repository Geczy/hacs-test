"""Switch platform for Free Sleep."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, SIDE_LEFT, SIDE_RIGHT
from .coordinator import FreeSleepDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Free Sleep switch entities."""
    coordinator: FreeSleepDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        FreeSleepPowerSwitch(coordinator, entry, SIDE_LEFT),
        FreeSleepPowerSwitch(coordinator, entry, SIDE_RIGHT),
        FreeSleepLinkSidesSwitch(coordinator, entry),
    ]

    async_add_entities(entities)


class FreeSleepPowerSwitch(CoordinatorEntity[FreeSleepDataUpdateCoordinator], SwitchEntity):
    """Representation of a Free Sleep power switch."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:power"

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
        side: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._side = side
        self._attr_unique_id = f"{entry.entry_id}_{side}_power"
        self._attr_name = f"Power {side}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 3/4",
            "configuration_url": entry.data.get("host"),
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        if device_status := self.coordinator.data.get("device_status"):
            if side_data := device_status.get(self._side):
                return side_data.get("isOn", False)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.api.async_update_device_status({
            self._side: {"isOn": True}
        })
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.api.async_update_device_status({
            self._side: {"isOn": False}
        })
        await self.coordinator.async_request_refresh()


class FreeSleepLinkSidesSwitch(CoordinatorEntity[FreeSleepDataUpdateCoordinator], SwitchEntity):
    """Representation of a Free Sleep link sides switch."""

    _attr_has_entity_name = True
    _attr_name = "Link both sides"
    _attr_icon = "mdi:link"

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_link_sides"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 3/4",
            "configuration_url": entry.data.get("host"),
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        if settings := self.coordinator.data.get("settings"):
            return settings.get("linkBothSides", False)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.api.async_update_settings({
            "linkBothSides": True
        })
        await self.coordinator.async_refresh_settings()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.api.async_update_settings({
            "linkBothSides": False
        })
        await self.coordinator.async_refresh_settings()

