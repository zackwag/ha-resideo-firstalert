"""Constants for the First Alert by Resideo integration."""

from resideo_firstalert_api import (
    ALARM_STATE_ALARM,
    ALARM_STATE_EOL_YES,
    ALARM_STATE_LOW,
    ALARM_STATE_NONE,
    ALARM_STATE_SILENCED,
    ALARM_STATE_TESTING,
    ALARM_STATE_UNKNOWN,
    BATTERY_STATE_MAP,
    CO_ALARM_STATES,
    POWER_STATE_MAP,
    SMOKE_ALARM_STATES,
)

DOMAIN = "resideo_firstalert"

# Update interval
DEFAULT_SCAN_INTERVAL = 60  # seconds
MIN_SCAN_INTERVAL = 5  # seconds
MAX_SCAN_INTERVAL = 3600  # seconds (1 hour)

# Config keys
CONF_REFRESH_TOKEN = "refresh_token"
CONF_SCAN_INTERVAL = "scan_interval"

__all__ = [
    "ALARM_STATE_ALARM",
    "ALARM_STATE_EOL_YES",
    "ALARM_STATE_LOW",
    "ALARM_STATE_NONE",
    "ALARM_STATE_SILENCED",
    "ALARM_STATE_TESTING",
    "ALARM_STATE_UNKNOWN",
    "BATTERY_STATE_MAP",
    "CO_ALARM_STATES",
    "CONF_REFRESH_TOKEN",
    "CONF_SCAN_INTERVAL",
    "DEFAULT_SCAN_INTERVAL",
    "DOMAIN",
    "MAX_SCAN_INTERVAL",
    "MIN_SCAN_INTERVAL",
    "POWER_STATE_MAP",
    "SMOKE_ALARM_STATES",
]
