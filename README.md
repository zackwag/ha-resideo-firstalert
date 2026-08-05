# First Alert by Resideo — Home Assistant HACS Integration

A HACS custom integration for First Alert Safe & Sound smoke/CO detectors, reverse-engineered from the First Alert app's Resideo/Auth0 OAuth flow and REST API. Combines cloud polling with real-time SignalR push notifications for near-instant alarm detection.

## Features

- **Full alarm state detection** — recognizes all alarm variants from the official app, including early warning, interconnect, and direct alarm states for both smoke and CO
- **Real-time push notifications** — maintains a SignalR WebSocket connection to the Resideo notification service, triggering an immediate refresh when device state changes
- **Event entities** — fires typed Home Assistant events on state changes (smoke alarm, CO alarm, battery low, AC power loss, etc.) for use in automations
- **Repairs integration** — raises persistent repair issues for devices that are offline, faulted, or at end-of-life
- **Power & battery normalization** — handles transitional power states (`acToDc`, `acLoss`, `acRestored`, etc.) and extended battery states (`replace`, `critical`)

## Entities

For each smoke/CO detector the integration creates:

### Binary Sensors

| Entity | Description | Default |
| -------- | ------------- | --------- |
| Smoke Alarm | On when smoke is detected (includes early warning and interconnect states) | Enabled |
| CO Alarm | On when CO is detected (includes early warning and interconnect states) | Enabled |
| Malfunction | On when device has a problem | Enabled |
| Connectivity | On when device is online | Enabled |
| Battery Low | On when battery is low, needs replacement, or is critical | Enabled |
| Test Mode | On when device is in test mode | Enabled |
| Silenced | On when alarm is silenced | Enabled |
| End of Life | On when device needs replacement (includes `eolWarning` and `expired`) | Enabled |
| Early Warning | On when early warning is enabled | Enabled |
| Connectivity (Computed) | On when device is online, per the API's computed status | Disabled |
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
| -------- | ------------- | --------- |
| Battery Status | `good`, `low`, `replace`, or `critical` | Enabled |
| Power Source | `ac`, `battery`, or `dc` (transitional states normalized) | Enabled |
| Smoke Status | All app states: `idle`, `alarm`, `smokeAlarm`, `smokeEarlyWarning`, `smokeInterconnectAlarm`, `smokeEarlyWarningInterconnectAlarm` | Enabled |
| CO Status | All app states: `idle`, `alarm`, `coAlarm`, `coEarlyWarning`, `carbonMonoxideAlarm`, `carbonMonoxideEarlyWarning`, `carbonMonoxideInterconnectAlarm`, `carbonMonoxideEarlyWarningInterconnectAlarm` | Enabled |
| Test Status | `idle` or `testing` | Enabled |
| Silence Status | `not_silenced` or `silenced` | Enabled |
| End of Life Status | `no`, `yes`, `eolWarning`, or `expired` | Enabled |
| Language | Device language setting | Enabled |
| Last Seen | Timestamp of last communication | Enabled |
| Registration Status | Device registration status (e.g. `Registered`) | Disabled |
| Sync Status | Cloud data sync status (e.g. `Completed`) | Disabled |
| Debug Level | Device's configured debug log level | Disabled |
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

### Event Entity

Each device has an **Alarm Events** event entity that fires typed HA events on state changes:

| Event Type | Trigger |
| ------------ | --------- |
| `smoke_alarm` | Smoke alarm activated |
| `smoke_early_warning` | Smoke early warning detected |
| `smoke_interconnect_alarm` | Smoke alarm from interconnected device |
| `co_alarm` | CO alarm activated |
| `co_early_warning` | CO early warning detected |
| `co_interconnect_alarm` | CO alarm from interconnected device |
| `battery_low` | Battery level low |
| `battery_replace` | Battery critical / needs replacement |
| `power_ac_loss` | AC power lost |
| `power_ac_restored` | AC power restored |
| `malfunction` | Device malfunction detected |
| `end_of_life` | Device reached end of life |
| `silence` | Alarm silenced |
| `test` | Self-test initiated |

Events include `state` and `event_source` data attributes. Events only fire on state *changes* — the initial load on startup does not trigger events.

### Repairs

The integration raises repair issues in **Settings → System → Repairs** for persistent device problems:

| Issue | Condition |
| ------- | ----------- |
| Device offline | Offline for 3+ consecutive polls |
| End of life | Immediately on EOL/warning/expired |
| Persistent fault | Any fault flag active for 2+ consecutive polls |

Repairs auto-resolve when the condition clears.

## Tested Devices

| Device | Model |
|--------|-------|
| First Alert Safe & Sound Smart Smoke/CO Alarm (Wired and Wireless) | SMCO600NV/AC |

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

> [!IMPORTANT]
> **Email/password login no longer works.** Resideo has enabled a captcha on
> its Auth0 login endpoint, which rejects the request before your credentials
> are ever checked — so a correct password fails exactly like a wrong one:
>
> ```
> POST https://login.resideo.com/usernamepassword/login
> HTTP 401  {"name":"invalid_captcha","description":"Invalid captcha value"}
> ```
>
> This cannot be fixed inside the integration; the captcha exists specifically
> to block non-browser clients. Use **Enter refresh token manually** instead.

1. Go to **Settings → Devices & Services → Add Integration → First Alert by Resideo**
2. Choose **Enter refresh token manually** and supply a token — see
   [Manual Token Entry](#manual-token-entry) below
3. Your devices are discovered automatically

## Manual Token Entry

Since email/password login is captcha-blocked, this is the supported way to
authenticate. There are two ways to obtain a token.

### Option A — browser login (no proxy needed)

The captcha only blocks *scripted* logins; a real browser can complete it.

1. Build an Auth0 authorize URL for the app client, with PKCE (`code_challenge`,
   `code_challenge_method=S256`) and `redirect_uri`
   `com.resideo.firstalert://login.resideo.com/ios/com.resideo.firstalert/callback`
2. Open it in a desktop browser, log in, and solve the captcha
3. The browser will fail to follow the `com.resideo.firstalert://` redirect —
   that is the success case. Copy the whole failed URL and take its `code`
   parameter (it is also recorded in browser history)
4. Exchange the code at `POST https://login.resideo.com/oauth/token` with
   `grant_type=authorization_code` and your `code_verifier`

Authorization codes expire within about 30 seconds, so do steps 3-4 promptly.

### Option B — capture from the app

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
| -------- | --------- | -------------- |
| Update interval | 60s | How often to poll the Resideo API for device state (5–3600 seconds). |
| Update refresh token | — | Enter a new refresh token if your current one has expired, without recreating the integration. |

## Requirements

- [`python-dateutil`](https://pypi.org/project/python-dateutil/) `>= 2.8.2` (installed automatically) — used to parse device timestamps.
- Home Assistant 2024.1.0 or newer

## Notes

- **Refresh token rotation** — Resideo occasionally rotates your refresh token when the access token is renewed. The integration detects this automatically and saves the new token to the config entry; no action is needed on your part.
- **Token expiry** — access tokens expire hourly and are refreshed automatically in the background. If the refresh token itself expires (~30 days) or is revoked, Home Assistant will prompt you to re-authenticate from the integration card.
- **Using credentials for the wrong account** — if you reauthenticate, or use **Update refresh token**, with credentials for a different Resideo account than the one originally configured, the integration detects the mismatch and rejects it instead of silently repointing the entry at a different account.
- **Polling + real-time push** — the integration polls on your configured interval as a baseline, but also maintains a SignalR WebSocket connection to the Resideo notification service. When a device state change occurs, the server pushes an event and the integration immediately refreshes — so alarms are typically detected within seconds, not on the next poll. The device list itself (used to detect new devices) is refreshed at most once every 5 minutes regardless of your polling interval.
- **New devices** — a detector added to your Resideo account after setup is picked up automatically (within the 5-minute device-list refresh above); there's no need to remove and re-add the integration.
- **Removed devices** — once a detector no longer appears in your Resideo account, its device page in Home Assistant can be manually deleted (three-dot menu → **Delete**). Devices still reporting state can't be deleted this way.
- **Unknown data defaults to safe** — if the Resideo API omits or returns an unrecognized value for an alarm field, the corresponding binary sensor treats it as the safe/off state rather than reporting a false alarm.
- **Availability** — entities go unavailable if a device drops off the Resideo cloud or a poll for it fails, and recover automatically once a subsequent poll succeeds.
- **Last-changed timestamps** — the smoke, CO, malfunction, battery, test, silenced, and end-of-life binary sensors expose a `last_changed` attribute with the timestamp the API last reported for that state, useful for confirming whether (and when) an event actually arrived from the API. They also expose an `event_source` attribute (`self`, `node`, or `remote`) indicating whether the event originated from the device itself, a mesh node, or a remote interconnect.
- **Suggested Area** — each detector's Resideo location name (e.g. "Home", or a second property's name if your account has more than one) is passed to Home Assistant as a suggested Area on first setup, so devices land somewhere sensible without manual sorting.

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

### Using Event Entities (Interconnect Detection)

```yaml
automation:
  - alias: "Interconnect Smoke Alarm"
    trigger:
      - platform: state
        entity_id: event.living_room_detector_alarm_events
        attribute: event_type
        to: "smoke_interconnect_alarm"
    action:
      - service: notify.mobile_app
        data:
          title: "INTERCONNECT SMOKE ALARM"
          message: "A connected detector triggered the smoke alarm in Living Room"
          data:
            priority: high
            ttl: 0
```

## Troubleshooting

### Diagnostics

On the device page in Home Assistant, click the three-dot menu → **Download diagnostics**. The report includes the parsed and raw device state for each detector, plus current options. The refresh token, access token, and WiFi SSID are automatically redacted. Attach this when opening an issue.

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

4. Open <http://localhost:8123>, complete onboarding, then add the integration via **Settings → Devices & Services → Add Integration → First Alert by Resideo**

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

### Running Tests

The test suite covers `api.py` and `auth.py` (the parts of the integration with no Home Assistant dependency) with mocked HTTP calls:

```bash
pip install -r requirements-test.txt
PYTHONPATH=custom_components python -m pytest tests/ -v
```

## Privacy Note

This integration communicates with Resideo's cloud servers, so your device data passes through their infrastructure. Only the refresh token is stored locally — your email and password are not stored.

## Credits

This project was originally started by [Aiden Mitchell](https://github.com/aidenmitchell), who did the initial reverse-engineering of the Resideo API and built the first version of this integration. It hadn't been updated in about 7 months, so this fork has picked up active development.

## License

MIT License — see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is an unofficial integration and is not affiliated with, endorsed by, or supported by First Alert or Resideo. Use at your own risk.
