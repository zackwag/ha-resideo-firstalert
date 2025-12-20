# First Alert by Resideo - Home Assistant Integration

A custom Home Assistant integration for First Alert Safe & Sound smoke/CO detectors connected via the Resideo platform.

## Supported Devices

- First Alert Safe & Sound Smart Smoke/CO Alarm (SMCO600NVACA)
- Other Resideo-connected First Alert devices may also work

## Features

- **Smoke Alarm Detection** - Binary sensor that triggers when smoke is detected
- **CO Alarm Detection** - Binary sensor that triggers when carbon monoxide is detected
- **Battery Status** - Monitor battery health (good/low)
- **Power Source** - See if device is on AC or battery power
- **Connectivity Status** - Know if your detector is online
- **Malfunction Detection** - Get alerts if the device has issues
- **WiFi Signal Strength** - Diagnostic sensor showing signal quality
- **Last Seen** - Track when the device last communicated

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

### Getting Your Refresh Token

This integration requires a refresh token from the Resideo API. To obtain one:

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

### Adding the Integration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "First Alert by Resideo"
3. Enter your refresh token
4. Your devices will be automatically discovered

## Entities Created

For each smoke detector, the following entities are created:

### Binary Sensors
| Entity | Description | Device Class |
|--------|-------------|--------------|
| Smoke Alarm | On when smoke is detected | `smoke` |
| CO Alarm | On when CO is detected | `co` |
| Malfunction | On when device has a problem | `problem` |
| Connectivity | On when device is online | `connectivity` |
| Battery Low | On when battery is low | `battery` |

### Sensors
| Entity | Description |
|--------|-------------|
| Battery Status | `good` or `low` |
| Power Source | `ac` or `battery` |
| Smoke Status | `idle` or `alarm` |
| CO Status | `idle` or `alarm` |
| WiFi Signal Strength | Signal strength in dBm (diagnostic) |
| WiFi Network | Connected SSID (diagnostic) |
| Last Seen | Timestamp of last communication |
| Firmware Version | Device firmware (diagnostic) |

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

## Troubleshooting

### "Invalid authentication" error
Your refresh token may have expired. Capture a new one from the app.

### "Unable to connect" error
Check your internet connection and verify the Resideo API is accessible.

### Devices not showing
Make sure your devices are properly set up in the First Alert app and are online.

## Technical Details

- **Polling Interval**: 60 seconds (configurable)
- **API Base URL**: `https://api.resideo.com`
- **Authentication**: OAuth 2.0 with refresh tokens

## Privacy Note

This integration communicates with Resideo's cloud servers. Your device data passes through their infrastructure. The integration stores only the refresh token locally.

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.

## Disclaimer

This is an unofficial integration and is not affiliated with, endorsed by, or supported by First Alert or Resideo. Use at your own risk.
