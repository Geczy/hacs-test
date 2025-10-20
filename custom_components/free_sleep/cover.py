"""Cover platform for Free Sleep adjustable base."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BASE_PRESET_FLAT,
    BASE_PRESETS,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import FreeSleepDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Free Sleep cover entities."""
    coordinator: FreeSleepDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Only create cover entity if base control is available
    if coordinator.data.get("base_control"):
        async_add_entities([FreeSleepBaseCover(coordinator, entry)])


class FreeSleepBaseCover(CoordinatorEntity[FreeSleepDataUpdateCoordinator], CoverEntity):
    """Representation of the adjustable base as a cover entity."""

    _attr_has_entity_name = True
    _attr_name = "Adjustable base"
    _attr_device_class = CoverDeviceClass.DAMPER
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.STOP
        | CoverEntityFeature.OPEN_TILT
        | CoverEntityFeature.CLOSE_TILT
        | CoverEntityFeature.SET_TILT_POSITION
    )

    def __init__(
        self,
        coordinator: FreeSleepDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the cover entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_base_cover"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Free Sleep Pod",
            "manufacturer": MANUFACTURER,
            "model": "Pod 4 with Adjustable Base",
            "configuration_url": entry.data.get("host"),
        }

    @property
    def current_cover_position(self) -> int | None:
        """Return current position (derived from head angle)."""
        if base_control := self.coordinator.data.get("base_control"):
            # Use head position as primary position (0-60° -> 0-100%)
            if head := base_control.get("head"):
                return int((head / 60) * 100)
        return None

    @property
    def current_cover_tilt_position(self) -> int | None:
        """Return current tilt position (derived from feet angle)."""
        if base_control := self.coordinator.data.get("base_control"):
            # Use feet position as tilt (0-45° -> 0-100%)
            if feet := base_control.get("feet"):
                return int((feet / 45) * 100)
        return None

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening."""
        if base_control := self.coordinator.data.get("base_control"):
            return base_control.get("isMoving", False)
        return False

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        # We can't distinguish opening vs closing, so return False
        return False

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed (flat position)."""
        if base_control := self.coordinator.data.get("base_control"):
            head = base_control.get("head", 0)
            feet = base_control.get("feet", 0)
            return head == 0 and feet == 0
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {}
        if base_control := self.coordinator.data.get("base_control"):
            attrs["head_angle"] = base_control.get("head", 0)
            attrs["feet_angle"] = base_control.get("feet", 0)
            if last_update := base_control.get("lastUpdate"):
                attrs["last_update"] = last_update
        return attrs

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover (go to relax preset)."""
        preset = BASE_PRESETS.get("relax", {})
        await self.coordinator.api.async_set_base_position(
            preset["head"], preset["feet"], preset.get("feedRate", 50)
        )
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover (go to flat position)."""
        await self.coordinator.api.async_set_base_preset(BASE_PRESET_FLAT)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position (sets head angle)."""
        if (position := kwargs.get(ATTR_POSITION)) is None:
            return

        # Convert position (0-100%) to head angle (0-60°)
        head = int((position / 100) * 60)

        # Keep current feet position
        feet = 0
        if base_control := self.coordinator.data.get("base_control"):
            feet = base_control.get("feet", 0)

        await self.coordinator.api.async_set_base_position(head, feet)
        await self.coordinator.async_request_refresh()

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        """Open the cover tilt (raise feet)."""
        await self.async_set_cover_tilt_position(tilt_position=100)

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        """Close the cover tilt (lower feet)."""
        await self.async_set_cover_tilt_position(tilt_position=0)

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position (sets feet angle)."""
        if (tilt_position := kwargs.get(ATTR_TILT_POSITION)) is None:
            return

        # Convert tilt position (0-100%) to feet angle (0-45°)
        feet = int((tilt_position / 100) * 45)

        # Keep current head position
        head = 0
        if base_control := self.coordinator.data.get("base_control"):
            head = base_control.get("head", 0)

        await self.coordinator.api.async_set_base_position(head, feet)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover movement."""
        # Set to current position to stop movement
        if base_control := self.coordinator.data.get("base_control"):
            head = base_control.get("head", 0)
            feet = base_control.get("feet", 0)
            await self.coordinator.api.async_set_base_position(head, feet)
            await self.coordinator.async_request_refresh()

