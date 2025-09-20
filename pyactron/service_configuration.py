"""Actron service configuration, retrieved from the cloud service."""

import json
import logging
from dataclasses import dataclass
from typing import ClassVar

from aiohttp import ClientSession
from aiohttp.client_exceptions import (
    ClientOSError,
    ClientResponseError,
    ServerDisconnectedError,
)

from .exceptions import ActronException

_LOGGER = logging.getLogger(__name__)

@dataclass
class ServiceConfiguration:
    """Actron service configuration class for cloud service."""
    # Class variables (not serialized)
    service_configuration_url: ClassVar[str] = "https://que.actronair.com.au/api/v0/bc/app-config"
    
    # Non-serializable fields (must be first to be required)
    session: ClientSession
    
    # Instance variables (serialized)
    service_base_url: str = "https://que.actronair.com.au/api/v0/bc"
    ninja_service_host: str = "que.actronair.com.au"
    notification_mode: str = "SignalR"
    signalr_endpoint: str = "https://que.actronair.com.au/api/v0/messaging/aconnect"

    def to_dict(self) -> dict:
        """Convert to serializable dictionary."""
        # Manually create dict excluding the session field to avoid deepcopy issues
        return {
            "service_base_url": self.service_base_url,
            "ninja_service_host": self.ninja_service_host,
            "notification_mode": self.notification_mode,
            "signalr_endpoint": self.signalr_endpoint,
        }
    
    @classmethod
    def from_dict(cls, data: dict, session: ClientSession) -> "ServiceConfiguration":
        """Create from dictionary."""
        return cls(session=session, **data)

    async def refresh_configuration(self) -> None:
        """Refresh the service configuration from the remote service."""
        await self._get_remote_configuration()

    async def _get_remote_configuration(self):
        """Make the http request."""

        _LOGGER.debug(
            "Loading service configuration from: %s", self.service_configuration_url
        )

        try:
            async with self.session.get(
                f"{self.service_configuration_url}",
            ) as response:
                if response.status != 200:
                    _LOGGER.debug(
                        "Unexpected HTTP status code %s for %s",
                        response.status,
                        response.url,
                    )
                response.raise_for_status()

                data = json.loads(await response.text())

                self.service_base_url = data["accountServiceBaseUri"]
                self.ninja_service_host = data["ninjaServiceHost"]
                self.notification_mode = data["notificationMode"]
                self.signalr_endpoint = data["signalrEndpoint"]

        # TODO: do this to other HTTP requests
        except ClientOSError as e:
            _LOGGER.error("Network error while fetching service configuration: %s", e)
            raise ActronException(f"Network error: {e}") from e
        except ClientResponseError as e:
            _LOGGER.error(
                "HTTP error while fetching service configuration: %s (status: %s)",
                e,
                e.status,
            )
            raise ActronException(f"HTTP error {e.status}: {e}") from e
        except ServerDisconnectedError as e:
            _LOGGER.error(
                "Server disconnected while fetching service configuration: %s", e
            )
            raise ActronException(f"Server disconnected: {e}") from e
        except json.JSONDecodeError as e:
            _LOGGER.error(
                "Invalid JSON response from service configuration endpoint: %s", e
            )
            raise ActronException(f"Invalid JSON response: {e}") from e
        except KeyError as e:
            _LOGGER.error(
                "Missing required field in service configuration response: %s", e
            )
            raise ActronException(f"Missing required field in response: {e}") from e
        except Exception as e:
            _LOGGER.error(
                "Unexpected error while fetching service configuration: %s", e
            )
            raise ActronException(f"Unexpected error: {e}") from e
