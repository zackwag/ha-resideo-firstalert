"""Repairs integration for First Alert by Resideo."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .api import DeviceState
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Persistence thresholds (consecutive polls) before raising a repair
THRESHOLD_OFFLINE = 3
THRESHOLD_FAULT = 2
# EOL is immediate — it won't resolve itself


def check_device_repairs(
    hass: HomeAssistant,
    device_id: str,
    state: DeviceState,
    consecutive_offline: int,
    consecutive_faults: dict[str, int],
) -> tuple[int, dict[str, int]]:
    """Check device state and create/resolve repair issues.

    Returns updated (consecutive_offline, consecutive_faults) counters.
    """
    # --- Offline ---
    # Battery-powered devices (power_state dc or battery) sleep to conserve
    # energy, so being offline is expected — skip the offline repair for them.
    is_battery_powered = state.power_state in ("dc", "battery")
    if not state.is_online and not is_battery_powered:
        consecutive_offline += 1
        if consecutive_offline >= THRESHOLD_OFFLINE:
            ir.async_create_issue(
                hass,
                DOMAIN,
                f"{device_id}_offline",
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="device_offline",
                translation_placeholders={"device_name": state.name},
            )
    else:
        if consecutive_offline >= THRESHOLD_OFFLINE:
            ir.async_delete_issue(hass, DOMAIN, f"{device_id}_offline")
        consecutive_offline = 0

    # --- End of Life (immediate, no threshold) ---
    if state.eol_state in ("yes", "eolWarning", "expired"):
        ir.async_create_issue(
            hass,
            DOMAIN,
            f"{device_id}_eol",
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key="device_end_of_life",
            translation_placeholders={"device_name": state.name},
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, f"{device_id}_eol")

    # --- Malfunction ---
    consecutive_faults = _check_fault(
        hass,
        device_id,
        "malfunction",
        state.malfunction_state not in ("none", "unknown"),
        state.name,
        consecutive_faults,
    )

    # --- Individual fault flags ---
    fault_checks = [
        ("fault", state.fault),
        ("e2_fault", state.e2_fault),
        ("photo_fault", state.photo_fault),
        ("drift_malfunction", state.drift_malfunction),
        ("co_fault", state.co_fault),
        ("temperature_fault", state.temperature_fault),
        ("voice_fault", state.voice_fault),
        ("radio_fault", state.radio_fault),
    ]

    for fault_key, is_active in fault_checks:
        consecutive_faults = _check_fault(
            hass,
            device_id,
            fault_key,
            is_active,
            state.name,
            consecutive_faults,
        )

    return consecutive_offline, consecutive_faults


def _check_fault(
    hass: HomeAssistant,
    device_id: str,
    fault_key: str,
    is_active: bool,
    device_name: str,
    consecutive_faults: dict[str, int],
) -> dict[str, int]:
    """Check a single fault condition against its threshold."""
    issue_id = f"{device_id}_{fault_key}"

    if is_active:
        count = consecutive_faults.get(fault_key, 0) + 1
        consecutive_faults[fault_key] = count
        if count >= THRESHOLD_FAULT:
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="device_fault",
                translation_placeholders={
                    "device_name": device_name,
                    "fault_type": fault_key.replace("_", " ").title(),
                },
            )
    else:
        if consecutive_faults.get(fault_key, 0) >= THRESHOLD_FAULT:
            ir.async_delete_issue(hass, DOMAIN, issue_id)
        consecutive_faults[fault_key] = 0

    return consecutive_faults
