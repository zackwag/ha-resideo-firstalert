"""Regression tests for the config flow's already-configured abort handling.

_abort_if_unique_id_configured() raises AbortFlow (a HomeAssistantError
subclass), which a bare `except Exception:` will swallow and turn into a
misleading "unknown error" instead of the proper already_configured abort.

Steps are exercised directly (bypassing hass.config_entries.flow, which
would need the integration to be discoverable under a real HA config dir)
so these only depend on the real ConfigFlow/AbortFlow classes and a
MockConfigEntry, not on HA's component loader.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.data_entry_flow import AbortFlow
from pytest_homeassistant_custom_component.common import MockConfigEntry
from resideo_firstalert.config_flow import ResideoConfigFlow
from resideo_firstalert.const import DOMAIN

ACCOUNT_DATA = {
    "data": {
        "id": "user-1",
        "contactEmail": "person@example.com",
        "firstName": "Ann",
        "lastName": "Alarm",
    }
}


def _flow(hass) -> ResideoConfigFlow:
    flow = ResideoConfigFlow()
    flow.hass = hass
    flow.handler = DOMAIN
    flow.flow_id = "test-flow-id"
    flow.context = {"source": "user"}
    return flow


async def test_manual_step_aborts_when_account_already_configured(hass) -> None:
    """Re-adding an already-configured account aborts instead of erroring."""
    MockConfigEntry(domain=DOMAIN, unique_id="user-1").add_to_hass(hass)
    flow = _flow(hass)

    with (
        patch(
            "resideo_firstalert.config_flow.async_get_clientsession",
            return_value=Mock(),
        ),
        patch(
            "resideo_firstalert.config_flow.ResideoApiClient.get_accounts",
            return_value=ACCOUNT_DATA,
        ),
        pytest.raises(AbortFlow, match="already_configured"),
    ):
        await flow.async_step_manual({"refresh_token": "some-refresh-token"})


async def test_browser_step_aborts_when_account_already_configured(hass) -> None:
    """Same abort behavior for the browser-assisted login step."""
    MockConfigEntry(domain=DOMAIN, unique_id="user-1").add_to_hass(hass)
    flow = _flow(hass)

    with (
        patch(
            "resideo_firstalert.config_flow.async_get_clientsession",
            return_value=Mock(),
        ),
        patch.object(
            ResideoConfigFlow,
            "_tokens_from_pasted_code",
            AsyncMock(return_value={"refresh_token": "some-refresh-token"}),
        ),
        patch(
            "resideo_firstalert.config_flow.ResideoApiClient.get_accounts",
            return_value=ACCOUNT_DATA,
        ),
        pytest.raises(AbortFlow, match="already_configured"),
    ):
        await flow.async_step_browser({"callback": "some-pasted-code"})
