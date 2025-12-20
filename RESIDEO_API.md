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

### `alarmState.smoke.deviceState`
| Value | Description |
|-------|-------------|
| `idle` | Normal - no smoke detected |
| `alarm` | Smoke alarm active |

### `alarmState.co.deviceState`
| Value | Description |
|-------|-------------|
| `idle` | Normal - no CO detected |
| `alarm` | CO alarm active |

### `alarmState.battery.deviceState`
| Value | Description |
|-------|-------------|
| `good` | Battery healthy |
| `low` | Battery low (assumed) |

### `alarmState.power.deviceState`
| Value | Description |
|-------|-------------|
| `ac` | Running on AC power |
| `battery` | Running on battery (assumed) |

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
| `yes` | End of life - replace device (assumed) |

### `alarmState.test.deviceState`
| Value | Description |
|-------|-------------|
| `idle` | Not in test mode |
| `testing` | Test in progress (assumed) |

---

## Other Endpoints (Discovered)

```http
GET /ris-public-api/api/v1/geofence
POST /ds-activity-feed-api/api/v1/app/events
```

---

## Device Types

| `globalDeviceType` | Description |
|-------------------|-------------|
| `Citadel_SC5` | First Alert Safe & Sound Smart Smoke/CO Alarm (SMCO600NVACA) |

---

## Home Assistant Integration Notes

### Sensors to Expose

1. **Binary Sensors:**
   - Smoke Alarm (`alarmState.smoke.deviceState` != "idle")
   - CO Alarm (`alarmState.co.deviceState` != "idle")
   - Malfunction (`alarmState.malfunction.deviceState` != "none")
   - Online Status (`isOnline`)

2. **Sensors:**
   - Battery Status (`alarmState.battery.deviceState`)
   - Power Source (`alarmState.power.deviceState`)
   - WiFi Signal Strength (`deviceStatus.rssi`)
   - Last Message Time (`lastMessageReceivedTime`)

3. **Diagnostic Sensors:**
   - Firmware versions
   - End of Life status
   - Various fault flags

### Polling Interval

Recommend polling every 30-60 seconds. The device reports timestamps in `tStampEpoch` format.

### OAuth Flow for Home Assistant

For Home Assistant, you'll need to implement the full OAuth PKCE flow:
1. Generate code_verifier and code_challenge
2. Open browser to authorization URL
3. Handle callback with authorization code
4. Exchange code for tokens
5. Store and refresh tokens as needed

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
