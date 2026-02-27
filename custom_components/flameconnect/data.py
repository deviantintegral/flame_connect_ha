"""Custom types for FlameConnect.

Defines the runtime data structure attached to each config entry.
Access pattern: entry.runtime_data.client / entry.runtime_data.coordinator
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from flameconnect import FlameConnectClient

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import FlameConnectDataUpdateCoordinator

type FlameConnectConfigEntry = ConfigEntry[FlameConnectData]


@dataclass
class FlameConnectData:
    """Runtime data for FlameConnect config entries.

    Stored as entry.runtime_data after successful setup.
    Provides typed access to the API client and coordinator instances.
    """

    client: FlameConnectClient
    coordinator: FlameConnectDataUpdateCoordinator
