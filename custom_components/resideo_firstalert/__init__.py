"""The First Alert by Resideo integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    ResideoApiClient,
    ResideoApiError,
    ResideoAuthError,
    ResideoConnectionError,
)
from .const import CONF_REFRESH_TOKEN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import ResideoDataUpdateCoordinator

if TYPE_CHECKING:
    from typing import TypeAlias
    ResideoConfigEntry: TypeAlias = ConfigEntry[ResideoDataUpdateCoordinator]
else:
    ResideoConfigEntry = ConfigEntry

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up First Alert by Resideo from a config entry."""
    refresh_token = entry.data[CONF_REFRESH_TOKEN]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    def _persist_refresh_token(new_refresh_token: str) -> None:
        """Persist a rotated refresh token to the config entry."""
        new_data = {**entry.data, CONF_REFRESH_TOKEN: new_refresh_token}
        if CONF_TOKEN in entry.data:
            new_data[CONF_TOKEN] = {"refresh_token": new_refresh_token}
        hass.config_entries.async_update_entry(entry, data=new_data)

    session = async_get_clientsession(hass)
    client = ResideoApiClient(
        session, refresh_token, on_refresh_token_updated=_persist_refresh_token
    )

    # Test the connection
    try:
        await client.get_accounts()
    except ResideoAuthError as err:
        raise ConfigEntryAuthFailed("Invalid authentication") from err
    except ResideoConnectionError as err:
        raise ConfigEntryNotReady(f"Connection error: {err}") from err
    except ResideoApiError as err:
        raise ConfigEntryNotReady(f"Failed to connect to Resideo API: {err}") from err

    # Create the coordinator
    coordinator = ResideoDataUpdateCoordinator(hass, client, scan_interval)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator
    entry.runtime_data = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_options_updated))

    return True


async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: ResideoDataUpdateCoordinator = entry.runtime_data
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator.update_interval = timedelta(seconds=scan_interval)
    _LOGGER.debug("Updated scan interval to %s seconds", scan_interval)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
