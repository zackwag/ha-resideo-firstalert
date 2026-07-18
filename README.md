# First Alert by Resideo — Home Assistant HACS Integration

A HACS custom integration for First Alert Safe & Sound smoke/CO detectors, reverse-engineered from the First Alert app's Resideo/Auth0 OAuth flow and REST API. Polls the Resideo cloud for device state — there is no push channel available from the platform.

## Entities

For each smoke/CO detector the integration creates:

### Binary Sensors

| Entity | Description | Default |
|--------|-------------|---------|
| Smoke Alarm | On when smoke is detected | Enabled |
| CO Alarm | On when CO is detected | Enabled |
| Malfunction | On when device has a problem | Enabled |
| Connectivity | On when device is online | Enabled |
| Battery Low | On when battery is low | Enabled |
| Test Mode | On when device is in test mode | Enabled |
| Silenced | On when alarm is silenced | Enabled |
| End of Life | On when device needs replacement | Enabled |
| Early Warning | On when early warning is enabled | Enabled |
| Supervision Healthy | On when supervision is healthy | Disabled |
| General Fault | On when general fault detected | Disabled |
| E2 Fault | On when E2 fault detected | Disabled |
| Photo Sensor Fault | On when photo sensor fault detected | Disabled |
| Drift Malfunction | On when drift malfunction detected | Disabled |
| CO Sensor Fault | On when CO sensor fault detected | Disabled |
| Temperature Sensor Fault | On when temp sensor fault detected | Disabled |
| Voice Module Fault | On when voice module fault detected | Disabled |
| Radio Fault | On when radio fault detected | Disabled |

### Sensors

| Entity | Description | Default |
|--------|-------------|---------|
| Battery Status | `good` or `low` | Enabled |
| Power Source | `ac`, `battery`, or `dc` | Enabled |
| Smoke Status | `idle` or `alarm` | Enabled |
| CO Status | `idle` or `alarm` | Enabled |
| Test Status | `idle` or `testing` | Enabled |
| Silence Status | `not_silenced` or `silenced` | Enabled |
| End of Life Status | `no` or `yes` | Enabled |
| Language | Device language setting | Enabled |
| Last Seen | Timestamp of last communication | Enabled |
| Room | Room number setting | Disabled |
| WiFi Signal Strength | Signal strength in dBm | Disabled |
| WiFi Network | Connected SSID | Disabled |
| Firmware Version | Device firmware | Disabled |
| Firmware (Exec Core) | Exec core firmware version | Disabled |
| Firmware (Sensor Core) | Sensor core firmware version | Disabled |
| Hardware Version (E2C) | E2C hardware version | Disabled |
| Hardware Version (Exec Core) | Exec core hardware version | Disabled |
| Hardware Version (Sensor Core) | Sensor core hardware version | Disabled |
| Voice File Version | Voice file version | Disabled |
| Running Hours | Total running hours | Disabled |
| Registration Date | When device was registered | Disabled |
| Last Firmware Update | Last firmware update timestamp | Disabled |

## Tested Devices

| Device | Model |
|--------|-------|
| First Alert Safe & Sound Smart Smoke/CO Alarm | SMCO600NVACA |

Other Resideo-connected First Alert devices may work but have not been verified. If yours does, please open an issue or PR to add it to this list.

## Installation

### HACS (recommended)

1. In HA, go to **HACS → Integrations**
2. Click the three-dot menu (top right) → **Custom repositories**
3. Enter `https://github.com/zackwag/ha-resideo-firstalert` and set category to **Integration**
4. Click **Add**, then find and install **First Alert by Resideo**
5. Restart Home Assistant

### Manual

Copy `custom_components/resideo_firstalert/` into your HA `config/custom_components/` directory, then restart.

## Setup

1. Go to **Settings → Devices & Services → Add Integration → First Alert by Resideo**
2. Choose **Login with email and password** (recommended) and enter your Resideo account credentials — the same ones used in the First Alert app
3. Your devices are discovered automatically

If you'd rather not enter your account password, choose **Enter refresh token manually** instead and see [Manual Token Entry](#manual-token-entry) below.

## Manual Token Entry

If you prefer not to use email/password login, you can supply a refresh token directly:

1. Install a network proxy such as [Proxyman](https://proxyman.io/) (macOS/iOS) or [mitmproxy](https://mitmproxy.org/)
2. Configure SSL interception for `login.resideo.com`
3. Log into the First Alert app on your phone while capturing traffic
4. Find the request to `POST https://login.resideo.com/oauth/token` and copy the `refresh_token` field from the response:
   ```json
   {
     "access_token": "...",
     "refresh_token": "THIS_IS_YOUR_TOKEN",
     "expires_in": 3600,
     "token_type": "Bearer"
   }
   ```
5. In Home Assistant, select **Enter refresh token manually** and paste the token

## Options

After setup, click **Configure** on the integration card to change:

| Option | Default | Description |
|--------|---------|--------------|
| Update interval | 60s | How often to poll the Resideo API for device state (5–3600 seconds). |
| Update refresh token | — | Enter a new refresh token if your current one has expired, without recreating the integration. |

## Requirements

- [`python-dateutil`](https://pypi.org/project/python-dateutil/) `>= 2.8.2` (installed automatically) — used to parse device timestamps.
- Home Assistant 2024.1.0 or newer

## Notes

- **Refresh token rotation** — Resideo occasionally rotates your refresh token when the access token is renewed. The integration detects this automatically and saves the new token to the config entry; no action is needed on your part.
- **Token expiry** — access tokens expire hourly and are refreshed automatically in the background. If the refresh token itself expires (~30 days) or is revoked, Home Assistant will prompt you to re-authenticate from the integration card.
- **Polling, not push** — the Resideo API has no real-time push channel, so all state comes from polling on the configured interval. A shorter interval detects a real alarm faster but makes more API calls.
- **New devices** — a detector added to your Resideo account after setup is picked up automatically on the next poll; there's no need to remove and re-add the integration.
- **Unknown data defaults to safe** — if the Resideo API omits or returns an unrecognized value for an alarm field, the corresponding binary sensor treats it as the safe/off state rather than reporting a false alarm.
- **Availability** — entities go unavailable if a device drops off the Resideo cloud or a poll for it fails, and recover automatically once a subsequent poll succeeds.

## Example Automations

### Alert on Smoke Detection
```yaml
automation:
  - alias: "Smoke Alarm Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_detector_smoke_alarm
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "SMOKE DETECTED!"
          message: "Smoke alarm triggered in Living Room"
          data:
            priority: high
            ttl: 0
```

### Alert on CO Detection
```yaml
automation:
  - alias: "CO Alarm Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_detector_co_alarm
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "CARBON MONOXIDE DETECTED!"
          message: "CO alarm triggered - evacuate immediately!"
          data:
            priority: high
            ttl: 0
```

### Low Battery Alert
```yaml
automation:
  - alias: "Smoke Detector Low Battery"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_detector_battery_low
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Low Battery"
          message: "Living Room smoke detector battery is low"
```

### End of Life Alert
```yaml
automation:
  - alias: "Smoke Detector End of Life"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_detector_end_of_life
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Detector Replacement Needed"
          message: "Living Room smoke detector has reached end of life and should be replaced"
```

## Troubleshooting

### Common Errors

- **"Invalid email or password"** — double-check your credentials; these are the same as your First Alert / Resideo app login.
- **"Authentication failed"** — your refresh token may have expired. Use **Configure** to update it, or re-authenticate with email/password.
- **"Unable to connect"** — check your internet connection and verify the Resideo API is accessible.
- **Devices not showing** — make sure your devices are set up in the First Alert app and are online.

### Debug logging

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.resideo_firstalert: debug
```

## Removing the Integration

1. Go to **Settings → Devices & Services**
2. Find **First Alert by Resideo** and click on it
3. Click the three-dot menu → **Delete**

All entities and device data are removed. No additional cleanup is required.

## Local Development

### Prerequisites

- Docker and Docker Compose
- A Resideo account with First Alert devices

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/zackwag/ha-resideo-firstalert.git
   cd ha-resideo-firstalert
   ```
2. Create the config file:
   ```bash
   cp config/configuration.yaml.example config/configuration.yaml
   ```
3. Start Home Assistant:
   ```bash
   docker compose up -d
   ```
4. Open http://localhost:8123, complete onboarding, then add the integration via **Settings → Devices & Services → Add Integration → First Alert by Resideo**

### Development Workflow

The `custom_components` folder is mounted directly into the container, so code changes take effect after a restart:

```bash
# Restart to pick up code changes
docker compose restart

# View logs
docker compose logs -f homeassistant

# Stop
docker compose down
```

## Privacy Note

This integration communicates with Resideo's cloud servers, so your device data passes through their infrastructure. Only the refresh token is stored locally — your email and password are not stored.

## License

MIT License — see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is an unofficial integration and is not affiliated with, endorsed by, or supported by First Alert or Resideo. Use at your own risk.
