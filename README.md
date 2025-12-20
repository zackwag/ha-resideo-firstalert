# First Alert by Resideo - Home Assistant Integration

A custom Home Assistant integration for First Alert Safe & Sound smoke/CO detectors connected via the Resideo platform.

## Supported Devices

- First Alert Safe & Sound Smart Smoke/CO Alarm (SMCO600NVACA)
- Other Resideo-connected First Alert devices may also work

## Features

- **Easy Setup** - Login with your Resideo email and password directly
- **Smoke Alarm Detection** - Binary sensor that triggers when smoke is detected
- **CO Alarm Detection** - Binary sensor that triggers when carbon monoxide is detected
- **Battery Monitoring** - Track battery status and get low battery alerts
- **Power Source** - See if device is on AC or battery power
- **Connectivity Status** - Know if your detector is online
- **Malfunction Detection** - Get alerts if the device has issues
- **Test Mode & Silence Status** - Monitor when detectors are in test mode or silenced
- **Early Warning** - Track early warning feature status
- **End of Life Alerts** - Know when your detector needs replacement
- **Comprehensive Fault Detection** - Monitor various fault conditions
- **Configurable Polling** - Adjust update interval from 5 seconds to 1 hour

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → Custom repositories
3. Add `https://github.com/aidenmitchell/ha-resideo-firstalert` with category "Integration"
4. Search for "First Alert by Resideo" and install
5. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/resideo_firstalert` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

### Authentication

When adding the integration, you have two options:

#### Option 1: Login with Email & Password (Recommended)

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "First Alert by Resideo"
3. Select **"Login with email and password"**
4. Enter your Resideo account credentials (same as the First Alert app)
5. Your devices will be automatically discovered

#### Option 2: Manual Token Entry

If you prefer, you can manually obtain and enter a refresh token:

1. **Install a network proxy** like [Proxyman](https://proxyman.io/) (macOS/iOS) or [mitmproxy](https://mitmproxy.org/)

2. **Configure SSL interception** for `login.resideo.com`

3. **Log into the First Alert app** on your phone while capturing traffic

4. **Look for the request** to `POST https://login.resideo.com/oauth/token`

5. **Find the `refresh_token`** in the response JSON:
   ```json
   {
     "access_token": "...",
     "refresh_token": "THIS_IS_YOUR_TOKEN",
     "expires_in": 3600,
     "token_type": "Bearer"
   }
   ```

6. In Home Assistant, select **"Enter refresh token manually"** and paste your token

### Options

After setup, you can configure the integration via **Settings** → **Devices & Services** → **First Alert by Resideo** → **Configure**:

- **Settings** - Adjust the polling interval (5-3600 seconds, default: 60)
- **Update refresh token** - Enter a new token if needed without recreating the integration

## Entities Created

For each smoke detector, the following entities are created:

### Binary Sensors

| Entity | Description | Device Class | Default |
|--------|-------------|--------------|---------|
| Smoke Alarm | On when smoke is detected | `smoke` | Enabled |
| CO Alarm | On when CO is detected | `co` | Enabled |
| Malfunction | On when device has a problem | `problem` | Enabled |
| Connectivity | On when device is online | `connectivity` | Enabled |
| Battery Low | On when battery is low | `battery` | Enabled |
| Test Mode | On when device is in test mode | `running` | Enabled |
| Silenced | On when alarm is silenced | `running` | Enabled |
| End of Life | On when device needs replacement | `problem` | Enabled |
| Early Warning | On when early warning is enabled | - | Enabled |
| Supervision Healthy | On when supervision is healthy | - | Disabled |
| General Fault | On when general fault detected | `problem` | Disabled |
| E2 Fault | On when E2 fault detected | `problem` | Disabled |
| Photo Sensor Fault | On when photo sensor fault detected | `problem` | Disabled |
| Drift Malfunction | On when drift malfunction detected | `problem` | Disabled |
| CO Sensor Fault | On when CO sensor fault detected | `problem` | Disabled |
| Temperature Sensor Fault | On when temp sensor fault detected | `problem` | Disabled |
| Voice Module Fault | On when voice module fault detected | `problem` | Disabled |
| Radio Fault | On when radio fault detected | `problem` | Disabled |

### Sensors

| Entity | Description | Default |
|--------|-------------|---------|
| Battery Status | `good` or `low` | Enabled |
| Power Source | `ac` or `battery` | Enabled |
| Smoke Status | `idle` or `alarm` | Enabled |
| CO Status | `idle` or `alarm` | Enabled |
| Test Status | `idle` or `testing` | Enabled |
| Silence Status | `not_silenced` or `silenced` | Enabled |
| End of Life Status | `no` or `yes` | Enabled |
| Language | Device language setting | Enabled |
| Room | Room number setting | Disabled |
| WiFi Signal Strength | Signal strength in dBm | Disabled |
| WiFi Network | Connected SSID | Disabled |
| Last Seen | Timestamp of last communication | Disabled |
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

### "Invalid email or password" error
Double-check your credentials. These are the same as your First Alert / Resideo app login.

### "Authentication failed" error
Your refresh token may have expired. Use the **Configure** option to update your token, or re-authenticate with email/password.

### "Unable to connect" error
Check your internet connection and verify the Resideo API is accessible.

### Devices not showing
Make sure your devices are properly set up in the First Alert app and are online.

### Token Expiration
- **Access tokens** expire hourly and are automatically refreshed
- **Refresh tokens** expire after ~30 days. When this happens, Home Assistant will prompt you to re-authenticate

## Technical Details

- **Polling Interval**: 60 seconds (configurable from 5-3600 seconds)
- **API Base URL**: `https://api.resideo.com`
- **Authentication**: OAuth 2.0 with PKCE via Auth0

## Privacy Note

This integration communicates with Resideo's cloud servers. Your device data passes through their infrastructure. The integration stores only the refresh token locally - your email and password are not stored.

## License

MIT License - See LICENSE file for details.

## Local Development

### Prerequisites

- Docker and Docker Compose
- A Resideo account with First Alert devices

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/aidenmitchell/ha-resideo-firstalert.git
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

4. Open http://localhost:8123 in your browser

5. Complete the Home Assistant onboarding, then add the integration:
   - Settings → Devices & Services → Add Integration
   - Search "First Alert by Resideo"
   - Login with your email and password

### Development Workflow

The `custom_components` folder is mounted directly into the container, so changes to the integration code take effect after restarting Home Assistant:

```bash
# Restart to pick up code changes
docker compose restart

# View logs
docker compose logs -f homeassistant

# Stop
docker compose down
```

### Debug Logging

The example configuration enables debug logging for the integration. View logs with:
```bash
docker compose logs -f homeassistant 2>&1 | grep resideo_firstalert
```

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.

## Disclaimer

This is an unofficial integration and is not affiliated with, endorsed by, or supported by First Alert or Resideo. Use at your own risk.
