"""Application credentials for First Alert by Resideo."""

from __future__ import annotations

import base64
import hashlib
import secrets
from typing import Any

from homeassistant.components.application_credentials import (
    AuthImplementation,
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .const import OAUTH_AUDIENCE, OAUTH_AUTHORIZE_URL, OAUTH_TOKEN_URL


class ResideoOAuth2Implementation(AuthImplementation):
    """Resideo OAuth2 implementation using PKCE."""

    def __init__(
        self,
        hass: HomeAssistant,
        domain: str,
        client_credential: ClientCredential,
        authorization_server: AuthorizationServer,
    ) -> None:
        """Initialize the OAuth2 implementation."""
        super().__init__(
            hass=hass,
            auth_domain=domain,
            credential=client_credential,
            authorization_server=authorization_server,
        )
        self._code_verifier: str | None = None

    def _generate_pkce(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        # Generate a random code verifier (43-128 characters)
        code_verifier = secrets.token_urlsafe(32)

        # Create the code challenge using S256 method
        code_challenge_digest = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge_digest).decode().rstrip("=")

        return code_verifier, code_challenge

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Return extra data for the authorization request."""
        # Generate PKCE values
        self._code_verifier, code_challenge = self._generate_pkce()

        return {
            "audience": OAUTH_AUDIENCE,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "prompt": "login",
        }

    async def async_resolve_external_data(self, external_data: Any) -> dict[str, Any]:
        """Resolve external data to tokens."""
        # The external_data contains the authorization code from the callback
        return {
            "code": external_data["code"],
            "code_verifier": self._code_verifier,
        }

    async def _async_refresh_token(self, token: dict[str, Any]) -> dict[str, Any]:
        """Refresh the access token."""
        new_token = await self._token_request(
            {
                "grant_type": "refresh_token",
                "refresh_token": token["refresh_token"],
                "client_id": self.client_id,
            }
        )
        # Preserve the refresh token if not returned
        if "refresh_token" not in new_token:
            new_token["refresh_token"] = token["refresh_token"]
        return new_token

    async def _async_token_request(self, data: dict[str, Any]) -> dict[str, Any]:
        """Make a token request."""
        # Add client_id to all token requests
        data["client_id"] = self.client_id
        return await super()._async_token_request(data)


async def async_get_auth_implementation(
    hass: HomeAssistant,
    auth_domain: str,
    credential: ClientCredential,
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return the auth implementation for Resideo."""
    return ResideoOAuth2Implementation(
        hass,
        auth_domain,
        credential,
        AuthorizationServer(
            authorize_url=OAUTH_AUTHORIZE_URL,
            token_url=OAUTH_TOKEN_URL,
        ),
    )


async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Return description placeholders for the credentials form."""
    return {
        "more_info_url": "https://github.com/zackwag/ha-resideo-firstalert#oauth-setup",
        "oauth_consent_url": OAUTH_AUTHORIZE_URL,
        "oauth_creds_url": "https://github.com/zackwag/ha-resideo-firstalert#getting-started",
    }
