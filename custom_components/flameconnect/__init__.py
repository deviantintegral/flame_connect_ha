"""Custom integration to integrate FlameConnect with Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flameconnect import FlameConnectClient, TokenAuth
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import create_token_provider
from .const import PLATFORMS
from .coordinator import FlameConnectDataUpdateCoordinator
from .data import FlameConnectData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import FlameConnectConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FlameConnectConfigEntry,
) -> bool:
    """Set up FlameConnect from a config entry."""
    get_token = create_token_provider(hass, entry)
    client = FlameConnectClient(
        auth=TokenAuth(get_token),
        session=async_get_clientsession(hass),
    )
    coordinator = FlameConnectDataUpdateCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = FlameConnectData(client=client, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: FlameConnectConfigEntry,
) -> bool:
    """Unload a FlameConnect config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
