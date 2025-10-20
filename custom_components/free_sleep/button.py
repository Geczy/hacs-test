"""Button platform for Free Sleep."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
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
    """Set up Free Sleep button entities."""
    coordinator: FreeSleepDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[ButtonEntity] = [
        FreeSleepPrimeButton(coordinator, entry),
        FreeSleepSnoozeButton(coordinator, entry, SIDE_LEFT),
        FreeSleepSnoozeButton(coordinator, entry, SIDE_RIGHT),
        FreeSleepDismissAlarmButton(coordinator, entry, SIDE_LEFT),
        FreeSleepDismissAlarmButton(coordinator, entry, SIDE_RIGHT),
    ]

    # Add base stop button if base is available
    if coordinator.data.get("base_control"):
        entities.append(FreeSleepStopBaseButton(coordinator, entry))

    async_add_entities(entities)


class FreeSleepPrimeButton(CoordinatorEntity[FreeSleepDataUpdateCoordinator], ButtonEntity):
    """Representation of a prime pod button."""

    _attr_has_entity_name = True
    _attr_name = "Prime pod"
    _attr_icon = "mdi:water-pump"

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_prime"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 3/4",
            "configuration_url": entry.data.get("host"),
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.api.async_prime_pod()
        await self.coordinator.async_request_refresh()


class FreeSleepSnoozeButton(CoordinatorEntity[FreeSleepDataUpdateCoordinator], ButtonEntity):
    """Representation of a snooze alarm button."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:alarm-snooze"

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
        side: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._side = side
        self._attr_unique_id = f"{entry.entry_id}_snooze_{side}"
        self._attr_name = f"Snooze alarm {side}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 3/4",
            "configuration_url": entry.data.get("host"),
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.api.async_snooze_alarm(self._side)
        await self.coordinator.async_request_refresh()


class FreeSleepDismissAlarmButton(CoordinatorEntity[FreeSleepDataUpdateCoordinator], ButtonEntity):
    """Representation of a dismiss alarm button."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:alarm-off"

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
        side: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._side = side
        self._attr_unique_id = f"{entry.entry_id}_dismiss_alarm_{side}"
        self._attr_name = f"Dismiss alarm {side}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 3/4",
            "configuration_url": entry.data.get("host"),
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        # Dismiss is essentially snoozing with snooze=False parameter
        # but the API snooze endpoint handles this via side parameter only
        await self.coordinator.api.async_snooze_alarm(self._side)
        await self.coordinator.async_request_refresh()


class FreeSleepStopBaseButton(CoordinatorEntity[FreeSleepDataUpdateCoordinator], ButtonEntity):
    """Representation of a stop base movement button."""

    _attr_has_entity_name = True
    _attr_name = "Stop base movement"
    _attr_icon = "mdi:stop"

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_stop_base"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 4 with Adjustable Base",
            "configuration_url": entry.data.get("host"),
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        # Stop by setting to current position
        if base_control := self.coordinator.data.get("base_control"):
            head = base_control.get("head", 0)
            feet = base_control.get("feet", 0)
            await self.coordinator.api.async_set_base_position(head, feet)
            await self.coordinator.async_request_refresh()

