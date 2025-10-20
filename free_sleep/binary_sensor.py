"""Binary sensor platform for Free Sleep."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, SIDE_LEFT, SIDE_RIGHT
from .coordinator import FreeSleepDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FreeSleepBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Free Sleep binary sensor entity."""

    value_fn: Callable[[dict[str, Any]], bool | None] | None = None
    side: str | None = None


BINARY_SENSOR_TYPES: tuple[FreeSleepBinarySensorEntityDescription, ...] = (
    # Water level
    FreeSleepBinarySensorEntityDescription(
        key="water_level_ok",
        translation_key="water_level_ok",
        name="Water level OK",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: data.get("device_status", {}).get("waterLevel") == "true",
    ),
    # Priming status
    FreeSleepBinarySensorEntityDescription(
        key="is_priming",
        translation_key="is_priming",
        name="Priming",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:water-pump",
        value_fn=lambda data: data.get("device_status", {}).get("isPriming", False),
    ),
    # Prime notification
    FreeSleepBinarySensorEntityDescription(
        key="prime_notification",
        translation_key="prime_notification",
        name="Prime notification",
        icon="mdi:bell",
        value_fn=lambda data: data.get("device_status", {}).get("primeCompletedNotification") is not None,
    ),
    # Base moving
    FreeSleepBinarySensorEntityDescription(
        key="base_moving",
        translation_key="base_moving",
        name="Base moving",
        device_class=BinarySensorDeviceClass.MOVING,
        value_fn=lambda data: data.get("base_control", {}).get("isMoving", False),
    ),
    # Left side sensors
    FreeSleepBinarySensorEntityDescription(
        key="pod_on_left",
        translation_key="pod_on",
        name="Pod on left",
        device_class=BinarySensorDeviceClass.POWER,
        side=SIDE_LEFT,
        value_fn=lambda data: data.get("device_status", {}).get("left", {}).get("isOn", False),
    ),
    FreeSleepBinarySensorEntityDescription(
        key="alarm_vibrating_left",
        translation_key="alarm_vibrating",
        name="Alarm vibrating left",
        device_class=BinarySensorDeviceClass.VIBRATION,
        side=SIDE_LEFT,
        value_fn=lambda data: data.get("device_status", {}).get("left", {}).get("isAlarmVibrating", False),
    ),
    # Right side sensors
    FreeSleepBinarySensorEntityDescription(
        key="pod_on_right",
        translation_key="pod_on",
        name="Pod on right",
        device_class=BinarySensorDeviceClass.POWER,
        side=SIDE_RIGHT,
        value_fn=lambda data: data.get("device_status", {}).get("right", {}).get("isOn", False),
    ),
    FreeSleepBinarySensorEntityDescription(
        key="alarm_vibrating_right",
        translation_key="alarm_vibrating",
        name="Alarm vibrating right",
        device_class=BinarySensorDeviceClass.VIBRATION,
        side=SIDE_RIGHT,
        value_fn=lambda data: data.get("device_status", {}).get("right", {}).get("isAlarmVibrating", False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Free Sleep binary sensor entities."""
    coordinator: FreeSleepDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        FreeSleepBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_TYPES
    ]

    async_add_entities(entities)


class FreeSleepBinarySensor(CoordinatorEntity[FreeSleepDataUpdateCoordinator], BinarySensorEntity):
    """Representation of a Free Sleep binary sensor."""

    entity_description: FreeSleepBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
        description: FreeSleepBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 3/4",
            "configuration_url": entry.data.get("host"),
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

