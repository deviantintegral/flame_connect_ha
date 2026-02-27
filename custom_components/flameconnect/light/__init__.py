"""FlameConnect light platform.

Provides three light entities per fireplace:
- Media light: RGBW light with effect support (media themes).
- Overhead light: RGBW overhead light.
- Log effect light: RGBW log effect light.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

from custom_components.flameconnect.entity import FlameConnectEntity
from flameconnect import FlameEffectParam, LightStatus, LogEffect, LogEffectParam, MediaTheme, RGBWColor
from homeassistant.components.light import ATTR_EFFECT, ATTR_RGBW_COLOR, LightEntity, LightEntityDescription
from homeassistant.components.light.const import ColorMode, LightEntityFeature

if TYPE_CHECKING:
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Mapping from effect name string to MediaTheme enum value.
_MEDIA_THEME_MAP: dict[str, MediaTheme] = {theme.name.lower().replace("_", " "): theme for theme in MediaTheme}

_MEDIA_LIGHT_DESCRIPTION = LightEntityDescription(
    key="media_light",
    translation_key="media_light",
    icon="mdi:led-strip-variant",
)

_OVERHEAD_LIGHT_DESCRIPTION = LightEntityDescription(
    key="overhead_light",
    translation_key="overhead_light",
    icon="mdi:ceiling-light",
)

_LOG_EFFECT_DESCRIPTION = LightEntityDescription(
    key="log_effect",
    translation_key="log_effect",
    icon="mdi:campfire",
)


def _rgbw_to_tuple(color: RGBWColor) -> tuple[int, int, int, int]:
    """Convert a library RGBWColor to a Home Assistant RGBW tuple."""
    return (color.red, color.green, color.blue, color.white)


def _tuple_to_rgbw(rgbw: tuple[int, int, int, int]) -> RGBWColor:
    """Convert a Home Assistant RGBW tuple to a library RGBWColor."""
    return RGBWColor(red=rgbw[0], green=rgbw[1], blue=rgbw[2], white=rgbw[3])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FlameConnectConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlameConnect light entities from a config entry."""
    coordinator = entry.runtime_data.coordinator
    entities: list[LightEntity] = []
    for fire in coordinator.fires:
        if fire.features.rgb_fuel_bed:
            entities.append(FlameConnectMediaLight(coordinator, _MEDIA_LIGHT_DESCRIPTION, fire))
        if fire.features.rgb_back_light:
            entities.append(FlameConnectOverheadLight(coordinator, _OVERHEAD_LIGHT_DESCRIPTION, fire))
        if fire.features.rgb_log_effect:
            entities.append(FlameConnectLogEffectLight(coordinator, _LOG_EFFECT_DESCRIPTION, fire))
    async_add_entities(entities)


class FlameConnectMediaLight(LightEntity, FlameConnectEntity):
    """Media light entity with RGBW colour and effect (media theme) support."""

    _attr_color_mode = ColorMode.RGBW
    _attr_supported_color_modes = {ColorMode.RGBW}
    _attr_supported_features = LightEntityFeature.EFFECT

    @property
    def is_on(self) -> bool | None:
        """Return True if the media light is on."""
        param = self._get_param(FlameEffectParam)
        if param is None:
            return None
        return param.media_light == LightStatus.ON

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return the current RGBW colour of the media light."""
        param = self._get_param(FlameEffectParam)
        if param is None:
            return None
        return _rgbw_to_tuple(param.media_color)

    @property
    def effect_list(self) -> list[str]:
        """Return the list of supported media theme effects."""
        return list(_MEDIA_THEME_MAP)

    @property
    def effect(self) -> str | None:
        """Return the currently active media theme effect."""
        param = self._get_param(FlameEffectParam)
        if param is None:
            return None
        return param.media_theme.name.lower().replace("_", " ")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the media light with optional colour and effect."""
        changes: dict[str, Any] = {"media_light": LightStatus.ON}
        rgbw: tuple[int, int, int, int] | None = kwargs.get(ATTR_RGBW_COLOR)
        if rgbw is not None:
            changes["media_color"] = _tuple_to_rgbw(rgbw)
        effect: str | None = kwargs.get(ATTR_EFFECT)
        if effect is not None:
            changes["media_theme"] = _MEDIA_THEME_MAP[effect]
        await self._write_flame_effect(**changes)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the media light."""
        await self._write_flame_effect(media_light=LightStatus.OFF)

    async def _write_flame_effect(self, **changes: Any) -> None:
        """Read-modify-write a FlameEffectParam for this fireplace."""
        client = self.coordinator.config_entry.runtime_data.client
        overview = await client.get_fire_overview(self._fire_id)
        param = next(p for p in overview.parameters if isinstance(p, FlameEffectParam))
        new_param = dataclasses.replace(param, **changes)
        await client.write_parameters(self._fire_id, [new_param])
        await self.coordinator.async_request_refresh()


class FlameConnectOverheadLight(LightEntity, FlameConnectEntity):
    """Overhead light entity with RGBW colour support.

    Uses the ``light_status`` field (not ``overhead_light``) for on/off state.
    """

    _attr_color_mode = ColorMode.RGBW
    _attr_supported_color_modes = {ColorMode.RGBW}

    @property
    def is_on(self) -> bool | None:
        """Return True if the overhead light is on."""
        param = self._get_param(FlameEffectParam)
        if param is None:
            return None
        return param.light_status == LightStatus.ON

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return the current RGBW colour of the overhead light."""
        param = self._get_param(FlameEffectParam)
        if param is None:
            return None
        return _rgbw_to_tuple(param.overhead_color)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the overhead light with optional colour."""
        changes: dict[str, Any] = {"light_status": LightStatus.ON}
        rgbw: tuple[int, int, int, int] | None = kwargs.get(ATTR_RGBW_COLOR)
        if rgbw is not None:
            changes["overhead_color"] = _tuple_to_rgbw(rgbw)
        await self._write_flame_effect(**changes)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the overhead light."""
        await self._write_flame_effect(light_status=LightStatus.OFF)

    async def _write_flame_effect(self, **changes: Any) -> None:
        """Read-modify-write a FlameEffectParam for this fireplace."""
        client = self.coordinator.config_entry.runtime_data.client
        overview = await client.get_fire_overview(self._fire_id)
        param = next(p for p in overview.parameters if isinstance(p, FlameEffectParam))
        new_param = dataclasses.replace(param, **changes)
        await client.write_parameters(self._fire_id, [new_param])
        await self.coordinator.async_request_refresh()


class FlameConnectLogEffectLight(LightEntity, FlameConnectEntity):
    """Log effect light entity with RGBW colour support."""

    _attr_color_mode = ColorMode.RGBW
    _attr_supported_color_modes = {ColorMode.RGBW}

    @property
    def is_on(self) -> bool | None:
        """Return True if the log effect is on."""
        param = self._get_param(LogEffectParam)
        if param is None:
            return None
        return param.log_effect == LogEffect.ON

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return the current RGBW colour of the log effect."""
        param = self._get_param(LogEffectParam)
        if param is None:
            return None
        return _rgbw_to_tuple(param.color)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the log effect with optional colour."""
        changes: dict[str, Any] = {"log_effect": LogEffect.ON}
        rgbw: tuple[int, int, int, int] | None = kwargs.get(ATTR_RGBW_COLOR)
        if rgbw is not None:
            changes["color"] = _tuple_to_rgbw(rgbw)
        await self._write_log_effect(**changes)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the log effect."""
        await self._write_log_effect(log_effect=LogEffect.OFF)

    async def _write_log_effect(self, **changes: Any) -> None:
        """Read-modify-write a LogEffectParam for this fireplace."""
        client = self.coordinator.config_entry.runtime_data.client
        overview = await client.get_fire_overview(self._fire_id)
        param = next(p for p in overview.parameters if isinstance(p, LogEffectParam))
        new_param = dataclasses.replace(param, **changes)
        await client.write_parameters(self._fire_id, [new_param])
        await self.coordinator.async_request_refresh()
