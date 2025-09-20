"""Coordinator for Daikin integration."""

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .pyactron.appliance import Appliance

_LOGGER = logging.getLogger(__name__)

type ActronConfigEntry = ConfigEntry[ActronCoordinator]
class ActronCoordinator(DataUpdateCoordinator[None]):
    """Class to manage fetching Actron data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ActronConfigEntry, 
        device: Appliance
    ) -> None:
        """Initialize global Actron data updater."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=device.device_id,
            update_interval=timedelta(seconds=10),
        )
        self.device = device

    async def _async_update_data(self) -> None:
        await self.device.update_status()


