"""Base entity for Actron."""

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ActronCoordinator


class ActronEntity(CoordinatorEntity[ActronCoordinator]):
    """Base entity for Actron."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ActronCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.device = coordinator.device

        self._attr_device_info = DeviceInfo(
            connections={
                (CONNECTION_NETWORK_MAC, self.device.mac)
            },
            manufacturer=self.device.manufacturer,
            model=self.device.user.aircon_model,
            name=self.device.device_id,
            sw_version= self.device.firmware_version,
        )
