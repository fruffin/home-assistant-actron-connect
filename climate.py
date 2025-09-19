"""Support for the Actron HVAC."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DEVICE_TARGET_TEMPERATURE_STEP, DEVICE_MIN_TEMP, DEVICE_MAX_TEMP, DEVICE_TEMP_UNIT

from .coordinator import ActronConfigEntry, ActronCoordinator
from .entity import ActronEntity

_LOGGER = logging.getLogger(__name__)

_HVAC_MODES: list[HVACMode] = [HVACMode.COOL, HVACMode.HEAT, HVACMode.FAN_ONLY, HVACMode.HEAT_COOL, HVACMode.OFF]
_FAN_MODES: list[str] = ["low", "medium", "high"]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ActronConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Actron climate based on config_entry."""
    coordinator = entry.runtime_data
    async_add_entities([ActronClimate(coordinator)])

class ActronClimate(ActronEntity, ClimateEntity):
    """Representation of a Actron HVAC."""

    def __init__(self, coordinator: ActronCoordinator) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.device.device_id}-climate"
        self._attr_name = "Climate"
        self._attr_fan_modes = _FAN_MODES
        self._attr_hvac_modes = _HVAC_MODES
        self._attr_target_temperature_step = DEVICE_TARGET_TEMPERATURE_STEP
        self._attr_min_temp = DEVICE_MIN_TEMP
        self._attr_max_temp = DEVICE_MAX_TEMP
        self._attr_temperature_unit = DEVICE_TEMP_UNIT
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        await self.device.async_set_hvac_mode(hvac_mode)
        await self.coordinator.async_refresh()

    async def async_turn_on(self):
        """Turn the entity on."""
        await self.device.async_turn_on()
        await self.coordinator.async_refresh()

    async def async_turn_off(self):
        """Turn the entity off."""
        await self.device.async_turn_off()
        await self.coordinator.async_refresh()

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        await self.device.async_set_fan_mode(fan_mode)
        await self.coordinator.async_refresh()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        # Extract temperature from kwargs and convert to float
        target_temperature = float(kwargs.get(ATTR_TEMPERATURE))
        await self.device.async_set_temperature(target_temperature)
        await self.coordinator.async_refresh()

    @property
    def current_temperature(self) -> float:
        """Return the current inside temperature."""
        return self.device.current_temperature

    @property
    def fan_mode(self) -> str:
        """Return the current fan mode."""
        return self.device.fan_speed

    @property
    def hvac_action(self) -> HVACAction:
        """Return device's on status."""
        return self.device.compressor_activity

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        return self.device.mode

    @property
    def target_temperature(self) -> float:
        """Return the target temperature."""
        return self.device.target_temperature
