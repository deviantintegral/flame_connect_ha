"""Fireplace validation for config flow.

Verifies that the user's account has at least one WiFi-connected fireplace
by fetching the fire list and checking each one for a valid overview.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.flameconnect.const import LOGGER

if TYPE_CHECKING:
    from flameconnect import FlameConnectClient


class NoWifiFireplacesError(Exception):
    """Raised when no WiFi-connected fireplaces are found."""


async def validate_fireplaces(client: FlameConnectClient) -> None:
    """Check that the account has at least one WiFi-connected fireplace.

    Fetches the fire list and attempts to get an overview for each one.
    Fires whose overview fails (e.g. Bluetooth-only devices where
    WifiFireOverview is null) are skipped.

    Args:
        client: An authenticated FlameConnectClient.

    Raises:
        NoWifiFireplacesError: If no fireplaces return a valid WiFi overview.
        ApiError: If the API request itself fails.
        FlameConnectError: If a library-level error occurs.

    """
    fires = await client.get_fires()

    if not fires:
        LOGGER.debug("No fireplaces found in account")
        raise NoWifiFireplacesError

    for fire in fires:
        try:
            await client.get_fire_overview(fire.fire_id)
        except (TypeError, KeyError):
            LOGGER.debug(
                "Fire %s (%s) has no WiFi overview, skipping",
                fire.friendly_name,
                fire.fire_id,
            )
            continue
        else:
            # At least one fire has a valid WiFi overview.
            return

    LOGGER.debug("None of the %d fireplaces have a WiFi overview", len(fires))
    raise NoWifiFireplacesError
