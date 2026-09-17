"""Authentication helpers for First Alert by Resideo — re-exported from pyresideo-firstalert."""

from resideo_firstalert_api import (
    AuthenticationError,
    ResideoAuth,
    build_authorize_url,
    exchange_code_for_tokens,
    generate_pkce_pair,
    parse_authorization_code,
)

__all__ = [
    "AuthenticationError",
    "ResideoAuth",
    "build_authorize_url",
    "exchange_code_for_tokens",
    "generate_pkce_pair",
    "parse_authorization_code",
]
