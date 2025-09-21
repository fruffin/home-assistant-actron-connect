"""Support for Actron AC sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ATTR_INSIDE_TEMPERATURE
from .coordinator import ActronConfigEntry, ActronCoordinator
from .entity import ActronEntity
from .pyactron.appliance import Appliance

@dataclass(frozen=True, kw_only=True)
class ActronSensorEntityDescription(SensorEntityDescription):
    """Describes Actron sensor entity."""

    value_func: Callable[[Appliance], float | None]

SENSOR_TYPES: tuple[ActronSensorEntityDescription, ...] = (
    ActronSensorEntityDescription(
        key=ATTR_INSIDE_TEMPERATURE,
        translation_key="inside_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_func=lambda device: device.current_temperature,
    ),
)

async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ActronConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Actron climate based on config_entry."""
    coordinator = entry.runtime_data
    sensors = [ATTR_INSIDE_TEMPERATURE]

    entities = [
        ActronSensor(coordinator, description)
        for description in SENSOR_TYPES
        if description.key in sensors
    ]
    async_add_entities(entities)


class ActronSensor(ActronEntity, SensorEntity):
    """Representation of a Sensor."""

    entity_description: ActronSensorEntityDescription

    def __init__(
        self, coordinator: ActronCoordinator, description: ActronSensorEntityDescription
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self.device.device_id}-{description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.entity_description.value_func(self.device)
