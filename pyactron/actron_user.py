"""Actron user class."""

from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from typing import Optional

_LOGGER = logging.getLogger(__name__)
DEVICE_TYPE_TO_MODEL_NAME = {
    0: "Standard Classic",
    1: "ESP Plus",
    2: "ESP Ultima",
    3: "Platinum Plus",
    4: "Platinum Ultima",
}

@dataclass
class ActronUser:
    """Actron user class."""
    
    email: str
    fullname: str
    address: str
    suburb: str
    postcode: str
    state: str
    country: str
    user_access_token: str
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None
    timezone: str = ""
    version: str = ""
    aircon_block_id: str = ""
    aircon_type: int = 0
    aircon_zone_number: int = 0
    zones: list[str] = None
    
    @property
    def aircon_model(self) -> str:
        """Return the model of the aircon."""
        return f"Actron {DEVICE_TYPE_TO_MODEL_NAME[self.aircon_type]}"

    def __post_init__(self):
        """Initialize after dataclass creation."""
        if self.zones is None:
            self.zones = []

    def to_dict(self) -> dict:
        """Convert to serializable dictionary."""
        data = asdict(self)
        # Convert datetime objects to ISO format strings for JSON serialization
        if data["last_updated"] is not None and isinstance(data["last_updated"], datetime):
            data["last_updated"] = data["last_updated"].isoformat()
        if data["created_at"] is not None and isinstance(data["created_at"], datetime):
            data["created_at"] = data["created_at"].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "ActronUser":
        """Create from dictionary."""
        # Convert ISO format strings back to datetime objects
        if data.get("last_updated"):
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)