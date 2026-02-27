"""Credential validation via Azure AD B2C for flameconnect."""

from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlparse

import msal

from flameconnect import AuthenticationError  # type: ignore[attr-defined]
from flameconnect.b2c_login import b2c_login_with_credentials  # type: ignore[import-not-found]
from flameconnect.const import AUTHORITY, CLIENT_ID, SCOPES  # type: ignore[attr-defined]


async def validate_credentials(email: str, password: str) -> str:
    """Authenticate via Azure AD B2C and return a serialized MSAL token cache.

    Creates an MSAL auth code flow, uses flameconnect's b2c_login helper to
    perform the browser-less B2C sign-in, then exchanges the resulting auth
    code for tokens.

    Args:
        email: User's email address.
        password: User's password.

    Returns:
        The serialized MSAL token cache string.

    Raises:
        AuthenticationError: If authentication fails (invalid credentials).

    """
    cache = msal.SerializableTokenCache()
    app = await asyncio.to_thread(
        msal.PublicClientApplication,
        CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache,
    )

    flow: dict = await asyncio.to_thread(
        app.initiate_auth_code_flow,
        scopes=SCOPES,
        redirect_uri=f"msal{CLIENT_ID}://auth",
    )

    auth_uri: str = flow["auth_uri"]

    redirect_url = await b2c_login_with_credentials(
        auth_uri,
        email,
        password,
    )

    parsed = urlparse(redirect_url)
    auth_response: dict[str, str] = {k: v[0] for k, v in parse_qs(parsed.query).items()}

    result: dict = await asyncio.to_thread(
        app.acquire_token_by_auth_code_flow,
        flow,
        auth_response,
    )

    if "error" in result:
        raise AuthenticationError(result.get("error_description", result["error"]))

    serialized: str = cache.serialize()
    return serialized
