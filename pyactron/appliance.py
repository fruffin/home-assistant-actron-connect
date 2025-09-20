"""Pyactron base appliance, represent an Actron device."""

import asyncio
from datetime import datetime, timedelta
import json
import logging
from typing import Optional

from aiohttp import ClientSession
from aiohttp.client_exceptions import (
    ClientOSError,
    ClientResponseError,
    ServerDisconnectedError,
)
from aiohttp.web_exceptions import HTTPForbidden
from homeassistant.components.climate.const import HVACAction, HVACMode

import re

from ..const import DEVICE_UPDATE_SKIP_SECONDS
from .exceptions import ActronException
from .actron_user import ActronUser
from .service_configuration import ServiceConfiguration

_LOGGER = logging.getLogger(__name__)

HVACMODE_TO_ACTRON = {
    HVACMode.HEAT_COOL: 0,
    HVACMode.HEAT: 1,
    HVACMode.COOL: 2,
    HVACMode.FAN_ONLY: 3,
}

ACTRON_TO_HVACMODE = {
    0: HVACMode.HEAT_COOL,
    1: HVACMode.HEAT,
    2: HVACMode.COOL,
    3: HVACMode.FAN_ONLY,
}

FAN_SPEED_STRING_TO_ACTRON = {
    "low": 0,
    "medium": 1,
    "high": 2,
}

ACTRON_TO_FAN_SPEED_STRING = {
    0: "low",
    1: "medium",
    2: "high",
}

HVACACTION_TO_ACTRON = {
    HVACAction.HEATING: 0,
    HVACAction.COOLING: 1,
    HVACAction.IDLE: 2,
}

ACTRON_TO_HVACACTION = {
    0: HVACAction.HEATING,
    1: HVACAction.COOLING,
    2: HVACAction.IDLE,
}

DEVICE_ID_REGULAR_EXPRESSION = r"\"(ACONNECT[0-9A-F]+_\d_\d_\d)\":{\"vid\":\d,\"did\":\d,\"device_type\":\"airconditioner\",\"default_name\":\"Air Conditioner Settings\""

class Appliance:  # pylint: disable=too-many-public-methods
    """Actron main appliance class."""

    hostname: str
    base_url: str
    service_configuration: ServiceConfiguration
    user: ActronUser
    session: ClientSession
    _mac: str
    _device_id: str
    _block_id: str
    _firmwareVersion: str
    _is_on: bool
    _mode: int
    _fan_speed: int
    _target_temperature: float
    _current_temperature: float
    _is_esp_on: bool
    _is_fan_continuous: bool
    _compressor_activity: int
    _enabled_zones: list[int]
    _skip_update_until: datetime = datetime.min

    MAX_CONCURRENT_REQUESTS = 4

    def __init__(self, hostname: str, service_configuration: ServiceConfiguration, user: ActronUser, session: ClientSession) -> None:
        """Init the pyactron appliance, representing one Actron device."""
        self.hostname = hostname
        self.base_url = f"http://{self.hostname}"
        self.service_configuration = service_configuration
        self.user = user
        self.session = session
        self.request_semaphore = asyncio.Semaphore(value=self.MAX_CONCURRENT_REQUESTS)
        self.headers: dict = {}

    async def init(self):
        """Initialize the device and fetch initial state."""
        self._block_id = await self._get_block_id_from_remote_service()
        await self.update_device_info()
        await self.update_status()

    async def update_device_info(self):
        """Update device info."""
        # fetch info form the local device
        try:
            info_response = await self._get_resource("1.json")

            if not info_response:
                raise ActronException("Invalid response from device")
        except Exception as e:
            _LOGGER.error("Error communicating with device: %s", e)
            raise ActronException(f"Failed to communicate with device: {e}") from e

        # Extract basic info
        try:
            data = json.loads(info_response)

            self._mac = data['MacAddress']
            self._device_id = data['BlockID']
            self._firmwareVersion = data['firmwareVersion']
        except ActronException as e:
            _LOGGER.error("Error extracting values: %s", e)
            raise

    async def update_status(self):
        """Update device status."""

        # updating the state of the device can take some time to propagate to the actual device
        # so we delay the update to the next update cycle to avoid the state going back and forth
        # between actual state and desired state
        if self._skip_update_until < datetime.now():
            # fetch info form the local device
            try:
                data_response = await self._get_resource("6.json")

                if not data_response:
                    raise ActronException("Invalid response from device")
            except Exception as e:
                _LOGGER.error("Error communicating with device: %s", e)
                raise ActronException(f"Failed to communicate with device: {e}") from e

            # Extract basic info
            try:
                data = json.loads(data_response)

                self._is_on = data['isOn']
                self._mode = data['mode']
                self._fan_speed = data['fanSpeed']
                self._target_temperature = data['setPoint']
                self._current_temperature = data['roomTemp_oC']
                self._is_esp_on = data['isInESP_Mode']
                self._is_fan_continuous = data['fanIsCont']
                self._compressor_activity = data['compressorActivity']
                self._enabled_zones = data['enabledZones']
            except ActronException as e:
                _LOGGER.error("Error extracting values: %s", e)
                raise

    async def _get_resource(self, path: str, params: Optional[dict] = None):
        """Make the http request."""
        if params is None:
            params = {}

        _LOGGER.debug(
            "Calling: %s/%s %s [%s]",
            self.base_url,
            path,
            params if "pass" not in params else {**params, **{"pass": "****"}},
            self.headers,
        )

        # cannot manage session on outer async with or this will close the session
        # passed to pyactron (homeassistant for instance)
        async with self.request_semaphore:
            async with self.session.get(
                f'{self.base_url}/{path}',
                params=params,
            ) as response:
                if response.status == 403:
                    raise HTTPForbidden(reason=f"HTTP 403 Forbidden for {response.url}")
                if response.status == 404:
                    _LOGGER.debug("HTTP 404 Not Found for %s", response.url)
                    return (
                        {}
                    )  # return an empty dict to indicate successful connection but bad data
                if response.status != 200:
                    _LOGGER.debug(
                        "Unexpected HTTP status code %s for %s",
                        response.status,
                        response.url,
                    )
                response.raise_for_status()
                return await response.text()

    def _extract_block_id_from_response(self, response: str) -> str:
        """Extract the block id from the response."""
        match = re.search(DEVICE_ID_REGULAR_EXPRESSION, response)
        if match:
            return match.group(1)
        return None

    async def _get_block_id_from_remote_service(self) -> str:
        """Get the block id from the remote service."""
        service_url = f'https://{self.service_configuration.ninja_service_host}/rest/v0/devices?user_access_token={self.user.user_access_token}'
        _LOGGER.debug("Loading service configuration from: %s", service_url)

        try:
            async with self.session.get(
                service_url,
            ) as response:
                if response.status != 200:
                    _LOGGER.debug(
                        "Unexpected HTTP status code %s for %s",
                        response.status,
                        response.url,
                    )
                response.raise_for_status()

                block_id = self._extract_block_id_from_response(await response.text())

                if block_id is None:
                    raise ActronException("Failed to get block id")

                return block_id
               
        except Exception as e:
            _LOGGER.error("Unexpected error while fetching the block id: %s", e)
            raise ActronException(f"Unexpected error: {e}") from e

    async def _send_ninja_command(self, block_id: str, payload: str) -> None:
        """Send a command to the Ninja service."""
        url = f'https://{self.service_configuration.ninja_service_host}/rest/v0/device/{block_id}?user_access_token={self.user.user_access_token}'

        try:
            async with self.session.put(
                url,
                headers={'Content-Type': 'application/json'},
                data=payload,
            ) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Unexpected HTTP status code when sending a ninja command: %s for %s",
                        response.status,
                        response.url,
                    )
                response.raise_for_status()
            
            # skip the update for a few seconds to avoid the state going back and forth
            self._skip_update_until = datetime.now() + timedelta(seconds=DEVICE_UPDATE_SKIP_SECONDS)
        except Exception as e:
            _LOGGER.error("Unexpected error while sending a ninja command: %s", e)
            raise ActronException(f"Unexpected error: {e}") from e

    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        """Set new target hvac mode."""
        # turn off the device if the mode is off
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
            return

        # turn on the device if it is not already on
        if not self.is_on:
            await self.async_turn_on()

        payload = f'{{"DA":{{"mode":{HVACMODE_TO_ACTRON[hvac_mode]} }}}}'
        await self._send_ninja_command(self._block_id, payload)
        self._mode = HVACMODE_TO_ACTRON[hvac_mode]

    async def async_turn_on(self):
        """Turn the entity on."""
        payload = '{"DA":{"amOn":1} }'
        await self._send_ninja_command(self._block_id, payload)
        self._is_on = True

    async def async_turn_off(self):
        """Turn the entity off."""
        payload = '{"DA":{"amOn":0} }'
        await self._send_ninja_command(self._block_id, payload)
        self._is_on = False

    async def async_set_fan_mode(self, fan_mode: str):
        """Set new target fan mode."""
        payload = f'{{"DA":{{"fanSpeed":{FAN_SPEED_STRING_TO_ACTRON[fan_mode]} }}}}'
        await self._send_ninja_command(self._block_id, payload)
        self._fan_speed = FAN_SPEED_STRING_TO_ACTRON[fan_mode]

    async def async_set_temperature(self, target_temperature: float):
        """Set new target temperature."""
        payload = f'{{"DA":{{"tempTarget":{target_temperature} }}}}'
        await self._send_ninja_command(self._block_id, payload)
        self._target_temperature = target_temperature

    async def async_zone_turn_on(self, zone_id: int):
        """Set zone status."""
        self._enabled_zones[zone_id] = 1
        payload = f'{{"DA":{{"enabledZones":{json.dumps(self._enabled_zones)} }}}}'
        await self._send_ninja_command(self._block_id, payload)

    async def async_zone_turn_off(self, zone_id: int):
        """Set zone status."""
        self._enabled_zones[zone_id] = 0
        payload = f'{{"DA":{{"enabledZones":{json.dumps(self._enabled_zones)} }}}}'
        await self._send_ninja_command(self._block_id, payload)

    @property
    def manufacturer(self) -> str:
        """Return device's manufacturer."""
        return "Actron"
    
    @property
    def model(self) -> str:
        """Return device's model."""
        return "Actron Ultima"

    @property
    def mac(self) -> str:
        """Return device's MAC address."""
        return self._mac

    @property
    def device_id(self) -> str:
        """Return device's ID."""
        return self._device_id

    @property
    def block_id(self) -> str:
        """Return device's block ID."""
        return self._block_id

    @property
    def firmware_version(self) -> str:
        """Return device's firmware version."""
        return self._firmwareVersion

    @property
    def is_on(self) -> bool:
        """Return device's on status."""
        return self._is_on

    @property
    def mode(self) -> HVACMode:
        """Return device's mode."""
        if not self.is_on:
            return HVACMode.OFF

        return ACTRON_TO_HVACMODE[self._mode]

    @property
    def fan_speed(self) -> str:
        """Return device's fan speed."""
        return ACTRON_TO_FAN_SPEED_STRING[self._fan_speed]

    @property
    def target_temperature(self) -> float:
        """Return device's target temperature."""
        return self._target_temperature

    @property
    def current_temperature(self) -> float:
        """Return device's current temperature."""
        return self._current_temperature

    @property
    def is_esp_on(self) -> bool:
        """Return device's ESP on status."""
        return self._is_esp_on

    @property
    def is_fan_continuous(self) -> bool:
        """Return device's fan continuous status."""
        return self._is_fan_continuous

    @property
    def compressor_activity(self) -> HVACAction:
        """Return device's compressor activity."""
        return ACTRON_TO_HVACACTION[self._compressor_activity]

    @property
    def enabled_zones(self) -> list[int]:
        """Return device's enabled zones."""
        return self._enabled_zones

    @property
    def zone_names(self) -> list[str]:
        """Return a list of zone names."""
        return self.user.zones

    # @property
    # def support_zone_count(self) -> bool:
    #     """Return True if the device supports count of active zones."""
    #     return "en_zone" in self.values
