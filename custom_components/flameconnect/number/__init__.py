"""Number platform for FlameConnect."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.flameconnect.entity import FlameConnectEntity
from flameconnect import FlameEffectParam, HeatMode, HeatParam, SoundParam, TimerParam, TimerStatus
from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import EntityCategory, UnitOfTime

if TYPE_CHECKING:
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


_FEATURE_REQUIREMENTS: dict[str, str] = {
    "flame_speed": "flame_fan_speed",
    "timer_duration": "count_down_timer",
    "boost_duration": "power_boost",
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
        icon="mdi:fire-circle",
    ),
    NumberEntityDescription(
        key="timer_duration",
        translation_key="timer_duration",
        native_min_value=1,
        native_max_value=480,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer-sand",
    ),
    NumberEntityDescription(
        key="boost_duration",
        translation_key="boost_duration",
        native_min_value=1,
        native_max_value=20,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:rocket-launch",
    ),
    NumberEntityDescription(
        key="sound_volume",
        translation_key="sound_volume",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:volume-high",
    ),
    NumberEntityDescription(
        key="sound_file",
        translation_key="sound_file",
        native_min_value=0,
        native_max_value=255,
        native_step=1,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:music-note",
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
            stored = self.coordinator.timer_durations.get(self._fire_id)
            if stored is not None:
                return float(stored)
            param = self._get_param(TimerParam)
            if param is None:
                return None
            return float(param.duration)

        if key == "boost_duration":
            stored = self.coordinator.boost_durations.get(self._fire_id)
            if stored is not None:
                return float(stored)
            heat = self._get_param(HeatParam)
            if heat is None:
                return None
            return float(heat.boost_duration)

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
        """Set the value.

        Timer duration is stored locally and only sent to the API when
        the timer switch is turned on.  Other values use debounced
        writes to coalesce rapid slider changes.
        """
        key = self.entity_description.key

        if key == "timer_duration":
            duration = int(value)
            self.coordinator.timer_durations[self._fire_id] = duration
            self.async_write_ha_state()
            current = self._get_param(TimerParam)
            if current and current.timer_status == TimerStatus.ENABLED:
                await self.coordinator.async_write_fields_debounced(
                    self._fire_id, TimerParam, timer_status=TimerStatus.ENABLED, duration=duration
                )
            return

        if key == "boost_duration":
            duration = int(value)
            self.coordinator.boost_durations[self._fire_id] = duration
            self.async_write_ha_state()
            heat = self._get_param(HeatParam)
            if heat and heat.heat_mode == HeatMode.BOOST:
                await self.coordinator.async_write_fields_debounced(
                    self._fire_id, HeatParam, heat_mode=HeatMode.BOOST, boost_duration=duration
                )
            return

        if key == "flame_speed":
            await self.coordinator.async_write_fields_debounced(self._fire_id, FlameEffectParam, flame_speed=int(value))
        elif key == "sound_volume":
            await self.coordinator.async_write_fields_debounced(self._fire_id, SoundParam, volume=int(value))
        elif key == "sound_file":
            await self.coordinator.async_write_fields_debounced(self._fire_id, SoundParam, sound_file=int(value))
