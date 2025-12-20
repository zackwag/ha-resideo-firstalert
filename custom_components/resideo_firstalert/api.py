"""API client for First Alert by Resideo."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from .const import (
    API_ACCOUNTS_ENDPOINT,
    API_BASE_URL,
    API_DEVICE_STATE_ENDPOINT,
    OAUTH_CLIENT_ID,
    OAUTH_TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class DeviceState:
    """Represents the state of a smoke detector."""

    device_id: str
    name: str
    device_type: str
    sku: str
    is_online: bool
    is_supervision_healthy: bool

    # Alarm states
    smoke_state: str
    co_state: str
    battery_state: str
    power_state: str
    malfunction_state: str
    test_state: str
    silence_state: str
    eol_state: str

    # Device config
    early_warning: bool | None
    language: str | None
    room: int | None

    # Device status
    rssi: int | None
    ssid: str | None

    # Firmware/hardware versions
    firmware_version: str | None
    fw_ver_exec_core: str | None
    fw_ver_sensor_core: str | None
    hw_ver_e2c: str | None
    hw_ver_exec_core: str | None
    hw_ver_sensor_core: str | None
    voice_file_ver: str | None
    running_hours: int | None

    # Fault flags
    fault: bool
    e2_fault: bool
    photo_fault: bool
    drift_malfunction: bool
    co_fault: bool
    temperature_fault: bool
    voice_fault: bool
    radio_fault: bool

    # Timestamps
    last_message_time: str | None
    registration_date: str | None
    last_firmware_update_time: str | None

    raw_data: dict[str, Any]


@dataclass
class Location:
    """Represents a location with devices."""

    id: str
    name: str
    devices: list[dict[str, Any]]


class ResideoApiError(Exception):
    """Base exception for Resideo API errors."""


class ResideoAuthError(ResideoApiError):
    """Authentication error."""


class ResideoConnectionError(ResideoApiError):
    """Connection error."""


class ResideoApiClient:
    """Client for the Resideo API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        refresh_token: str,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._refresh_token = refresh_token
        self._access_token: str | None = None
        self._token_expiry: datetime | None = None
        self._lock = asyncio.Lock()

    async def _ensure_token(self) -> str:
        """Ensure we have a valid access token."""
        async with self._lock:
            if self._access_token and self._token_expiry:
                # Refresh if token expires in less than 5 minutes
                if datetime.now() < self._token_expiry - timedelta(minutes=5):
                    return self._access_token

            # Refresh the token
            await self._refresh_access_token()
            return self._access_token

    async def _refresh_access_token(self) -> None:
        """Refresh the access token."""
        _LOGGER.debug("Refreshing access token")
        try:
            async with self._session.post(
                OAUTH_TOKEN_URL,
                json={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                    "client_id": OAUTH_CLIENT_ID,
                },
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 401:
                    raise ResideoAuthError("Invalid refresh token")
                if response.status != 200:
                    raise ResideoApiError(
                        f"Token refresh failed with status {response.status}"
                    )

                data = await response.json()
                self._access_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
                _LOGGER.debug("Access token refreshed, expires in %s seconds", expires_in)

        except aiohttp.ClientError as err:
            raise ResideoConnectionError(f"Connection error: {err}") from err

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request to the API."""
        token = await self._ensure_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        url = f"{API_BASE_URL}{endpoint}"

        try:
            async with self._session.request(
                method, url, headers=headers, **kwargs
            ) as response:
                if response.status == 401:
                    # Token might have expired, try refreshing once
                    await self._refresh_access_token()
                    token = self._access_token
                    headers["Authorization"] = f"Bearer {token}"
                    async with self._session.request(
                        method, url, headers=headers, **kwargs
                    ) as retry_response:
                        if retry_response.status == 401:
                            raise ResideoAuthError("Authentication failed")
                        retry_response.raise_for_status()
                        return await retry_response.json()

                if response.status != 200:
                    text = await response.text()
                    raise ResideoApiError(
                        f"API request failed with status {response.status}: {text}"
                    )

                return await response.json()

        except aiohttp.ClientError as err:
            raise ResideoConnectionError(f"Connection error: {err}") from err

    async def get_accounts(self) -> dict[str, Any]:
        """Get account information including devices."""
        return await self._request("GET", API_ACCOUNTS_ENDPOINT)

    async def get_device_state(self, device_id: str) -> dict[str, Any]:
        """Get the state of a specific device."""
        endpoint = API_DEVICE_STATE_ENDPOINT.format(device_id=device_id)
        return await self._request("GET", endpoint)

    async def get_devices(self) -> list[dict[str, Any]]:
        """Get all devices from the account."""
        accounts_data = await self.get_accounts()
        devices = []

        data = accounts_data.get("data", {})
        for consumer_user in data.get("consumerUsers", []):
            consumer_account = consumer_user.get("consumerAccount", {})
            for location in consumer_account.get("locations", []):
                location_name = location.get("name", "Unknown")
                for consumer_device in location.get("consumerDevices", []):
                    device = consumer_device.get("device", {})
                    devices.append({
                        "device_id": device.get("deviceId"),
                        "name": consumer_device.get("name", device.get("deviceId")),
                        "location": location_name,
                        "device_type": device.get("globalDeviceType"),
                        "consumer_device_id": consumer_device.get("id"),
                    })

        return devices

    async def get_all_device_states(self) -> dict[str, DeviceState]:
        """Get the state of all devices."""
        devices = await self.get_devices()
        states = {}

        for device in devices:
            device_id = device.get("device_id")
            if not device_id:
                continue

            try:
                state_data = await self.get_device_state(device_id)
                states[device_id] = self._parse_device_state(state_data, device)
            except ResideoApiError as err:
                _LOGGER.warning(
                    "Failed to get state for device %s: %s", device_id, err
                )

        return states

    def _parse_device_state(
        self, state_data: dict[str, Any], device_info: dict[str, Any]
    ) -> DeviceState:
        """Parse device state from API response."""
        device_state = state_data.get("deviceState", {})
        reported = device_state.get("reported", {})
        alarm_state = reported.get("alarmState", {})
        device_status = reported.get("deviceStatus", {})
        device_info_data = reported.get("deviceInfo", {})
        device_config = reported.get("deviceConfig", {})
        status_flags = reported.get("deviceStatusFlags", {})

        return DeviceState(
            device_id=state_data.get("name", device_info.get("device_id", "")),
            name=device_info.get("name", state_data.get("name", "Unknown")),
            device_type=state_data.get("deviceType", ""),
            sku=state_data.get("sku", ""),
            is_online=state_data.get("isOnline", False),
            is_supervision_healthy=state_data.get("isSupervisionHealthy", False),
            # Alarm states
            smoke_state=alarm_state.get("smoke", {}).get("deviceState", "unknown"),
            co_state=alarm_state.get("co", {}).get("deviceState", "unknown"),
            battery_state=alarm_state.get("battery", {}).get("deviceState", "unknown"),
            power_state=alarm_state.get("power", {}).get("deviceState", "unknown"),
            malfunction_state=alarm_state.get("malfunction", {}).get("deviceState", "unknown"),
            test_state=alarm_state.get("test", {}).get("deviceState", "unknown"),
            silence_state=alarm_state.get("silence", {}).get("deviceState", "unknown"),
            eol_state=alarm_state.get("eol", {}).get("deviceState", "unknown"),
            # Device config
            early_warning=device_config.get("earlyWarning"),
            language=device_config.get("language"),
            room=device_config.get("room"),
            # Device status
            rssi=device_status.get("rssi"),
            ssid=device_status.get("ssid"),
            # Firmware/hardware versions
            firmware_version=device_info_data.get("fwVerE2C"),
            fw_ver_exec_core=device_info_data.get("fwVerExecCore"),
            fw_ver_sensor_core=device_info_data.get("fwVerSensorCore"),
            hw_ver_e2c=device_info_data.get("hwVerE2C"),
            hw_ver_exec_core=device_info_data.get("hwVerExecCore"),
            hw_ver_sensor_core=device_info_data.get("hwVerSensorCore"),
            voice_file_ver=device_info_data.get("voiceFileVer"),
            running_hours=device_info_data.get("runningHrs"),
            # Fault flags
            fault=status_flags.get("fault", False),
            e2_fault=status_flags.get("e2Fault", False),
            photo_fault=status_flags.get("photoFault", False),
            drift_malfunction=status_flags.get("driftMalfunction", False),
            co_fault=status_flags.get("coFault", False),
            temperature_fault=status_flags.get("temperatureFault", False),
            voice_fault=status_flags.get("voiceFault", False),
            radio_fault=status_flags.get("radioFault", False),
            # Timestamps
            last_message_time=state_data.get("lastMessageReceivedTime"),
            registration_date=state_data.get("registrationDate"),
            last_firmware_update_time=state_data.get("lastFirmwareUpdateTime"),
            raw_data=state_data,
        )

    async def test_connection(self) -> bool:
        """Test the connection to the API."""
        try:
            await self.get_accounts()
            return True
        except ResideoApiError:
            return False
