"""The actron_ultima integration."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .pyactron.appliance import Appliance

from .pyactron.service_configuration import ServiceConfiguration
from .pyactron.actron_user import ActronUser

from .const import CONF_SERVICE_CONFIGURATION, CONF_USER
from .coordinator import ActronConfigEntry, ActronCoordinator

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.CLIMATE]


def _recreate_service_configuration(service_config_data: dict, session) -> ServiceConfiguration:
    """Recreate ServiceConfiguration object from stored data."""
    return ServiceConfiguration.from_dict(service_config_data, session)


def _recreate_actron_user(user_data: dict) -> ActronUser:
    """Recreate ActronUser object from stored data."""
    return ActronUser.from_dict(user_data)


async def async_setup_entry(hass: HomeAssistant, entry: ActronConfigEntry) -> bool:
    """Set up actron_ultima from a config entry."""
    conf = entry.data

    host = conf[CONF_HOST]

    # recreate the service configuration from stored data
    session = async_get_clientsession(hass)
    service_configuration = _recreate_service_configuration(conf[CONF_SERVICE_CONFIGURATION], session)
    
    # recreate the user from stored data
    user = _recreate_actron_user(conf[CONF_USER])

    # refreshing the service configuration after restarts to make sure it is up to date
    await service_configuration.refresh_configuration()

    # create the appliance
    device = Appliance(host, service_configuration, user, session)
    await device.init()

    # create the coordinator
    coordinator = ActronCoordinator(hass, entry, device)
    await coordinator.async_config_entry_first_refresh()

    # store the coordinator in the entry
    entry.runtime_data = coordinator

    # forward the entry to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ActronConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
