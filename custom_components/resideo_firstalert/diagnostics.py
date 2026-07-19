"""Diagnostics support for First Alert by Resideo."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import ResideoDataUpdateCoordinator

TO_REDACT = {"refresh_token", "access_token", "ssid"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: ResideoDataUpdateCoordinator = entry.runtime_data

    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "last_update_success": coordinator.last_update_success,
        "devices": {
            device_id: async_redact_data(asdict(device_state), TO_REDACT)
            for device_id, device_state in coordinator.data.items()
        },
    }
