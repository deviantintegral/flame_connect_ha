"""Diagnostics support for FlameConnect."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.redact import async_redact_data

from .api import CONF_TOKEN_CACHE

TO_REDACT = {CONF_TOKEN_CACHE}

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import FlameConnectConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: FlameConnectConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return async_redact_data(dict(entry.data), TO_REDACT)
