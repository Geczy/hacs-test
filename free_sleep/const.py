"""Constants for the Free Sleep integration."""
from typing import Final

DOMAIN: Final = "free_sleep"

# Configuration
CONF_HOST: Final = "host"

# Update intervals (in seconds)
UPDATE_INTERVAL_DEVICE_STATUS: Final = 5
UPDATE_INTERVAL_BASE_CONTROL: Final = 10
UPDATE_INTERVAL_VITALS: Final = 60

# API Endpoints
ENDPOINT_DEVICE_STATUS: Final = "/api/deviceStatus"
ENDPOINT_SETTINGS: Final = "/api/settings"
ENDPOINT_SCHEDULES: Final = "/api/schedules"
ENDPOINT_BASE_CONTROL: Final = "/api/base-control"
ENDPOINT_BASE_CONTROL_PRESET: Final = "/api/base-control/preset"
ENDPOINT_VITALS_SUMMARY: Final = "/api/metrics/vitals/summary"
ENDPOINT_SLEEP: Final = "/api/metrics/sleep"
ENDPOINT_VERSION: Final = "/api/version"
ENDPOINT_WATER_LEVEL: Final = "/api/waterLevel"
ENDPOINT_SNOOZE: Final = "/api/deviceStatus/snooze"
ENDPOINT_DISMISS_PRIME: Final = "/api/deviceStatus/dismissPrimeNotification"

# Temperature limits (Fahrenheit)
MIN_TEMPERATURE_F: Final = 55
MAX_TEMPERATURE_F: Final = 110

# Base control limits
BASE_HEAD_MIN: Final = 0
BASE_HEAD_MAX: Final = 60
BASE_FEET_MIN: Final = 0
BASE_FEET_MAX: Final = 45
BASE_FEED_RATE_MIN: Final = 30
BASE_FEED_RATE_MAX: Final = 100
BASE_FEED_RATE_DEFAULT: Final = 50

# LED brightness limits
LED_BRIGHTNESS_MIN: Final = 0
LED_BRIGHTNESS_MAX: Final = 100

# Sides
SIDE_LEFT: Final = "left"
SIDE_RIGHT: Final = "right"

# Base presets
BASE_PRESET_FLAT: Final = "flat"
BASE_PRESET_SLEEP: Final = "sleep"
BASE_PRESET_RELAX: Final = "relax"
BASE_PRESET_ZERO_GRAVITY: Final = "zero_gravity"
BASE_PRESET_ANTI_SNORE: Final = "anti_snore"

BASE_PRESETS: Final = {
    BASE_PRESET_FLAT: {"head": 0, "feet": 0, "feedRate": 50},
    BASE_PRESET_SLEEP: {"head": 10, "feet": 5, "feedRate": 50},
    BASE_PRESET_RELAX: {"head": 30, "feet": 15, "feedRate": 50},
    BASE_PRESET_ZERO_GRAVITY: {"head": 30, "feet": 30, "feedRate": 50},
    BASE_PRESET_ANTI_SNORE: {"head": 20, "feet": 0, "feedRate": 50},
}

# Services
SERVICE_SET_SCHEDULE: Final = "set_schedule"
SERVICE_SET_ALARM: Final = "set_alarm"
SERVICE_SET_BASE_POSITION: Final = "set_base_position"
SERVICE_SET_BASE_PRESET: Final = "set_base_preset"
SERVICE_ENABLE_AWAY_MODE: Final = "enable_away_mode"
SERVICE_DISABLE_AWAY_MODE: Final = "disable_away_mode"
SERVICE_PRIME_POD: Final = "prime_pod"

# Device info
MANUFACTURER: Final = "Free Sleep"
DEFAULT_NAME: Final = "Free Sleep Pod"

