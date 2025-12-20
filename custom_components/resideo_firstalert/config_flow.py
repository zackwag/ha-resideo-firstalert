"""Config flow for First Alert by Resideo integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_TOKEN
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ResideoApiClient, ResideoAuthError, ResideoConnectionError
from .const import CONF_REFRESH_TOKEN, DOMAIN, OAUTH_SCOPES

_LOGGER = logging.getLogger(__name__)


class ResideoOAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle the OAuth2 config flow for Resideo."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data for authorization URL."""
        return {
            "scope": OAUTH_SCOPES,
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user-initiated flow - offer choice between OAuth and manual."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["oauth", "manual"],
            description_placeholders={
                "docs_url": "https://github.com/aidenmitchell/ha-resideo-firstalert#authentication"
            },
        )

    async def async_step_oauth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle OAuth flow."""
        return await self.async_step_pick_implementation()

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual token entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            refresh_token = user_input[CONF_REFRESH_TOKEN]

            # Test the refresh token
            session = async_get_clientsession(self.hass)
            client = ResideoApiClient(session, refresh_token)

            try:
                accounts = await client.get_accounts()
                data = accounts.get("data", {})
                email = data.get("contactEmail", "unknown")
                user_id = data.get("id", "unknown")
                first_name = data.get("firstName", "")
                last_name = data.get("lastName", "")

                await self.async_set_unique_id(user_id)
                self._abort_if_unique_id_configured()

                title = f"First Alert ({email})"
                if first_name:
                    title = f"First Alert ({first_name} {last_name})"

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_REFRESH_TOKEN: refresh_token,
                        CONF_TOKEN: {
                            "refresh_token": refresh_token,
                        },
                    },
                )

            except ResideoAuthError:
                errors["base"] = "invalid_auth"
            except ResideoConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({vol.Required(CONF_REFRESH_TOKEN): str}),
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/aidenmitchell/ha-resideo-firstalert#getting-your-refresh-token"
            },
        )

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create entry from OAuth data."""
        token = data.get(CONF_TOKEN, {})
        refresh_token = token.get("refresh_token")

        if not refresh_token:
            return self.async_abort(reason="no_refresh_token")

        # Test the token and get user info
        session = async_get_clientsession(self.hass)
        client = ResideoApiClient(session, refresh_token)

        try:
            accounts = await client.get_accounts()
            account_data = accounts.get("data", {})
            email = account_data.get("contactEmail", "unknown")
            user_id = account_data.get("id", "unknown")
            first_name = account_data.get("firstName", "")
            last_name = account_data.get("lastName", "")

            await self.async_set_unique_id(user_id)
            self._abort_if_unique_id_configured()

            title = f"First Alert ({email})"
            if first_name:
                title = f"First Alert ({first_name} {last_name})"

            # Store refresh token in data for our API client
            data[CONF_REFRESH_TOKEN] = refresh_token

            return self.async_create_entry(title=title, data=data)

        except ResideoApiError as err:
            _LOGGER.error("Failed to verify OAuth token: %s", err)
            return self.async_abort(reason="oauth_error")

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation - offer choice."""
        return self.async_show_menu(
            step_id="reauth_confirm",
            menu_options=["reauth_oauth", "reauth_manual"],
        )

    async def async_step_reauth_oauth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth via OAuth."""
        return await self.async_step_pick_implementation()

    async def async_step_reauth_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth via manual token entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            refresh_token = user_input[CONF_REFRESH_TOKEN]

            session = async_get_clientsession(self.hass)
            client = ResideoApiClient(session, refresh_token)

            try:
                await client.get_accounts()

                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={
                        CONF_REFRESH_TOKEN: refresh_token,
                        CONF_TOKEN: {"refresh_token": refresh_token},
                    },
                )

            except ResideoAuthError:
                errors["base"] = "invalid_auth"
            except ResideoConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_manual",
            data_schema=vol.Schema({vol.Required(CONF_REFRESH_TOKEN): str}),
            errors=errors,
        )


# Import for API error
from .api import ResideoApiError
