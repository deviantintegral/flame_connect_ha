"""DataUpdateCoordinator for the FlameConnect integration.

Fetches fire discovery data once at setup, then polls per-fire overview
data on a 24-hour interval with random jitter to avoid thundering-herd
effects across multiple installations.
"""

from __future__ import annotations

import dataclasses
from datetime import timedelta
from random import randint
from typing import TYPE_CHECKING

from custom_components.flameconnect.const import DOMAIN, LOGGER
from flameconnect import ApiError, AuthenticationError, FireOverview, FlameConnectClient, FlameConnectError
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

if TYPE_CHECKING:
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from flameconnect import Fire
    from homeassistant.core import HomeAssistant


class FlameConnectDataUpdateCoordinator(DataUpdateCoordinator[dict[str, FireOverview]]):
    """Coordinator that polls FlameConnect cloud for fireplace data.

    Attributes:
        config_entry: The config entry for this integration instance.
        fires: List of discovered fires, populated by _async_setup.
    """

    config_entry: FlameConnectConfigEntry
    fires: list[Fire]

    def __init__(
        self,
        hass: HomeAssistant,
        client: FlameConnectClient,
        entry: FlameConnectConfigEntry,
    ) -> None:
        """Initialise the coordinator with a 24 h + jitter update interval."""
        jitter = timedelta(minutes=randint(0, 60))
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(hours=24) + jitter,
        )
        self.client = client

    async def _async_setup(self) -> None:
        """Discover all fires during first refresh."""
        self.fires = await self.client.get_fires()
        for fire in self.fires:
            enabled_features = [f.name for f in dataclasses.fields(fire.features) if getattr(fire.features, f.name)]
            LOGGER.debug(
                "Discovered fire %s (%s): with_heat=%s, brand=%s, model=%s, features=%s",
                fire.friendly_name,
                fire.fire_id,
                fire.with_heat,
                fire.brand,
                fire.product_type,
                ", ".join(enabled_features) if enabled_features else "none",
            )

    async def _async_update_data(self) -> dict[str, FireOverview]:
        """Fetch overview data for every discovered fire."""
        try:
            result: dict[str, FireOverview] = {}
            for fire in self.fires:
                result[fire.fire_id] = await self.client.get_fire_overview(fire.fire_id)
        except AuthenticationError as err:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "auth_expired",
                is_fixable=True,
                severity=ir.IssueSeverity.ERROR,
                translation_key="auth_expired",
            )
            raise ConfigEntryAuthFailed from err
        except (ApiError, FlameConnectError) as err:
            raise UpdateFailed(str(err)) from err
        else:
            return result
