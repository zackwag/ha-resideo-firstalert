"""Constants for the First Alert by Resideo integration."""

from datetime import timedelta

DOMAIN = "resideo_firstalert"

# OAuth Configuration
OAUTH_CLIENT_ID = "SRmiA7CaYi1JgivDZdzzoZu4X5VBogGt"
OAUTH_TOKEN_URL = "https://login.resideo.com/oauth/token"
OAUTH_AUTHORIZE_URL = "https://login.resideo.com/authorize"
OAUTH_AUDIENCE = "https://resideo-prod.auth0.com/api/v2/"

# API Configuration
API_BASE_URL = "https://api.resideo.com"
API_ACCOUNTS_ENDPOINT = "/ris-public-api/api/v1/accounts"
API_DEVICE_STATE_ENDPOINT = "/ris-public-api/api/v2/devices/smokeDetectors/{device_id}/state"

# Update interval
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

# Config keys
CONF_REFRESH_TOKEN = "refresh_token"
CONF_ACCESS_TOKEN = "access_token"
CONF_TOKEN_EXPIRY = "token_expiry"

# Device types
DEVICE_TYPE_SMOKE_DETECTOR = "SmokeDetector"

# Alarm states
ALARM_STATE_IDLE = "idle"
ALARM_STATE_ALARM = "alarm"
ALARM_STATE_GOOD = "good"
ALARM_STATE_LOW = "low"
ALARM_STATE_NONE = "none"
ALARM_STATE_AC = "ac"
ALARM_STATE_BATTERY = "battery"

# Platforms
PLATFORMS = ["binary_sensor", "sensor"]
