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

    async def _async_update_data(self) -> dict[str, DeviceState]:
        """Fetch data from the API."""
        try:
            data = await self.client.get_all_device_states()
            if self._last_update_success is False:
                _LOGGER.info("Connection to Resideo API restored")
            self._last_update_success = True
            return data
        except ResideoAuthError as err:
            self._last_update_success = False
            raise ConfigEntryAuthFailed("Authentication failed - token may have expired") from err
        except ResideoApiError as err:
            if self._last_update_success is not False:
                _LOGGER.warning("Unable to connect to Resideo API: %s", err)
            self._last_update_success = False
            raise UpdateFailed(f"Error communicating with Resideo API: {err}") from err
