"""Data coordinator for First Alert by Resideo."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DeviceState, ResideoApiClient, ResideoApiError, ResideoAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .repairs import check_device_repairs
from .signalr import SignalRClient

_LOGGER = logging.getLogger(__name__)


class ResideoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, DeviceState]]):
    """Class to manage fetching Resideo data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ResideoApiClient,
        update_interval_seconds: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval_seconds),
        )
        self.client = client
        self._last_update_success: bool | None = None
        self._signalr: SignalRClient | None = None
        # Repairs tracking: per-device counters for persistence thresholds
        self._consecutive_offline: dict[str, int] = {}
        self._consecutive_faults: dict[str, dict[str, int]] = {}

    async def async_start_signalr(self) -> None:
        """Start the SignalR connection for real-time updates."""
        if self._signalr is not None:
            return

        device_ids = list(self.data.keys()) if self.data else []
        if not device_ids:
            return

        self._signalr = SignalRClient(
            session=self.client._session,
            get_access_token=self._get_signalr_token,
            on_event=self._on_signalr_event,
        )
        await self._signalr.start(device_ids)
        _LOGGER.debug("SignalR real-time connection started")

    async def async_stop_signalr(self) -> None:
        """Stop the SignalR connection."""
        if self._signalr:
            await self._signalr.stop()
            self._signalr = None

    def _get_signalr_token(self) -> str | None:
        """Return the current access token for SignalR auth."""
        return self.client._access_token

    def _on_signalr_event(self, message: dict[str, Any]) -> None:
        """Handle a SignalR event by triggering an immediate refresh."""
        _LOGGER.debug("SignalR event received: %s", message.get("target"))
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> dict[str, DeviceState]:
        """Fetch data from the API."""
        try:
            data = await self.client.get_all_device_states()
            if self._last_update_success is False:
                _LOGGER.info("Connection to Resideo API restored")
            self._last_update_success = True
            self._check_repairs(data)
            return data
        except ResideoAuthError as err:
            self._last_update_success = False
            raise ConfigEntryAuthFailed("Authentication failed - token may have expired") from err
        except ResideoApiError as err:
            if self._last_update_success is not False:
                _LOGGER.warning("Unable to connect to Resideo API: %s", err)
            self._last_update_success = False
            raise UpdateFailed(f"Error communicating with Resideo API: {err}") from err

    def _check_repairs(self, data: dict[str, DeviceState]) -> None:
        """Run repair checks for all devices."""
        for device_id, state in data.items():
            offline_count = self._consecutive_offline.get(device_id, 0)
            fault_counts = self._consecutive_faults.get(device_id, {})

            offline_count, fault_counts = check_device_repairs(
                self.hass, device_id, state, offline_count, fault_counts
            )

            self._consecutive_offline[device_id] = offline_count
            self._consecutive_faults[device_id] = fault_counts
