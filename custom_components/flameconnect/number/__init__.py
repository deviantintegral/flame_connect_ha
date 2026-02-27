"""Number platform for FlameConnect."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from custom_components.flameconnect.entity import FlameConnectEntity
from flameconnect import FlameEffectParam, SoundParam, TimerParam
from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import EntityCategory, UnitOfTime

if TYPE_CHECKING:
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


_FEATURE_REQUIREMENTS: dict[str, str] = {
    "flame_speed": "flame_fan_speed",
    "timer_duration": "count_down_timer",
    "sound_volume": "sound",
    "sound_file": "sound",
}

NUMBER_DESCRIPTIONS: tuple[NumberEntityDescription, ...] = (
    NumberEntityDescription(
        key="flame_speed",
        translation_key="flame_speed",
        native_min_value=1,
        native_max_value=5,
        native_step=1,
    ),
    NumberEntityDescription(
        key="timer_duration",
        translation_key="timer_duration",
        native_min_value=1,
        native_max_value=480,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    NumberEntityDescription(
        key="sound_volume",
        translation_key="sound_volume",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.CONFIG,
    ),
    NumberEntityDescription(
        key="sound_file",
        translation_key="sound_file",
        native_min_value=0,
        native_max_value=255,
        native_step=1,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FlameConnectConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlameConnect number entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        FlameConnectNumberEntity(coordinator, description, fire)
        for description in NUMBER_DESCRIPTIONS
        for fire in coordinator.fires
        if getattr(fire.features, _FEATURE_REQUIREMENTS[description.key], False)
    )


class FlameConnectNumberEntity(NumberEntity, FlameConnectEntity):
    """Number entity for FlameConnect fireplace settings."""

    entity_description: NumberEntityDescription

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        key = self.entity_description.key

        if key == "flame_speed":
            param = self._get_param(FlameEffectParam)
            if param is None:
                return None
            return float(param.flame_speed)

        if key == "timer_duration":
            param = self._get_param(TimerParam)
            if param is None:
                return None
            return float(param.duration)

        if key == "sound_volume":
            param = self._get_param(SoundParam)
            if param is None:
                return None
            return float(param.volume)

        if key == "sound_file":
            param = self._get_param(SoundParam)
            if param is None:
                return None
            return float(param.sound_file)

        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        client = self.coordinator.config_entry.runtime_data.client
        key = self.entity_description.key

        if key == "flame_speed":
            overview = await client.get_fire_overview(self._fire_id)
            param = next(p for p in overview.parameters if isinstance(p, FlameEffectParam))
            new_param = dataclasses.replace(param, flame_speed=int(value))
            await client.write_parameters(self._fire_id, [new_param])

        elif key == "timer_duration":
            overview = await client.get_fire_overview(self._fire_id)
            current = next(p for p in overview.parameters if isinstance(p, TimerParam))
            new_param = TimerParam(timer_status=current.timer_status, duration=int(value))
            await client.write_parameters(self._fire_id, [new_param])

        elif key == "sound_volume":
            overview = await client.get_fire_overview(self._fire_id)
            current = next(p for p in overview.parameters if isinstance(p, SoundParam))
            new_param = dataclasses.replace(current, volume=int(value))
            await client.write_parameters(self._fire_id, [new_param])

        elif key == "sound_file":
            overview = await client.get_fire_overview(self._fire_id)
            current = next(p for p in overview.parameters if isinstance(p, SoundParam))
            new_param = dataclasses.replace(current, sound_file=int(value))
            await client.write_parameters(self._fire_id, [new_param])

        await self.coordinator.async_request_refresh()
