"""Support for Actron Ultima zones."""

from __future__ import annotations

from typing import Any
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ActronConfigEntry, ActronCoordinator
from .entity import ActronEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ActronConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Actron climate based on config_entry."""
    coordinator = entry.runtime_data
    switches: list[SwitchEntity] = []
    if zone_names := coordinator.device.zone_names:
        switches.extend(
            ActronZoneSwitch(coordinator, zone_id, zone_name)
            for zone_id, zone_name in enumerate(zone_names)
        )

    switches.append(ActronToggleSwitch(coordinator))
    async_add_entities(switches)


class ActronZoneSwitch(ActronEntity, SwitchEntity):
    """Representation of a zone."""

    _attr_translation_key = "zone"

    def __init__(self, coordinator: ActronCoordinator, zone_id: int, zone_name: str) -> None:
        """Initialize the zone."""
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._zone_name = f"Zone - {zone_name}"
        self._attr_unique_id = f"{self.device.mac}-zone-{zone_id}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._zone_name

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return self.device.enabled_zones[self._zone_id] == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the zone on."""
        await self.device.async_zone_turn_on(self._zone_id)
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the zone off."""
        await self.device.async_zone_turn_off(self._zone_id)
        await self.coordinator.async_refresh()


class ActronToggleSwitch(ActronEntity, SwitchEntity):
    """Switch state."""

    _attr_translation_key = "toggle"

    def __init__(self, coordinator: ActronCoordinator) -> None:
        """Initialize switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.device.device_id}-toggle"
        self._attr_name = "Power"

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return self.device.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the AC on."""
        await self.device.async_turn_on()
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the AC off."""
        await self.device.async_turn_off()
        await self.coordinator.async_refresh()
