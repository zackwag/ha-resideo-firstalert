"""Tests for api.py (no Home Assistant dependency, HTTP mocked via aioresponses)."""

from __future__ import annotations

from datetime import datetime, timedelta

import aiohttp
import pytest
from aioresponses import aioresponses
from resideo_firstalert.api import (
    ResideoApiClient,
    ResideoAuthError,
    ResideoConnectionError,
)
from resideo_firstalert.const import (
    ALARM_STATE_ALARM,
    API_ACCOUNTS_ENDPOINT,
    API_BASE_URL,
    API_DEVICE_STATE_ENDPOINT,
    OAUTH_TOKEN_URL,
)

ACCOUNTS_URL = f"{API_BASE_URL}{API_ACCOUNTS_ENDPOINT}"


def _device_state_url(device_id: str) -> str:
    return f"{API_BASE_URL}{API_DEVICE_STATE_ENDPOINT.format(device_id=device_id)}"


def _token_response(access_token: str = "access-1", refresh_token: str | None = None) -> dict:
    payload = {"access_token": access_token, "expires_in": 3600, "token_type": "Bearer"}
    if refresh_token:
        payload["refresh_token"] = refresh_token
    return payload


def _accounts_response(devices: list[dict]) -> dict:
    return {
        "data": {
            "id": "user-123",
            "consumerUsers": [
                {
                    "consumerAccount": {
                        "locations": [
                            {
                                "name": "Home",
                                "consumerDevices": devices,
                            }
                        ]
                    }
                }
            ],
        },
        "errors": [],
    }


def _consumer_device(device_id: str, name: str = "Living Room Detector") -> dict:
    return {
        "id": f"consumer-{device_id}",
        "name": name,
        "device": {"deviceId": device_id, "globalDeviceType": "Citadel_SC5"},
    }


def _device_state_response(
    *,
    device_id: str = "DEVICE1",
    smoke: str = "idle",
    include_smoke_key: bool = True,
) -> dict:
    alarm_state = {
        "co": {"eventSource": "self", "tStampEpoch": 1766247701, "deviceState": "idle"},
        "test": {"eventSource": "self", "tStampEpoch": 1766034736, "deviceState": "idle"},
        "malfunction": {
            "eventSource": "self",
            "tStampEpoch": 1766247701,
            "deviceState": "none",
        },
        "battery": {
            "eventSource": "self",
            "tStampEpoch": 1766247701,
            "deviceState": "good",
        },
        "eol": {"eventSource": "self", "tStampEpoch": 1766247704, "deviceState": "no"},
        "power": {"eventSource": "self", "tStampEpoch": 1766029736, "deviceState": "ac"},
        "silence": {
            "eventSource": "self",
            "tStampEpoch": 1766247701,
            "deviceState": "not_silenced",
        },
    }
    if include_smoke_key:
        alarm_state["smoke"] = {
            "eventSource": "self",
            "tStampEpoch": 1766247701,
            "deviceState": smoke,
        }

    return {
        "name": device_id,
        "deviceType": "SmokeDetector",
        "sku": "SMCO600NVACA",
        "registrationStatus": "Registered",
        "isOnline": True,
        "isOnlineComputed": True,
        "isSupervisionHealthy": True,
        "dataSyncState": "Completed",
        "registrationDate": "2025-12-18T03:22:17.457+00:00",
        "lastMessageReceivedTime": "2025-12-20T17:02:30.861+00:00",
        "deviceState": {
            "desired": {},
            "reported": {
                "alarmState": alarm_state,
                "deviceConfig": {
                    "language": "en_US",
                    "room": 14,
                    "earlyWarning": True,
                    "debugLevel": "error",
                },
                "deviceInfo": {
                    "hwVerE2C": "1.0.0",
                    "hwVerExecCore": "1.0.0",
                    "hwVerSensorCore": "1.0.0",
                    "fwVerE2C": "00.07.72.00",
                    "fwVerExecCore": "01.06.38",
                    "fwVerSensorCore": "11.00",
                    "voiceFileVer": "1.0.0",
                    "runningHrs": 0,
                },
                "deviceStatus": {"rssi": -30, "ssid": "WiFiNetwork"},
                "deviceStatusFlags": {
                    "fault": False,
                    "e2Fault": False,
                    "photoFault": False,
                    "driftMalfunction": False,
                    "coFault": False,
                    "temperatureFault": False,
                    "voiceFault": False,
                    "radioFault": False,
                },
            },
        },
        "lastFirmwareUpdateTime": "2025-12-18T03:22:45.412+00:00",
    }


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as sess:
        yield sess


async def test_refresh_access_token_sets_access_token_and_expiry(session) -> None:
    client = ResideoApiClient(session, "initial-refresh-token")
    with aioresponses() as m:
        m.post(OAUTH_TOKEN_URL, payload=_token_response(access_token="access-1"))
        await client._refresh_access_token()

    assert client._access_token == "access-1"
    assert client._token_expiry is not None
    assert client._token_expiry > datetime.now() + timedelta(minutes=59)


async def test_refresh_access_token_rotates_and_calls_callback(session) -> None:
    seen_tokens: list[str] = []
    client = ResideoApiClient(
        session, "old-refresh-token", on_refresh_token_updated=seen_tokens.append
    )
    with aioresponses() as m:
        m.post(
            OAUTH_TOKEN_URL,
            payload=_token_response(refresh_token="new-refresh-token"),
        )
        await client._refresh_access_token()

    assert client._refresh_token == "new-refresh-token"
    assert seen_tokens == ["new-refresh-token"]


async def test_refresh_access_token_no_callback_when_token_unchanged(session) -> None:
    seen_tokens: list[str] = []
    client = ResideoApiClient(
        session, "same-refresh-token", on_refresh_token_updated=seen_tokens.append
    )
    with aioresponses() as m:
        m.post(
            OAUTH_TOKEN_URL,
            payload=_token_response(refresh_token="same-refresh-token"),
        )
        await client._refresh_access_token()

    assert client._refresh_token == "same-refresh-token"
    assert seen_tokens == []


async def test_refresh_access_token_401_raises_auth_error(session) -> None:
    client = ResideoApiClient(session, "bad-refresh-token")
    with aioresponses() as m:
        m.post(OAUTH_TOKEN_URL, status=401)
        with pytest.raises(ResideoAuthError):
            await client._refresh_access_token()


async def test_refresh_access_token_connection_error(session) -> None:
    client = ResideoApiClient(session, "refresh-token")
    with aioresponses() as m:
        m.post(OAUTH_TOKEN_URL, exception=aiohttp.ClientConnectionError("boom"))
        with pytest.raises(ResideoConnectionError):
            await client._refresh_access_token()


async def test_get_devices_parses_account_response(session) -> None:
    client = ResideoApiClient(session, "refresh-token")
    with aioresponses() as m:
        m.post(OAUTH_TOKEN_URL, payload=_token_response())
        m.get(
            ACCOUNTS_URL,
            payload=_accounts_response([_consumer_device("DEVICE1", "Living Room Detector")]),
        )
        devices = await client.get_devices()

    assert devices == [
        {
            "device_id": "DEVICE1",
            "name": "Living Room Detector",
            "location": "Home",
            "device_type": "Citadel_SC5",
            "consumer_device_id": "consumer-DEVICE1",
        }
    ]


async def test_get_devices_caches_within_ttl(session) -> None:
    """A second get_devices() call within the cache TTL must not hit the network."""
    client = ResideoApiClient(session, "refresh-token")
    with aioresponses() as m:
        m.post(OAUTH_TOKEN_URL, payload=_token_response())
        # Registered once (no repeat=True): a second real HTTP call would fail.
        m.get(
            ACCOUNTS_URL,
            payload=_accounts_response([_consumer_device("DEVICE1")]),
        )
        first = await client.get_devices()
        second = await client.get_devices()

    assert first == second


async def test_get_devices_refetches_after_cache_expires(session) -> None:
    client = ResideoApiClient(session, "refresh-token")
    with aioresponses() as m:
        m.post(OAUTH_TOKEN_URL, payload=_token_response(), repeat=True)
        m.get(
            ACCOUNTS_URL,
            payload=_accounts_response([_consumer_device("DEVICE1")]),
        )
        first = await client.get_devices()

        # Force the cache to look expired.
        client._devices_cache_time = datetime.now() - timedelta(hours=1)

        m.get(
            ACCOUNTS_URL,
            payload=_accounts_response([_consumer_device("DEVICE1", "Renamed Detector")]),
        )
        second = await client.get_devices()

    assert first[0]["name"] == "Living Room Detector"
    assert second[0]["name"] == "Renamed Detector"


async def test_parse_device_state_full_response(session) -> None:
    client = ResideoApiClient(session, "refresh-token")
    device_info = {
        "device_id": "DEVICE1",
        "name": "Living Room Detector",
        "location": "Home",
    }

    state = client._parse_device_state(
        _device_state_response(device_id="DEVICE1", smoke="idle"), device_info
    )

    assert state.device_id == "DEVICE1"
    assert state.name == "Living Room Detector"
    assert state.location == "Home"
    assert state.sku == "SMCO600NVACA"
    assert state.is_online is True
    assert state.is_online_computed is True
    assert state.registration_status == "Registered"
    assert state.data_sync_state == "Completed"
    assert state.debug_level == "error"
    assert state.smoke_state == "idle"
    assert state.battery_state == "good"
    assert state.power_state == "ac"
    assert state.alarm_timestamps["smoke"] == 1766247701
    assert state.alarm_timestamps["battery"] == 1766247701
    assert state.rssi == -30
    assert state.ssid == "WiFiNetwork"
    assert state.room == 14
    assert state.early_warning is True


async def test_parse_device_state_missing_field_defaults_to_safe_state(session) -> None:
    """Regression test: a missing alarmState.smoke must not look like an active alarm."""
    client = ResideoApiClient(session, "refresh-token")
    device_info = {"device_id": "DEVICE1"}

    state = client._parse_device_state(
        _device_state_response(include_smoke_key=False), device_info
    )

    assert state.smoke_state == "unknown"
    assert state.smoke_state != ALARM_STATE_ALARM
    assert state.alarm_timestamps["smoke"] is None


async def test_get_all_device_states_propagates_auth_error(session) -> None:
    """Regression test: an auth failure while polling a device must not be swallowed."""
    client = ResideoApiClient(session, "refresh-token")
    with aioresponses() as m:
        m.post(OAUTH_TOKEN_URL, payload=_token_response(), repeat=True)
        m.get(
            ACCOUNTS_URL,
            payload=_accounts_response([_consumer_device("DEVICE1")]),
        )
        # First attempt gets 401, triggers a token refresh + one retry, which
        # also gets 401 - that's what should raise ResideoAuthError.
        m.get(_device_state_url("DEVICE1"), status=401)
        m.get(_device_state_url("DEVICE1"), status=401)

        with pytest.raises(ResideoAuthError):
            await client.get_all_device_states()


async def test_get_all_device_states_skips_device_with_non_auth_error(
    session, caplog: pytest.LogCaptureFixture
) -> None:
    client = ResideoApiClient(session, "refresh-token")
    with aioresponses() as m:
        m.post(OAUTH_TOKEN_URL, payload=_token_response())
        m.get(
            ACCOUNTS_URL,
            payload=_accounts_response(
                [_consumer_device("DEVICE1"), _consumer_device("DEVICE2")]
            ),
        )
        m.get(_device_state_url("DEVICE1"), status=500, body="boom")
        m.get(_device_state_url("DEVICE2"), payload=_device_state_response(device_id="DEVICE2"))

        states = await client.get_all_device_states()

    assert list(states) == ["DEVICE2"]
    assert "DEVICE1" in caplog.text
