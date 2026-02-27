"""Token management for the FlameConnect integration.

Provides a factory function that creates an async token provider callable
suitable for use with flameconnect.TokenAuth. The provider handles MSAL
token cache deserialization, silent token acquisition, cache persistence
to config entry data, and proper error propagation.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

import msal

from custom_components.flameconnect.const import LOGGER
from flameconnect import AuthenticationError
from flameconnect.const import AUTHORITY, CLIENT_ID, SCOPES

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

CONF_TOKEN_CACHE = "token_cache"


def _build_msal_app(
    cache_data: str,
) -> tuple[msal.PublicClientApplication, msal.SerializableTokenCache]:
    """Build an MSAL PublicClientApplication with a deserialized token cache.

    This is a synchronous helper intended to be called via asyncio.to_thread().
    """
    cache = msal.SerializableTokenCache()
    cache.deserialize(cache_data)

    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        validate_authority=False,
        token_cache=cache,
    )
    return app, cache


def create_token_provider(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Callable[[], Coroutine[Any, Any, str]]:
    """Create an async token provider for the FlameConnect API.

    Returns an async callable that:
    1. Deserializes the MSAL token cache from config entry data.
    2. Attempts silent token acquisition (refresh).
    3. Persists updated cache state back to the config entry when rotated.
    4. Raises AuthenticationError if token acquisition fails.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry containing the serialized token cache.

    Returns:
        An async callable that returns a valid access token string.

    """

    async def get_token() -> str:
        """Acquire a valid access token, refreshing if necessary.

        Raises:
            AuthenticationError: If no accounts exist in the cache or
                silent token acquisition fails.

        """
        cache_data: str = entry.data[CONF_TOKEN_CACHE]

        # Build the MSAL app with deserialized cache (blocking I/O).
        app, cache = await asyncio.to_thread(_build_msal_app, cache_data)

        # Get accounts from the cache.
        accounts: list[dict[str, Any]] = app.get_accounts()
        if not accounts:
            LOGGER.debug("No accounts found in MSAL token cache")
            raise AuthenticationError("No accounts in token cache; re-authentication required")

        # Attempt silent token acquisition (may perform network I/O for refresh).
        LOGGER.debug("Attempting silent token acquisition")
        result: dict[str, Any] | None = await asyncio.to_thread(app.acquire_token_silent, SCOPES, account=accounts[0])

        if result is None or "error" in result:
            error_desc = ""
            if result is not None:
                error_desc = f": {result.get('error', 'unknown')} - {result.get('error_description', 'N/A')}"
            LOGGER.debug("Silent token acquisition failed%s", error_desc)
            raise AuthenticationError(f"Token refresh failed{error_desc}; re-authentication required")

        # Persist updated cache if the token was rotated.
        if cache.has_state_changed:
            LOGGER.debug("Token cache state changed, persisting to config entry")
            new_data = {**entry.data, CONF_TOKEN_CACHE: cache.serialize()}
            hass.config_entries.async_update_entry(entry, data=new_data)

        access_token: str = result["access_token"]
        LOGGER.debug("Token acquired successfully")
        return access_token

    return get_token
