"""Config flow for the actron_ultima integration."""

from __future__ import annotations

import json
import logging
from types import MappingProxyType
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .pyactron.exceptions import ActronException

from .pyactron.actron_user import ActronUser

from .const import CONF_SERVICE_CONFIGURATION, CONF_USER, CONF_ZONES, DOMAIN
from .pyactron.service_configuration import ServiceConfiguration

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_ZONES): int,
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host

    async def authenticate(self, username: str, password: str) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data[CONF_USERNAME], data[CONF_PASSWORD]
    # )

    hub = PlaceholderHub(data[CONF_HOST])

    if not await hub.authenticate(data[CONF_USERNAME], data[CONF_PASSWORD]):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Name of the device"}


class FlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for actron_ultima."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # retrieve the service configuration
                session = async_get_clientsession(self.hass)
                service_configuration = ServiceConfiguration(session)
                await service_configuration.refresh_configuration()

                # log in
                user = await self._login(user_input[CONF_USERNAME], user_input[CONF_PASSWORD], service_configuration, session)

                # store the service configuration and user data in the entry data
                entry_data = {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_ZONES: user_input[CONF_ZONES],
                    # Store service configuration data using dataclass serialization
                    CONF_SERVICE_CONFIGURATION: service_configuration.to_dict(),
                    # Store user data using dataclass serialization
                    CONF_USER: user.to_dict(),
                }
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=entry_data)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def _login(self, username, password, service_configuration, session) -> ActronUser:
        """Login to the Actron cloud service."""

        _LOGGER.debug("Loading service configuration from: %s/signin", service_configuration.service_base_url)

        try:
            async with session.post(
                f'{service_configuration.service_base_url}/signin',
                auth=aiohttp.BasicAuth(username, password),
            ) as response:
                if response.status != 200:
                    _LOGGER.debug(
                        "Unexpected HTTP status code %s for %s",
                        response.status,
                        response.url,
                    )
                response.raise_for_status()

                data = json.loads(await response.text())

                return ActronUser(
                    email=data['value']['email'],
                    fullname=data['value']['fullname'],
                    address=data['value']['address1'],
                    suburb=data['value']['suburb'],
                    postcode=data['value']['postcode'],
                    state=data['value']['state'],
                    country=data['value']['country'],
                    user_access_token=data['value']['userAccessToken'],
                    last_updated=data['value']['lastUpdated'],
                    created_at=data['value']['createdAt'],
                    timezone=data['value']['timezone'],
                    version=data['value']['version'],
                    aircon_block_id=data['value']['airconBlockId'],
                    aircon_type=data['value']['airconType'],
                    aircon_zone_number=data['value']['airconZoneNumber'],
                    zones=data['value']['zones'],
                )
        except Exception as e:
            _LOGGER.error("Unexpected error while fetching service configuration: %s", e)
            raise ActronException(f"Unexpected error: {e}") from e

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
