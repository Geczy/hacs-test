"""Number platform for Free Sleep."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BASE_FEED_RATE_DEFAULT,
    BASE_FEED_RATE_MAX,
    BASE_FEED_RATE_MIN,
    BASE_FEET_MAX,
    BASE_FEET_MIN,
    BASE_HEAD_MAX,
    BASE_HEAD_MIN,
    DOMAIN,
    LED_BRIGHTNESS_MAX,
    LED_BRIGHTNESS_MIN,
    MANUFACTURER,
    MAX_TEMPERATURE_F,
    MIN_TEMPERATURE_F,
    SIDE_LEFT,
    SIDE_RIGHT,
)
from .coordinator import FreeSleepDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Free Sleep number entities."""
    coordinator: FreeSleepDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[NumberEntity] = [
        FreeSleepLEDBrightnessNumber(coordinator, entry),
        FreeSleepTemperatureNumber(coordinator, entry, SIDE_LEFT),
        FreeSleepTemperatureNumber(coordinator, entry, SIDE_RIGHT),
    ]

    # Add base control numbers if base is available
    if coordinator.data.get("base_control"):
        entities.extend([
            FreeSleepBaseHeadNumber(coordinator, entry),
            FreeSleepBaseFeetNumber(coordinator, entry),
            FreeSleepBaseFeedRateNumber(coordinator, entry),
        ])

    async_add_entities(entities)


class FreeSleepLEDBrightnessNumber(CoordinatorEntity[FreeSleepDataUpdateCoordinator], NumberEntity):
    """Representation of LED brightness number."""

    _attr_has_entity_name = True
    _attr_name = "LED brightness"
    _attr_icon = "mdi:lightbulb"
    _attr_native_min_value = LED_BRIGHTNESS_MIN
    _attr_native_max_value = LED_BRIGHTNESS_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_led_brightness"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 3/4",
            "configuration_url": entry.data.get("host"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if device_status := self.coordinator.data.get("device_status"):
            if settings := device_status.get("settings"):
                return settings.get("ledBrightness")
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.coordinator.api.async_update_device_status({
            "settings": {
                "ledBrightness": int(value)
            }
        })
        await self.coordinator.async_request_refresh()


class FreeSleepTemperatureNumber(CoordinatorEntity[FreeSleepDataUpdateCoordinator], NumberEntity):
    """Representation of temperature number."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_native_min_value = MIN_TEMPERATURE_F
    _attr_native_max_value = MAX_TEMPERATURE_F
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
        side: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._side = side
        self._attr_unique_id = f"{entry.entry_id}_{side}_temperature"
        self._attr_name = f"Target temperature {side}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 3/4",
            "configuration_url": entry.data.get("host"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if device_status := self.coordinator.data.get("device_status"):
            if side_data := device_status.get(self._side):
                return side_data.get("targetTemperatureF")
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.coordinator.api.async_update_device_status({
            self._side: {
                "targetTemperatureF": int(value)
            }
        })
        await self.coordinator.async_request_refresh()


class FreeSleepBaseHeadNumber(CoordinatorEntity[FreeSleepDataUpdateCoordinator], NumberEntity):
    """Representation of base head angle number."""

    _attr_has_entity_name = True
    _attr_name = "Base head angle"
    _attr_icon = "mdi:bed"
    _attr_native_min_value = BASE_HEAD_MIN
    _attr_native_max_value = BASE_HEAD_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = "°"

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_base_head"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 4 with Adjustable Base",
            "configuration_url": entry.data.get("host"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if base_control := self.coordinator.data.get("base_control"):
            return base_control.get("head")
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        # Get current feet position
        feet = BASE_FEET_MIN
        if base_control := self.coordinator.data.get("base_control"):
            feet = base_control.get("feet", BASE_FEET_MIN)

        await self.coordinator.api.async_set_base_position(
            int(value), feet, BASE_FEED_RATE_DEFAULT
        )
        await self.coordinator.async_request_refresh()


class FreeSleepBaseFeetNumber(CoordinatorEntity[FreeSleepDataUpdateCoordinator], NumberEntity):
    """Representation of base feet angle number."""

    _attr_has_entity_name = True
    _attr_name = "Base feet angle"
    _attr_icon = "mdi:bed"
    _attr_native_min_value = BASE_FEET_MIN
    _attr_native_max_value = BASE_FEET_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = "°"

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_base_feet"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 4 with Adjustable Base",
            "configuration_url": entry.data.get("host"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if base_control := self.coordinator.data.get("base_control"):
            return base_control.get("feet")
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        # Get current head position
        head = BASE_HEAD_MIN
        if base_control := self.coordinator.data.get("base_control"):
            head = base_control.get("head", BASE_HEAD_MIN)

        await self.coordinator.api.async_set_base_position(
            head, int(value), BASE_FEED_RATE_DEFAULT
        )
        await self.coordinator.async_request_refresh()


class FreeSleepBaseFeedRateNumber(CoordinatorEntity[FreeSleepDataUpdateCoordinator], NumberEntity):
    """Representation of base feed rate number."""

    _attr_has_entity_name = True
    _attr_name = "Base feed rate"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = BASE_FEED_RATE_MIN
    _attr_native_max_value = BASE_FEED_RATE_MAX
    _attr_native_step = 5
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_base_feed_rate"
        self._feed_rate = BASE_FEED_RATE_DEFAULT
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 4 with Adjustable Base",
            "configuration_url": entry.data.get("host"),
        }

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self._feed_rate

    async def async_set_native_value(self, value: float) -> None:
        """Set new value (stored for next position change)."""
        self._feed_rate = int(value)

