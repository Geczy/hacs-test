"""Climate platform for Free Sleep."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
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
    """Set up Free Sleep climate entities."""
    coordinator: FreeSleepDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        FreeSleepClimate(coordinator, entry, SIDE_LEFT),
        FreeSleepClimate(coordinator, entry, SIDE_RIGHT),
    ]

    async_add_entities(entities)


class FreeSleepClimate(CoordinatorEntity[FreeSleepDataUpdateCoordinator], ClimateEntity):
    """Representation of a Free Sleep climate entity."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT_COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_min_temp = MIN_TEMPERATURE_F
    _attr_max_temp = MAX_TEMPERATURE_F
    _attr_target_temperature_step = 1

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
        side: str,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._side = side
        self._attr_unique_id = f"{entry.entry_id}_{side}_climate"
        self._attr_name = f"{side.capitalize()} side"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 3/4",
            "configuration_url": entry.data.get("host"),
        }

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if device_status := self.coordinator.data.get("device_status"):
            if side_data := device_status.get(self._side):
                return side_data.get("currentTemperatureF")
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        if device_status := self.coordinator.data.get("device_status"):
            if side_data := device_status.get(self._side):
                return side_data.get("targetTemperatureF")
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation mode."""
        if device_status := self.coordinator.data.get("device_status"):
            if side_data := device_status.get(self._side):
                if side_data.get("isOn"):
                    return HVACMode.HEAT_COOL
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation."""
        if device_status := self.coordinator.data.get("device_status"):
            if side_data := device_status.get(self._side):
                if not side_data.get("isOn"):
                    return HVACAction.OFF

                current = side_data.get("currentTemperatureF")
                target = side_data.get("targetTemperatureF")

                if current is not None and target is not None:
                    if abs(current - target) < 1:
                        return HVACAction.IDLE
                    elif current < target:
                        return HVACAction.HEATING
                    else:
                        return HVACAction.COOLING

        return HVACAction.OFF

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {}
        if device_status := self.coordinator.data.get("device_status"):
            if side_data := device_status.get(self._side):
                if seconds := side_data.get("secondsRemaining"):
                    attrs["seconds_remaining"] = seconds
                if alarm := side_data.get("isAlarmVibrating"):
                    attrs["alarm_vibrating"] = alarm

        # Check if away mode is enabled
        if settings := self.coordinator.data.get("settings"):
            if side_settings := settings.get(self._side):
                if away_mode := side_settings.get("awayMode"):
                    attrs["away_mode"] = away_mode

        return attrs

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        # Check if away mode is enabled
        if settings := self.coordinator.data.get("settings"):
            if side_settings := settings.get(self._side):
                if side_settings.get("awayMode"):
                    _LOGGER.warning(
                        "Cannot change temperature while %s side is in away mode",
                        self._side
                    )
                    return

        await self.coordinator.api.async_update_device_status({
            self._side: {
                "targetTemperatureF": int(temperature)
            }
        })
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
        elif hvac_mode == HVACMode.HEAT_COOL:
            await self.async_turn_on()

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self.coordinator.api.async_update_device_status({
            self._side: {
                "isOn": True
            }
        })
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self.coordinator.api.async_update_device_status({
            self._side: {
                "isOn": False
            }
        })
        await self.coordinator.async_request_refresh()

