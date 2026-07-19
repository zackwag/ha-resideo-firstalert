"""Authentication helpers for First Alert by Resideo."""

from __future__ import annotations

import hashlib
import html
import logging
import re
import secrets
from base64 import urlsafe_b64encode
from urllib.parse import parse_qs, urlparse

import aiohttp

from .const import OAUTH_CLIENT_ID, OAUTH_TOKEN_URL

_LOGGER = logging.getLogger(__name__)

# Auth0 endpoints
AUTH0_BASE_URL = "https://login.resideo.com"
AUTH0_AUTHORIZE_URL = f"{AUTH0_BASE_URL}/authorize"
AUTH0_LOGIN_URL = f"{AUTH0_BASE_URL}/usernamepassword/login"
AUTH0_CALLBACK_URL = f"{AUTH0_BASE_URL}/login/callback"

# OAuth configuration
REDIRECT_URI = "com.resideo.firstalert://login.resideo.com/ios/com.resideo.firstalert/callback"
AUDIENCE = "https://resideo-prod.auth0.com/api/v2/"
SCOPE = "openid profile email offline_access"
TENANT = "resideo-prod"
CONNECTION = "Username-Password-Authentication"

# Auth0-Client header values: base64-encoded {"name": ..., "version": ...}
# library-identification JSON that Auth0's SDKs send with every request for
# their own telemetry. Not credentials - just identify which Auth0 client
# library and version made the request. Decode them yourself to check:
#   base64.b64decode(AUTH0_CLIENT_BROWSER)
AUTH0_CLIENT_BROWSER = "eyJuYW1lIjoiYXV0aDAuanMtdWxwIiwidmVyc2lvbiI6IjkuMTMuMiJ9"
AUTH0_CLIENT_APP = "eyJ2ZXJzaW9uIjoiMS4xNC4wIiwibmFtZSI6ImF1dGgwLWZsdXR0ZXIiLCJlbnYiOnsiY29yZSI6IjIuMTAuMCIsImlPUyI6IjI2LjEiLCJzd2lmdCI6IjUueCJ9fQ"


class AuthenticationError(Exception):
    """Authentication error."""


class ResideoAuth:
    """Handle Resideo Auth0 authentication flow."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the auth handler."""
        self._session = session
        self._code_verifier: str | None = None
        self._code_challenge: str | None = None
        self._state: str | None = None

    def _generate_pkce(self) -> None:
        """Generate PKCE code_verifier and code_challenge."""
        # Generate 32 random bytes, base64url encode, remove padding
        verifier_bytes = secrets.token_bytes(32)
        self._code_verifier = urlsafe_b64encode(verifier_bytes).decode("utf-8").rstrip("=")

        # SHA256 hash of verifier, base64url encode, remove padding
        challenge_bytes = hashlib.sha256(self._code_verifier.encode("ascii")).digest()
        self._code_challenge = urlsafe_b64encode(challenge_bytes).decode("utf-8").rstrip("=")

        # Generate random state
        state_bytes = secrets.token_bytes(32)
        self._state = urlsafe_b64encode(state_bytes).decode("utf-8").rstrip("=")

    async def authenticate(self, email: str, password: str) -> dict:
        """Authenticate with email and password, return tokens."""
        self._generate_pkce()

        # Create a cookie jar for this auth flow
        jar = aiohttp.CookieJar()

        async with aiohttp.ClientSession(cookie_jar=jar) as session:
            # Step 1: Initial authorize request
            _LOGGER.debug("Step 1: Starting authorization flow")
            auth0_state = await self._step1_authorize(session)

            # Step 2: Get login page and CSRF token
            _LOGGER.debug("Step 2: Getting login page")
            csrf_token = await self._step2_get_login_page(session, auth0_state)

            # Step 3: Submit credentials
            _LOGGER.debug("Step 3: Submitting credentials")
            wresult, wctx = await self._step3_submit_credentials(
                session, auth0_state, csrf_token, email, password
            )

            # Step 4: Post to callback
            _LOGGER.debug("Step 4: Posting to callback")
            resume_url = await self._step4_callback(session, wresult, wctx)

            # Step 5: Resume authorization and get code
            _LOGGER.debug("Step 5: Resuming authorization")
            auth_code = await self._step5_resume(session, resume_url)

            # Step 6: Exchange code for tokens
            _LOGGER.debug("Step 6: Exchanging code for tokens")
            tokens = await self._step6_exchange_code(auth_code)

            return tokens

    async def _step1_authorize(self, session: aiohttp.ClientSession) -> str:
        """Start the authorization flow, return auth0_state."""
        params = {
            "state": self._state,
            "scope": SCOPE,
            "signUpUrl": "https://myid.resideo.com/sign-up?userType=consumer",
            "client_id": OAUTH_CLIENT_ID,
            "code_challenge_method": "S256",
            "response_type": "code",
            "max_age": "0",
            "audience": AUDIENCE,
            "redirect_uri": REDIRECT_URI,
            "code_challenge": self._code_challenge,
            "prompt": "login",
            "auth0Client": AUTH0_CLIENT_APP,
        }

        async with session.get(
            AUTH0_AUTHORIZE_URL,
            params=params,
            allow_redirects=False,
            headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)"},
        ) as resp:
            if resp.status != 302:
                raise AuthenticationError(f"Expected redirect, got {resp.status}")

            location = resp.headers.get("Location", "")
            if not location:
                raise AuthenticationError("No redirect location in authorize response")

            # Extract auth0_state from the redirect URL
            parsed = urlparse(location)
            query_params = parse_qs(parsed.query)
            auth0_state = query_params.get("state", [None])[0]

            if not auth0_state:
                raise AuthenticationError("No state in authorize redirect")

            return auth0_state

    async def _step2_get_login_page(
        self, session: aiohttp.ClientSession, auth0_state: str
    ) -> str:
        """Get the login page and extract CSRF token."""
        login_url = f"{AUTH0_BASE_URL}/login"
        params = {"state": auth0_state}

        async with session.get(
            login_url,
            params=params,
            headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)"},
        ) as resp:
            if resp.status != 200:
                raise AuthenticationError(f"Failed to get login page: {resp.status}")

            # CSRF token is in Set-Cookie header with path=/usernamepassword/login
            # Extract it from the response headers directly
            csrf_token = None
            for cookie in resp.cookies.values():
                if cookie.key == "_csrf":
                    csrf_token = cookie.value
                    break

            # Also check the cookie jar with the specific path
            if not csrf_token:
                csrf_cookie = session.cookie_jar.filter_cookies(AUTH0_LOGIN_URL).get("_csrf")
                if csrf_cookie:
                    csrf_token = csrf_cookie.value

            if not csrf_token:
                raise AuthenticationError("No CSRF token in cookies")

            return csrf_token

    async def _step3_submit_credentials(
        self,
        session: aiohttp.ClientSession,
        auth0_state: str,
        csrf_token: str,
        email: str,
        password: str,
    ) -> tuple[str, str]:
        """Submit username/password, return wresult and wctx."""
        login_data = {
            "client_id": OAUTH_CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "tenant": TENANT,
            "response_type": "code",
            "scope": SCOPE,
            "audience": AUDIENCE,
            "_csrf": csrf_token,
            "state": auth0_state,
            "_intstate": "deprecated",
            "username": email,
            "password": password,
            "connection": CONNECTION,
        }

        headers = {
            "Auth0-Client": AUTH0_CLIENT_BROWSER,
            "Origin": AUTH0_BASE_URL,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)",
        }

        async with session.post(
            AUTH0_LOGIN_URL,
            json=login_data,
            headers=headers,
        ) as resp:
            text = await resp.text()

            if resp.status != 200:
                # Check for specific error messages
                if "Wrong email or password" in text or "invalid_grant" in text:
                    raise AuthenticationError("Invalid email or password")
                raise AuthenticationError(f"Login failed with status {resp.status}")

            # Extract wresult from HTML form
            wresult_match = re.search(r'name="wresult"\s+value="([^"]+)"', text)
            if not wresult_match:
                # Check for error in response
                if "Wrong email or password" in text:
                    raise AuthenticationError("Invalid email or password")
                _LOGGER.debug("Login response (first 1000 chars): %s", text[:1000])
                raise AuthenticationError("Could not extract wresult from login response")

            # Decode HTML entities in wresult
            wresult = html.unescape(wresult_match.group(1))

            # Extract wctx if present
            wctx_match = re.search(r'name="wctx"\s+value="([^"]+)"', text)
            wctx = html.unescape(wctx_match.group(1)) if wctx_match else ""

            _LOGGER.debug("Step 3: Got wresult (len=%d) and wctx (len=%d)", len(wresult), len(wctx))

            return wresult, wctx

    async def _step4_callback(
        self, session: aiohttp.ClientSession, wresult: str, wctx: str
    ) -> str:
        """Post to callback, return resume URL."""
        # Use simple dict for form data
        form_data = {
            "wa": "wsignin1.0",
            "wresult": wresult,
        }
        if wctx:
            form_data["wctx"] = wctx

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": AUTH0_BASE_URL,
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)",
        }

        _LOGGER.debug("Step 4: wresult length=%d, wctx length=%d", len(wresult), len(wctx) if wctx else 0)

        async with session.post(
            AUTH0_CALLBACK_URL,
            data=form_data,
            headers=headers,
            allow_redirects=False,
        ) as resp:
            if resp.status != 302:
                text = await resp.text()
                _LOGGER.debug("Callback response: %s", text[:500] if text else "empty")
                raise AuthenticationError(f"Expected redirect from callback, got {resp.status}")

            location = resp.headers.get("Location", "")
            if not location:
                raise AuthenticationError("No redirect location from callback")

            return location

    async def _step5_resume(self, session: aiohttp.ClientSession, resume_url: str) -> str:
        """Resume authorization and extract auth code."""
        if not resume_url.startswith("http"):
            resume_url = AUTH0_BASE_URL + resume_url

        async with session.get(
            resume_url,
            allow_redirects=False,
            headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)"},
        ) as resp:
            if resp.status != 302:
                raise AuthenticationError(f"Expected redirect from resume, got {resp.status}")

            location = resp.headers.get("Location", "")
            if not location:
                raise AuthenticationError("No redirect location from resume")

            # Extract authorization code from callback URL
            parsed = urlparse(location)
            query_params = parse_qs(parsed.query)

            auth_code = query_params.get("code", [None])[0]
            returned_state = query_params.get("state", [None])[0]

            if not auth_code:
                # Check for error
                error = query_params.get("error", [None])[0]
                error_desc = query_params.get("error_description", ["Unknown error"])[0]
                raise AuthenticationError(f"Authorization failed: {error} - {error_desc}")

            # Verify state matches
            if returned_state != self._state:
                raise AuthenticationError("State mismatch - possible security issue")

            return auth_code

    async def _step6_exchange_code(self, auth_code: str) -> dict:
        """Exchange authorization code for tokens."""
        token_data = {
            "client_id": OAUTH_CLIENT_ID,
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": self._code_verifier,
            "grant_type": "authorization_code",
        }

        headers = {
            "Auth0-Client": AUTH0_CLIENT_APP,
            "Content-Type": "application/json",
        }

        async with self._session.post(
            OAUTH_TOKEN_URL,
            json=token_data,
            headers=headers,
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise AuthenticationError(f"Token exchange failed: {resp.status} - {text}")

            return await resp.json()
