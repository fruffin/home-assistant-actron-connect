"""Constants for the actron_ultima integration."""

# DO NOT CHANGE THESE
from homeassistant.const import UnitOfTemperature

DOMAIN = "actron_ultima"
ATTR_INSIDE_TEMPERATURE = "inside_temperature"
CONF_SERVICE_CONFIGURATION = "service_configuration"
CONF_USER = "user"

# You can change these values to best fit your device and needs
DEVICE_TARGET_TEMPERATURE_STEP = 0.5
DEVICE_MIN_TEMP = 16
DEVICE_MAX_TEMP = 30
DEVICE_TEMP_UNIT = UnitOfTemperature.CELSIUS
DEVICE_UPDATE_SKIP_SECONDS = 20