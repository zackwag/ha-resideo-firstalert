"""The First Alert by Resideo integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ResideoApiClient, ResideoAuthError, ResideoConnectionError
from .const import CONF_REFRESH_TOKEN, DOMAIN
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

    session = async_get_clientsession(hass)
    client = ResideoApiClient(session, refresh_token)

    # Test the connection
    try:
        if not await client.test_connection():
            raise ConfigEntryNotReady("Failed to connect to Resideo API")
    except ResideoAuthError as err:
        raise ConfigEntryAuthFailed("Invalid authentication") from err
    except ResideoConnectionError as err:
        raise ConfigEntryNotReady(f"Connection error: {err}") from err

    # Create the coordinator
    coordinator = ResideoDataUpdateCoordinator(hass, client)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator
    entry.runtime_data = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
