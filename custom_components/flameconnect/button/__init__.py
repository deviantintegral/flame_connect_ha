"""Button platform for FlameConnect."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.flameconnect.entity import FlameConnectEntity
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

if TYPE_CHECKING:
    from custom_components.flameconnect.coordinator import FlameConnectDataUpdateCoordinator
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from flameconnect import Fire
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

BUTTON_DESCRIPTIONS: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="refresh",
        name="Refresh Data",
        icon="mdi:refresh",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FlameConnectConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlameConnect button entities."""
    data = entry.runtime_data
    coordinator = data.coordinator

    entities: list[ButtonEntity] = []
    for fire in coordinator.fires:
        entities.extend(
            FlameConnectRefreshButton(coordinator, description, fire) for description in BUTTON_DESCRIPTIONS
        )

    async_add_entities(entities)


class FlameConnectRefreshButton(ButtonEntity, FlameConnectEntity):
    """Button to trigger a data refresh from the FlameConnect cloud."""

    def __init__(
        self,
        coordinator: FlameConnectDataUpdateCoordinator,
        description: ButtonEntityDescription,
        fire: Fire,
    ) -> None:
        """Initialise the refresh button."""
        super().__init__(coordinator, description, fire)

    @property
    def available(self) -> bool:
        """Return True always, regardless of coordinator health.

        This button is the only in-band way to recover a coordinator that
        has stopped updating.  Inheriting coordinator availability would
        disable it exactly when it is needed, because Home Assistant
        refuses service calls to unavailable entities.
        """
        return True

    async def async_press(self) -> None:
        """Handle the button press to refresh coordinator data."""
        await self.coordinator.async_refresh()
