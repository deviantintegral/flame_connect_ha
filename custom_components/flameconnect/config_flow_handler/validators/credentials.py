"""Credential validators for flameconnect."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def validate_credentials(hass: HomeAssistant, username: str, password: str) -> None:
    """Validate user credentials.

    TODO: Will be implemented when the API client is available (Task 04).

    Args:
        hass: Home Assistant instance.
        username: The username to validate.
        password: The password to validate.

    """
