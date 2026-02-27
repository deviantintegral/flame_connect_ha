"""Select platform for FlameConnect."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.flameconnect.entity import FlameConnectEntity
from flameconnect import Brightness, FlameColor, FlameEffectParam, MediaTheme
from homeassistant.components.select import SelectEntity, SelectEntityDescription

if TYPE_CHECKING:
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


def _enum_to_options(enum_type: type[FlameColor | Brightness | MediaTheme]) -> list[str]:
    """Convert an enum type to a list of human-readable option strings."""
    return [member.name.lower() for member in enum_type]


FLAME_COLOR_OPTIONS = _enum_to_options(FlameColor)
BRIGHTNESS_OPTIONS = _enum_to_options(Brightness)
MEDIA_THEME_OPTIONS = _enum_to_options(MediaTheme)


_FEATURE_REQUIREMENTS: dict[str, str] = {
    "flame_color": "rgb_flame_accent",
    "brightness": "flame_dimming",
    "media_theme": "moods",
}

SELECT_DESCRIPTIONS: tuple[SelectEntityDescription, ...] = (
    SelectEntityDescription(
        key="flame_color",
        translation_key="flame_color",
        options=FLAME_COLOR_OPTIONS,
        icon="mdi:palette",
    ),
    SelectEntityDescription(
        key="brightness",
        translation_key="brightness",
        options=BRIGHTNESS_OPTIONS,
        icon="mdi:brightness-6",
    ),
    SelectEntityDescription(
        key="media_theme",
        translation_key="media_theme",
        options=MEDIA_THEME_OPTIONS,
        icon="mdi:palette-swatch-variant",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FlameConnectConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlameConnect select entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        FlameConnectSelectEntity(coordinator, description, fire)
        for description in SELECT_DESCRIPTIONS
        for fire in coordinator.fires
        if getattr(fire.features, _FEATURE_REQUIREMENTS[description.key], False)
    )


class FlameConnectSelectEntity(SelectEntity, FlameConnectEntity):
    """Select entity for FlameConnect fireplace settings."""

    entity_description: SelectEntityDescription

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        param = self._get_param(FlameEffectParam)
        if param is None:
            return None

        key = self.entity_description.key
        if key == "flame_color":
            return param.flame_color.name.lower()
        if key == "brightness":
            return param.brightness.name.lower()
        if key == "media_theme":
            return param.media_theme.name.lower()
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        key = self.entity_description.key
        enum_value = option.upper().replace(" ", "_")

        if key == "flame_color":
            await self.coordinator.async_write_fields(
                self._fire_id, FlameEffectParam, flame_color=FlameColor[enum_value]
            )
        elif key == "brightness":
            await self.coordinator.async_write_fields(
                self._fire_id, FlameEffectParam, brightness=Brightness[enum_value]
            )
        elif key == "media_theme":
            await self.coordinator.async_write_fields(
                self._fire_id, FlameEffectParam, media_theme=MediaTheme[enum_value]
            )
