"""Config flow for First Alert by Resideo integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_TOKEN
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    ResideoApiClient,
    ResideoAuthError,
    ResideoConnectionError,
)
from .auth import (
    AuthenticationError,
    build_authorize_url,
    exchange_code_for_tokens,
    generate_pkce_pair,
    parse_authorization_code,
)
from .const import (
    CONF_REFRESH_TOKEN,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class ResideoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Resideo."""

    def __init__(self) -> None:
        """Initialize the flow handler."""
        super().__init__()
        self._code_verifier: str | None = None
        self._auth_state: str | None = None
        self._authorize_url: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return ResideoOptionsFlowHandler()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle user-initiated flow - offer choice of auth methods."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["browser", "manual"],
            description_placeholders={
                "docs_url": "https://github.com/zackwag/ha-resideo-firstalert#getting-your-token"
            },
        )

    def _new_authorize_url(self) -> str:
        """Generate a fresh PKCE pair and authorize URL, storing flow state."""
        self._code_verifier, code_challenge, self._auth_state = generate_pkce_pair()
        self._authorize_url = build_authorize_url(code_challenge, self._auth_state)
        return self._authorize_url

    async def _tokens_from_pasted_code(self, pasted: str) -> dict:
        """Turn a pasted callback URL or code into tokens."""
        code = parse_authorization_code(pasted, self._auth_state)
        session = async_get_clientsession(self.hass)
        return await exchange_code_for_tokens(session, code, self._code_verifier)

    async def async_step_browser(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle browser-assisted login (sign in yourself, paste the callback)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                tokens = await self._tokens_from_pasted_code(user_input["callback"])
                refresh_token = tokens.get("refresh_token")

                if not refresh_token:
                    errors["base"] = "no_refresh_token"
                else:
                    session = async_get_clientsession(self.hass)
                    client = ResideoApiClient(session, refresh_token)
                    accounts = await client.get_accounts()
                    data = accounts.get("data", {})
                    user_id = data.get("id", "unknown")
                    first_name = data.get("firstName", "")
                    last_name = data.get("lastName", "")
                    email = data.get("contactEmail", "unknown")

                    await self.async_set_unique_id(user_id)
                    self._abort_if_unique_id_configured()

                    title = f"First Alert ({email})"
                    if first_name:
                        title = f"First Alert ({first_name} {last_name})"

                    current_token = client.refresh_token
                    return self.async_create_entry(
                        title=title,
                        data={
                            CONF_REFRESH_TOKEN: current_token,
                            CONF_TOKEN: {
                                "refresh_token": current_token,
                            },
                        },
                    )

            except AbortFlow:
                raise
            except AuthenticationError as err:
                _LOGGER.error("Browser login failed: %s", err)
                errors["base"] = "auth_error"
            except ResideoAuthError:
                errors["base"] = "invalid_auth"
            except ResideoConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during browser login")
                errors["base"] = "unknown"

        # Generate the URL once per flow so the pasted code matches its verifier.
        if self._authorize_url is None:
            self._new_authorize_url()

        return self.async_show_form(
            step_id="browser",
            data_schema=vol.Schema({vol.Required("callback"): str}),
            errors=errors,
            description_placeholders={"authorize_url": self._authorize_url},
        )

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
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

                current_token = client.refresh_token
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_REFRESH_TOKEN: current_token,
                        CONF_TOKEN: {
                            "refresh_token": current_token,
                        },
                    },
                )

            except AbortFlow:
                raise
            except ResideoAuthError:
                errors["base"] = "invalid_token"
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
                "docs_url": "https://github.com/zackwag/ha-resideo-firstalert#getting-your-token"
            },
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle reauth."""
        return await self.async_step_reauth_confirm()

    def _abort_if_reauth_account_mismatch(
        self, account_data: dict[str, Any]
    ) -> ConfigFlowResult | None:
        """Abort if reauth was completed with a different Resideo account."""
        user_id = account_data.get("id")
        reauth_entry = self._get_reauth_entry()
        if user_id and reauth_entry.unique_id and user_id != reauth_entry.unique_id:
            return self.async_abort(reason="reauth_account_mismatch")
        return None

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation - offer choice."""
        return self.async_show_menu(
            step_id="reauth_confirm",
            menu_options=["reauth_browser", "reauth_manual"],
        )

    async def async_step_reauth_browser(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth via browser-assisted login."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                tokens = await self._tokens_from_pasted_code(user_input["callback"])
                refresh_token = tokens.get("refresh_token")

                if not refresh_token:
                    errors["base"] = "no_refresh_token"
                else:
                    session = async_get_clientsession(self.hass)
                    client = ResideoApiClient(session, refresh_token)
                    accounts = await client.get_accounts()

                    if mismatch := self._abort_if_reauth_account_mismatch(accounts.get("data", {})):
                        return mismatch

                    current_token = client.refresh_token
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(),
                        data_updates={
                            CONF_REFRESH_TOKEN: current_token,
                            CONF_TOKEN: {"refresh_token": current_token},
                        },
                    )

            except AuthenticationError as err:
                _LOGGER.error("Browser reauth failed: %s", err)
                errors["base"] = "auth_error"
            except ResideoAuthError:
                errors["base"] = "invalid_auth"
            except ResideoConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during browser reauth")
                errors["base"] = "unknown"

        if self._authorize_url is None:
            self._new_authorize_url()

        return self.async_show_form(
            step_id="reauth_browser",
            data_schema=vol.Schema({vol.Required("callback"): str}),
            errors=errors,
            description_placeholders={"authorize_url": self._authorize_url},
        )

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
                accounts = await client.get_accounts()

                if mismatch := self._abort_if_reauth_account_mismatch(accounts.get("data", {})):
                    return mismatch

                current_token = client.refresh_token
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={
                        CONF_REFRESH_TOKEN: current_token,
                        CONF_TOKEN: {"refresh_token": current_token},
                    },
                )

            except ResideoAuthError:
                errors["base"] = "invalid_token"
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


class ResideoOptionsFlowHandler(OptionsFlow):
    """Handle options flow for Resideo."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Show menu of options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["settings", "update_token"],
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage general settings."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=current_interval,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
        )

    async def async_step_update_token(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the refresh token."""
        errors: dict[str, str] = {}

        if user_input is not None:
            refresh_token = user_input[CONF_REFRESH_TOKEN]

            # Test the new token
            session = async_get_clientsession(self.hass)
            client = ResideoApiClient(session, refresh_token)

            try:
                accounts = await client.get_accounts()
                account_data = accounts.get("data", {})
                user_id = account_data.get("id")

                if (
                    user_id
                    and self.config_entry.unique_id
                    and user_id != self.config_entry.unique_id
                ):
                    errors["base"] = "account_mismatch"
                else:
                    current_token = client.refresh_token
                    new_data = {
                        **self.config_entry.data,
                        CONF_REFRESH_TOKEN: current_token,
                    }
                    if CONF_TOKEN in self.config_entry.data:
                        new_data[CONF_TOKEN] = {"refresh_token": current_token}

                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data=new_data,
                    )
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)

                    return self.async_create_entry(title="", data=self.config_entry.options)

            except ResideoAuthError:
                errors["base"] = "invalid_token"
            except ResideoConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="update_token",
            data_schema=vol.Schema({vol.Required(CONF_REFRESH_TOKEN): str}),
            errors=errors,
        )
