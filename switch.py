"""Support for Actron Ultima zones."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ActronConfigEntry, ActronCoordinator
from .entity import ActronEntity

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ActronConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Actron climate based on config_entry."""
    coordinator = entry.runtime_data
    switches: list[SwitchEntity] = []
    # if zones := coordinator.device.zones:
    #     switches.extend(
    #         ActronZoneSwitch(coordinator, zone_id)
    #         for zone_id, zone in enumerate(zones)
    #         if zone[0] != "-"
    #     )

    switches.append(ActronToggleSwitch(coordinator))
    async_add_entities(switches)


# class ActronZoneSwitch(ActronEntity, SwitchEntity):
#     """Representation of a zone."""

#     _attr_translation_key = "zone"

#     def __init__(self, coordinator: ActronCoordinator, zone_id: int) -> None:
#         """Initialize the zone."""
#         super().__init__(coordinator)
#         self._zone_id = zone_id
#         self._attr_unique_id = f"{self.device.mac}-zone{zone_id}"

#     @property
#     def name(self) -> str:
#         """Return the name of the sensor."""
#         return self.device.zones[self._zone_id][0]

#     @property
#     def is_on(self) -> bool:
#         """Return the state of the sensor."""
#         return self.device.zones[self._zone_id][1] == "1"

#     async def async_turn_on(self, **kwargs: Any) -> None:
#         """Turn the zone on."""
#         await self.device.set_zone(self._zone_id, "zone_onoff", "1")
#         await self.coordinator.async_refresh()

#     async def async_turn_off(self, **kwargs: Any) -> None:
#         """Turn the zone off."""
#         await self.device.set_zone(self._zone_id, "zone_onoff", "0")
#         await self.coordinator.async_refresh()


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
        # await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the AC off."""
        await self.device.async_turn_off()
        # await self.coordinator.async_refresh()
