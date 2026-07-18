"""Tests for the PKCE helpers in auth.py (no network, no Home Assistant)."""

from __future__ import annotations

import base64
import hashlib
from unittest.mock import Mock

from resideo_firstalert.auth import ResideoAuth


def test_generate_pkce_verifier_is_valid_length_and_charset() -> None:
    auth = ResideoAuth(Mock())
    auth._generate_pkce()

    # RFC 7636: code_verifier must be 43-128 characters, unreserved charset.
    assert 43 <= len(auth._code_verifier) <= 128
    assert all(c not in "+/=" for c in auth._code_verifier)


def test_generate_pkce_challenge_is_s256_of_verifier() -> None:
    auth = ResideoAuth(Mock())
    auth._generate_pkce()

    expected_digest = hashlib.sha256(auth._code_verifier.encode("ascii")).digest()
    expected_challenge = (
        base64.urlsafe_b64encode(expected_digest).decode("utf-8").rstrip("=")
    )
    assert auth._code_challenge == expected_challenge


def test_generate_pkce_state_is_random_and_nonempty() -> None:
    auth = ResideoAuth(Mock())

    auth._generate_pkce()
    first_state = auth._state
    auth._generate_pkce()
    second_state = auth._state

    assert first_state
    assert second_state
    assert first_state != second_state
