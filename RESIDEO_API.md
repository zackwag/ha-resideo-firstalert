# First Alert by Resideo API Documentation

This document describes the API used by the First Alert by Resideo mobile app to communicate with smoke/CO detectors.

## Authentication

The API uses **OAuth 2.0 with PKCE** via **Auth0**.

### OAuth Configuration

| Parameter | Value |
|-----------|-------|
| Auth Domain | `login.resideo.com` |
| Client ID | `SRmiA7CaYi1JgivDZdzzoZu4X5VBogGt` |
| Audience | `https://resideo-prod.auth0.com/api/v2/` |
| Scopes | `openid profile email offline_access` |

### Token Refresh

Access tokens expire after 1 hour. Use the refresh token to get new access tokens:

```http
POST https://login.resideo.com/oauth/token
Content-Type: application/json

{
  "grant_type": "refresh_token",
  "refresh_token": "<refresh_token>",
  "client_id": "SRmiA7CaYi1JgivDZdzzoZu4X5VBogGt"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "id_token": "eyJ...",
  "scope": "openid profile email offline_access",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

---

## API Endpoints

Base URL: `https://api.resideo.com`

All requests require:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: application/json
```

### Get Account Information

```http
GET /ris-public-api/api/v1/accounts
```

**Response:**
```json
{
  "data": {
    "id": "VXNlcjow...",
    "firstName": "John",
    "lastName": "Doe",
    "contactEmail": "user@example.com",
    "countryCode": "US",
    "locale": "en_US",
    "consumerUsers": [
      {
        "id": "Q29uc3VtZXJVc2VyOj...",
        "role": "ADMIN",
        "consumerAccount": {
          "id": "Q29uc3VtZXJBY2NvdW50Oj...",
          "locations": [
            {
              "id": "Q29uc3VtZXJEZXZpY2VMb2NhdGlvbjo...",
              "name": "Home",
              "address": {
                "addressLine1": "123 Main St",
                "city": "Anytown",
                "stateProvinceRegionCode": "CA",
                "zipPostalCode": "90210",
                "countryCode": "US"
              },
              "geoCoordinate": {
                "latitude": 34.0901,
                "longitude": -118.4065
              },
              "consumerDevices": [
                {
                  "id": "Q29uc3VtZXJEZXZpY2U6...",
                  "name": "Living Room Detector",
                  "device": {
                    "id": "THlyaWNUaGVybW9zdGF0RGV2aWNlOj...",
                    "deviceId": "XXXXXXXXXXXX",
                    "globalDeviceType": "Citadel_SC5"
                  }
                }
              ]
            }
          ]
        }
      }
    ]
  },
  "errors": []
}
```

### Get Device State

```http
GET /ris-public-api/api/v2/devices/smokeDetectors/{deviceId}/state
```

**Example:** `GET /ris-public-api/api/v2/devices/smokeDetectors/XXXXXXXXXXXX/state`

**Response:**
```json
{
  "name": "XXXXXXXXXXXX",
  "deviceType": "SmokeDetector",
  "sku": "SMCO600NVACA",
  "registrationStatus": "Registered",
  "isOnline": true,
  "isSupervisionHealthy": true,
  "isOnlineComputed": true,
  "dataSyncState": "Completed",
  "registrationDate": "2025-12-18T03:22:17.457+00:00",
  "lastMessageReceivedTime": "2025-12-20T17:02:30.861+00:00",
  "deviceState": {
    "desired": { ... },
    "reported": {
      "alarmState": {
        "co": {
          "eventSource": "self",
          "tStampEpoch": 1766247701,
          "deviceState": "idle"
        },
        "smoke": {
          "eventSource": "self",
          "tStampEpoch": 1766247701,
          "deviceState": "idle"
        },
        "test": {
          "eventSource": "self",
          "tStampEpoch": 1766034736,
          "deviceState": "idle"
        },
        "malfunction": {
          "eventSource": "self",
          "tStampEpoch": 1766247701,
          "deviceState": "none"
        },
        "battery": {
          "eventSource": "self",
          "tStampEpoch": 1766247701,
          "deviceState": "good"
        },
        "eol": {
          "eventSource": "self",
          "tStampEpoch": 1766247704,
          "deviceState": "no"
        },
        "power": {
          "eventSource": "self",
          "tStampEpoch": 1766029736,
          "deviceState": "ac"
        },
        "silence": {
          "eventSource": "self",
          "tStampEpoch": 1766247701,
          "deviceState": "not_silenced"
        }
      },
      "deviceConfig": {
        "language": "en_US",
        "room": 14,
        "debugLevel": "error",
        "earlyWarning": true
      },
      "deviceInfo": {
        "hwVerE2C": "1.0.0",
        "hwVerExecCore": "1.0.0",
        "hwVerSensorCore": "1.0.0",
        "fwVerE2C": "00.07.72.00",
        "fwVerExecCore": "01.06.38",
        "fwVerSensorCore": "11.00",
        "voiceFileVer": "1.0.0",
        "runningHrs": 0
      },
      "deviceStatus": {
        "rssi": -30,
        "ssid": "WiFiNetwork"
      },
      "deviceStatusFlags": {
        "fault": false,
        "e2Fault": false,
        "photoFault": false,
        "driftMalfunction": false,
        "coFault": false,
        "temperatureFault": false,
        "voiceFault": false,
        "radioFault": false
      }
    }
  },
  "lastFirmwareUpdateTime": "2025-12-18T03:22:45.412+00:00"
}
```

---

## Alarm State Values

All values below are extracted from the official First Alert app (v2.25.2) via decompilation.

### `alarmState.smoke.deviceState`
| Value | Description |
|-------|-------------|
| `idle` | Normal - no smoke detected |
| `alarm` | Smoke alarm active (legacy/generic) |
| `smokeAlarm` | Smoke alarm active |
| `smokeEarlyWarning` | Smoke early warning (below alarm threshold) |
| `smokeInterconnectAlarm` | Smoke alarm triggered by interconnected device |
| `smokeEarlyWarningInterconnectAlarm` | Smoke early warning from interconnected device |

### `alarmState.co.deviceState`
| Value | Description |
|-------|-------------|
| `idle` | Normal - no CO detected |
| `alarm` | CO alarm active (legacy/generic) |
| `coAlarm` | CO alarm active |
| `coEarlyWarning` | CO early warning (below alarm threshold) |
| `carbonMonoxideAlarm` | CO alarm active (alternate key) |
| `carbonMonoxideEarlyWarning` | CO early warning (alternate key) |
| `carbonMonoxideInterconnectAlarm` | CO alarm from interconnected device |
| `carbonMonoxideEarlyWarningInterconnectAlarm` | CO early warning from interconnected device |

### `alarmState.battery.deviceState`
| Value | Description |
|-------|-------------|
| `good` | Battery healthy |
| `low` | Battery low |
| `replace` | Battery needs replacement |
| `critical` | Battery critically low |

### `alarmState.power.deviceState`

This field classifies the *type of electrical current* powering the device,
not "battery vs. plugged in" - it's a different axis from `alarmState.battery`
(battery presence/health, reported separately regardless of what's currently
powering the device).

The API also reports transitional states during power switchovers:

| Value | Description |
|-------|-------------|
| `ac` | Hardwired into 120V AC mains |
| `dc` | Powered by DC current. Confirmed via the official First Alert app: a battery-only SC5 unit (SMCO600NVACA) shows "Power Source: DC" alongside a separate "Battery Status: Good" - since a battery is itself a DC source, this is the expected value for battery-only installations, not a distinct "external DC adapter" mode. |
| `battery` | Present in earlier reverse-engineering notes as a guessed/assumed value, but not confirmed on any device tested so far - every battery-powered detector observed reports `dc`, not `battery`. Kept as a valid enum option in case some other device/model does return it. |
| `acOnly` | AC-only mode (no battery backup) |
| `acToDc` | Transitioning from AC to DC (AC just lost) |
| `dcToAc` | Transitioning from DC to AC (AC restoring) |
| `acLoss` | AC power lost |
| `acRestored` | AC power restored |

### `alarmState.malfunction.deviceState`
| Value | Description |
|-------|-------------|
| `none` | No malfunction |
| (other) | Device malfunction |

### `alarmState.silence.deviceState`
| Value | Description |
|-------|-------------|
| `not_silenced` | Alarm not silenced |
| `silenced` | Alarm temporarily silenced (assumed) |

### `alarmState.eol.deviceState`
| Value | Description |
|-------|-------------|
| `no` | Not at end of life |
| `yes` | End of life - replace device |
| `eolWarning` | Approaching end of life |
| `expired` | Past end of life |

### `alarmState.test.deviceState`
| Value | Description |
|-------|-------------|
| `idle` | Not in test mode |
| `testing` | Test in progress (assumed) |

### `eventSource` field

Each alarm state object includes an `eventSource` field indicating the origin of the event:

| Value | Description |
|-------|-------------|
| `self` | Event originated from this device |
| `node` | Event relayed from a mesh node |
| `remote` | Event from a remote interconnected device |

---

## Activity Feed

Retrieves the event/activity history for the account.

```http
POST https://api.resideo.com/ds-activity-feed-api/api/v1/app/events
Content-Type: application/json

{
  "deviceIds": ["XXXXXXXXXXXX"],
  "pageSize": 50,
  "pageNumber": 1
}
```

---

## SignalR Real-Time Notifications

The platform supports real-time push notifications via ASP.NET Core SignalR over WebSocket.

### Hub URL

```
https://ds-notification-service.prod.titans.cloud/Hub/
```

### Connection Flow

1. **Negotiate** — `POST /Hub/negotiate?negotiateVersion=1` with Bearer token to get a `connectionId`
2. **Connect** — open WebSocket to `wss://ds-notification-service.prod.titans.cloud/Hub/?id={connectionId}`
3. **Handshake** — send `{"protocol":"json","version":1}\x1e`, wait for empty `{}\x1e` response
4. **Subscribe** — invoke `SubscribeSignalRV2` with an array of device IDs:
   ```json
   {"type":1,"target":"SubscribeSignalRV2","arguments":[["DEVICE_ID_1","DEVICE_ID_2"]]}\x1e
   ```
5. **Listen** — server sends type 1 (invocation) messages on state changes, type 6 (ping) for keepalive

### Message Types

| Type | Meaning |
|------|---------|
| 1 | Invocation (server calling client method) |
| 6 | Ping/Pong (keepalive) |
| 7 | Close |

All messages are JSON terminated by the ASCII record separator `\x1e`.

---

## BLE Commands (OpenWeave)

The official app uses Bluetooth Low Energy via the OpenWeave protocol for certain device commands that are **not available through the cloud API**:

| Command | Method |
|---------|--------|
| Self-test | `dev.flutter.pigeon.openweave.OpenWeaveHost.systemTest` |
| Hush/Silence | `dev.flutter.pigeon.openweave.OpenWeaveHost.hush` |
| Identify (chirp/flash) | Likely BLE-only — cloud endpoint returns 404 for all path variations tested |

These require a direct BLE connection to the device and authentication using the `networkKey` from the device shadow's `CitadelSharedConfig`. The cloud API has no equivalent endpoint for triggering tests, silencing alarms, or identifying devices remotely.

---

## Other Endpoints (Discovered)

```http
GET /ris-public-api/api/v1/geofence
```

---

## Device Types

| `globalDeviceType` | Description |
|-------------------|-------------|
| `Citadel_SC5` | First Alert Safe & Sound Smart Smoke/CO Alarm (SMCO600NVACA) |

---

## Home Assistant Integration Notes

### Entities Implemented

1. **Binary Sensors:** Smoke Alarm, CO Alarm, Malfunction, Connectivity, Battery Low, Test Mode, Silenced, End of Life, Early Warning, plus fault flags (General, E2, Photo, Drift, CO, Temperature, Voice, Radio)
2. **Sensors:** Battery Status, Power Source, Smoke Status, CO Status, Test Status, Silence Status, EOL Status, Language, Last Seen, WiFi, firmware/hardware versions, running hours, registration info
3. **Event Entity:** Alarm Events (fires typed events on state changes)
4. **Repairs:** Offline, EOL, and fault conditions

### Real-Time Updates

The integration uses both polling (configurable, default 60s) and SignalR push. When a SignalR event arrives, it triggers an immediate API refresh — so alarms are detected within seconds.

### Alarm Detection Logic

Smoke and CO binary sensors trigger on the full set of alarm states (not just `"alarm"`), including early warning and interconnect variants. This ensures all alarm conditions from interconnected mesh networks are properly detected.

### OAuth Implementation

The integration supports two auth flows:
1. **Email/password login** — performs the Auth0 Resource Owner Password Grant
2. **Manual refresh token** — user supplies a token obtained via network proxy

---

## Example Python Client

```python
import requests

class ResideoClient:
    def __init__(self, refresh_token: str):
        self.client_id = "SRmiA7CaYi1JgivDZdzzoZu4X5VBogGt"
        self.refresh_token = refresh_token
        self.access_token = None

    def _refresh_access_token(self):
        resp = requests.post(
            "https://login.resideo.com/oauth/token",
            json={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id
            }
        )
        data = resp.json()
        self.access_token = data["access_token"]
        return self.access_token

    def _headers(self):
        if not self.access_token:
            self._refresh_access_token()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_accounts(self):
        resp = requests.get(
            "https://api.resideo.com/ris-public-api/api/v1/accounts",
            headers=self._headers()
        )
        return resp.json()

    def get_device_state(self, device_id: str):
        resp = requests.get(
            f"https://api.resideo.com/ris-public-api/api/v2/devices/smokeDetectors/{device_id}/state",
            headers=self._headers()
        )
        return resp.json()

# Usage
client = ResideoClient(refresh_token="your_refresh_token")
accounts = client.get_accounts()
state = client.get_device_state("YOUR_DEVICE_ID")
print(f"Smoke: {state['deviceState']['reported']['alarmState']['smoke']['deviceState']}")
print(f"CO: {state['deviceState']['reported']['alarmState']['co']['deviceState']}")
print(f"Battery: {state['deviceState']['reported']['alarmState']['battery']['deviceState']}")
```
