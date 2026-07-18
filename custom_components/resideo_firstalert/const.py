"""Constants for the First Alert by Resideo integration."""

DOMAIN = "resideo_firstalert"

# OAuth Configuration
OAUTH_CLIENT_ID = "SRmiA7CaYi1JgivDZdzzoZu4X5VBogGt"
OAUTH_TOKEN_URL = "https://login.resideo.com/oauth/token"

# API Configuration
API_BASE_URL = "https://api.resideo.com"
API_ACCOUNTS_ENDPOINT = "/ris-public-api/api/v1/accounts"
API_DEVICE_STATE_ENDPOINT = "/ris-public-api/api/v2/devices/smokeDetectors/{device_id}/state"

# Update interval
DEFAULT_SCAN_INTERVAL = 60  # seconds
MIN_SCAN_INTERVAL = 5  # seconds
MAX_SCAN_INTERVAL = 3600  # seconds (1 hour)

# Config keys
CONF_REFRESH_TOKEN = "refresh_token"
CONF_SCAN_INTERVAL = "scan_interval"

# Alarm states
ALARM_STATE_ALARM = "alarm"
ALARM_STATE_LOW = "low"
ALARM_STATE_NONE = "none"
ALARM_STATE_UNKNOWN = "unknown"
ALARM_STATE_SILENCED = "silenced"
ALARM_STATE_EOL_YES = "yes"
ALARM_STATE_TESTING = "testing"
