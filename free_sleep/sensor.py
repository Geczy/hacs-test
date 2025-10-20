"""Sensor platform for Free Sleep."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, SIDE_LEFT, SIDE_RIGHT
from .coordinator import FreeSleepDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FreeSleepSensorEntityDescription(SensorEntityDescription):
    """Describes Free Sleep sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType] | None = None
    side: str | None = None


SENSOR_TYPES: tuple[FreeSleepSensorEntityDescription, ...] = (
    # Water level sensors
    FreeSleepSensorEntityDescription(
        key="water_level",
        translation_key="water_level",
        name="Water level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _calculate_water_level_percentage(data),
    ),
    # Room climate sensors
    FreeSleepSensorEntityDescription(
        key="room_temperature",
        translation_key="room_temperature",
        name="Room temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("device_status", {}).get("roomClimate", {}).get("temperatureC"),
    ),
    FreeSleepSensorEntityDescription(
        key="room_humidity",
        translation_key="room_humidity",
        name="Room humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("device_status", {}).get("roomClimate", {}).get("humidity"),
    ),
    # LED brightness
    FreeSleepSensorEntityDescription(
        key="led_brightness",
        translation_key="led_brightness",
        name="LED brightness",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightbulb",
        value_fn=lambda data: data.get("device_status", {}).get("settings", {}).get("ledBrightness"),
    ),
    # Left side sensors
    FreeSleepSensorEntityDescription(
        key="current_temp_left",
        translation_key="current_temperature",
        name="Current temperature left",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        side=SIDE_LEFT,
        value_fn=lambda data: data.get("device_status", {}).get("left", {}).get("currentTemperatureF"),
    ),
    FreeSleepSensorEntityDescription(
        key="time_remaining_left",
        translation_key="time_remaining",
        name="Time remaining left",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer",
        side=SIDE_LEFT,
        value_fn=lambda data: data.get("device_status", {}).get("left", {}).get("secondsRemaining"),
    ),
    FreeSleepSensorEntityDescription(
        key="heart_rate_left",
        translation_key="heart_rate",
        name="Heart rate left",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-pulse",
        side=SIDE_LEFT,
        value_fn=lambda data: data.get("vitals", {}).get("left", {}).get("avgHeartRate"),
    ),
    FreeSleepSensorEntityDescription(
        key="hrv_left",
        translation_key="hrv",
        name="HRV left",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-pulse",
        side=SIDE_LEFT,
        value_fn=lambda data: data.get("vitals", {}).get("left", {}).get("avgHRV"),
    ),
    FreeSleepSensorEntityDescription(
        key="breathing_rate_left",
        translation_key="breathing_rate",
        name="Breathing rate left",
        native_unit_of_measurement="breaths/min",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lungs",
        side=SIDE_LEFT,
        value_fn=lambda data: data.get("vitals", {}).get("left", {}).get("avgBreathingRate"),
    ),
    # Right side sensors
    FreeSleepSensorEntityDescription(
        key="current_temp_right",
        translation_key="current_temperature",
        name="Current temperature right",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        side=SIDE_RIGHT,
        value_fn=lambda data: data.get("device_status", {}).get("right", {}).get("currentTemperatureF"),
    ),
    FreeSleepSensorEntityDescription(
        key="time_remaining_right",
        translation_key="time_remaining",
        name="Time remaining right",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer",
        side=SIDE_RIGHT,
        value_fn=lambda data: data.get("device_status", {}).get("right", {}).get("secondsRemaining"),
    ),
    FreeSleepSensorEntityDescription(
        key="heart_rate_right",
        translation_key="heart_rate",
        name="Heart rate right",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-pulse",
        side=SIDE_RIGHT,
        value_fn=lambda data: data.get("vitals", {}).get("right", {}).get("avgHeartRate"),
    ),
    FreeSleepSensorEntityDescription(
        key="hrv_right",
        translation_key="hrv",
        name="HRV right",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-pulse",
        side=SIDE_RIGHT,
        value_fn=lambda data: data.get("vitals", {}).get("right", {}).get("avgHRV"),
    ),
    FreeSleepSensorEntityDescription(
        key="breathing_rate_right",
        translation_key="breathing_rate",
        name="Breathing rate right",
        native_unit_of_measurement="breaths/min",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lungs",
        side=SIDE_RIGHT,
        value_fn=lambda data: data.get("vitals", {}).get("right", {}).get("avgBreathingRate"),
    ),
)


def _calculate_water_level_percentage(data: dict[str, Any]) -> float | None:
    """Calculate water level percentage from raw sensor data."""
    if water_raw := data.get("device_status", {}).get("waterLevelRaw"):
        raw = water_raw.get("raw")
        calibrated_empty = water_raw.get("calibratedEmpty")
        calibrated_full = water_raw.get("calibratedFull")

        if raw is not None and calibrated_empty is not None and calibrated_full is not None:
            if calibrated_full <= calibrated_empty:
                return None

            percentage = ((raw - calibrated_empty) / (calibrated_full - calibrated_empty)) * 100
            return max(0, min(100, percentage))

    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Free Sleep sensor entities."""
    coordinator: FreeSleepDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        FreeSleepSensor(coordinator, entry, description)
        for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class FreeSleepSensor(CoordinatorEntity[FreeSleepDataUpdateCoordinator], SensorEntity):
    """Representation of a Free Sleep sensor."""

    entity_description: FreeSleepSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
        description: FreeSleepSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

