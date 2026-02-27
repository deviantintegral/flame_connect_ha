"""Switch platform for FlameConnect.

Provides five switches for fireplace control:
- Power (on/off via dedicated client methods)
- Flame effect (enable/disable flame effect)
- Pulsating effect (enable/disable pulsating effect)
- Ambient sensor (enable/disable ambient light sensor)
- Timer (enable/disable the built-in timer)
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

from custom_components.flameconnect.entity import FlameConnectEntity
from flameconnect import (
    FireMode,
    FlameEffect,
    FlameEffectParam,
    LightStatus,
    ModeParam,
    PulsatingEffect,
    TimerParam,
    TimerStatus,
)
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

if TYPE_CHECKING:
    from custom_components.flameconnect.coordinator import FlameConnectDataUpdateCoordinator
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from flameconnect import Fire
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

SWITCH_DESCRIPTIONS: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="power",
        name="Power",
        icon="mdi:fireplace",
    ),
    SwitchEntityDescription(
        key="flame_effect",
        name="Flame effect",
        icon="mdi:fire",
    ),
    SwitchEntityDescription(
        key="pulsating_effect",
        name="Pulsating effect",
        icon="mdi:pulse",
    ),
    SwitchEntityDescription(
        key="ambient_sensor",
        name="Ambient sensor",
        icon="mdi:brightness-auto",
    ),
    SwitchEntityDescription(
        key="timer",
        name="Timer",
        icon="mdi:timer-outline",
    ),
)

_SWITCH_CLASSES: dict[str, type[FlameConnectSwitchBase]] = {}
"""Registry populated after all classes are defined."""

_FEATURE_REQUIREMENTS: dict[str, str] = {
    "ambient_sensor": "pir_toggle_smart_sense",
    "timer": "count_down_timer",
}
"""Map of switch keys to required ``FireFeatures`` attribute names.

Switches whose key appears here are only created when the corresponding
feature flag on the ``Fire`` object is ``True``.  Switches not listed
are always created.
"""


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FlameConnectConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlameConnect switch entities from a config entry."""
    data = entry.runtime_data
    coordinator = data.coordinator
    entities: list[SwitchEntity] = []
    for fire in coordinator.fires:
        for description in SWITCH_DESCRIPTIONS:
            feature_attr = _FEATURE_REQUIREMENTS.get(description.key)
            if feature_attr is not None and not getattr(fire.features, feature_attr):
                continue
            cls = _SWITCH_CLASSES[description.key]
            entities.append(cls(coordinator, description, fire))
    async_add_entities(entities)


class FlameConnectSwitchBase(SwitchEntity, FlameConnectEntity):
    """Base class for all FlameConnect switches."""

    def __init__(
        self,
        coordinator: FlameConnectDataUpdateCoordinator,
        description: SwitchEntityDescription,
        fire: Fire,
    ) -> None:
        """Initialise the switch entity."""
        super().__init__(coordinator, description, fire)


class FlameConnectPowerSwitch(FlameConnectSwitchBase):
    """Switch to turn the fireplace on and off."""

    @property
    def is_on(self) -> bool | None:
        """Return True if the fireplace is in manual (on) mode."""
        param = self._get_param(ModeParam)
        if param is None:
            return None
        return param.mode == FireMode.MANUAL

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the fireplace on."""
        client = self.coordinator.config_entry.runtime_data.client
        await client.turn_on(self._fire_id)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fireplace off."""
        client = self.coordinator.config_entry.runtime_data.client
        await client.turn_off(self._fire_id)
        await self.coordinator.async_request_refresh()


class FlameConnectFlameEffectSwitch(FlameConnectSwitchBase):
    """Switch to enable or disable the flame effect."""

    @property
    def is_on(self) -> bool | None:
        """Return True if the flame effect is enabled."""
        param = self._get_param(FlameEffectParam)
        if param is None:
            return None
        return param.flame_effect == FlameEffect.ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the flame effect."""
        await self._set_flame_effect(FlameEffect.ON)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the flame effect."""
        await self._set_flame_effect(FlameEffect.OFF)

    async def _set_flame_effect(self, value: FlameEffect) -> None:
        """Write the flame effect parameter using read-before-write."""
        client = self.coordinator.config_entry.runtime_data.client
        overview = await client.get_fire_overview(self._fire_id)
        param = next(p for p in overview.parameters if isinstance(p, FlameEffectParam))
        new_param = dataclasses.replace(param, flame_effect=value)
        await client.write_parameters(self._fire_id, [new_param])
        await self.coordinator.async_request_refresh()


class FlameConnectPulsatingEffectSwitch(FlameConnectSwitchBase):
    """Switch to enable or disable the pulsating effect."""

    @property
    def is_on(self) -> bool | None:
        """Return True if the pulsating effect is enabled."""
        param = self._get_param(FlameEffectParam)
        if param is None:
            return None
        return param.pulsating_effect == PulsatingEffect.ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the pulsating effect."""
        await self._set_pulsating_effect(PulsatingEffect.ON)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the pulsating effect."""
        await self._set_pulsating_effect(PulsatingEffect.OFF)

    async def _set_pulsating_effect(self, value: PulsatingEffect) -> None:
        """Write the pulsating effect parameter using read-before-write."""
        client = self.coordinator.config_entry.runtime_data.client
        overview = await client.get_fire_overview(self._fire_id)
        param = next(p for p in overview.parameters if isinstance(p, FlameEffectParam))
        new_param = dataclasses.replace(param, pulsating_effect=value)
        await client.write_parameters(self._fire_id, [new_param])
        await self.coordinator.async_request_refresh()


class FlameConnectAmbientSensorSwitch(FlameConnectSwitchBase):
    """Switch to enable or disable the ambient light sensor."""

    @property
    def is_on(self) -> bool | None:
        """Return True if the ambient sensor is enabled."""
        param = self._get_param(FlameEffectParam)
        if param is None:
            return None
        return param.ambient_sensor == LightStatus.ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the ambient sensor."""
        await self._set_ambient_sensor(LightStatus.ON)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the ambient sensor."""
        await self._set_ambient_sensor(LightStatus.OFF)

    async def _set_ambient_sensor(self, value: LightStatus) -> None:
        """Write the ambient sensor parameter using read-before-write."""
        client = self.coordinator.config_entry.runtime_data.client
        overview = await client.get_fire_overview(self._fire_id)
        param = next(p for p in overview.parameters if isinstance(p, FlameEffectParam))
        new_param = dataclasses.replace(param, ambient_sensor=value)
        await client.write_parameters(self._fire_id, [new_param])
        await self.coordinator.async_request_refresh()


class FlameConnectTimerSwitch(FlameConnectSwitchBase):
    """Switch to enable or disable the built-in timer."""

    @property
    def is_on(self) -> bool | None:
        """Return True if the timer is enabled."""
        param = self._get_param(TimerParam)
        if param is None:
            return None
        return param.timer_status == TimerStatus.ENABLED

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the timer, preserving the current duration."""
        await self._set_timer(TimerStatus.ENABLED)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the timer, preserving the current duration."""
        await self._set_timer(TimerStatus.DISABLED)

    async def _set_timer(self, status: TimerStatus) -> None:
        """Write the timer parameter, preserving the current duration."""
        client = self.coordinator.config_entry.runtime_data.client
        current = self._get_param(TimerParam)
        duration = current.duration if current else 60
        new_param = TimerParam(timer_status=status, duration=duration)
        await client.write_parameters(self._fire_id, [new_param])
        await self.coordinator.async_request_refresh()


# Populate the class registry after all classes are defined.
_SWITCH_CLASSES.update(
    {
        "power": FlameConnectPowerSwitch,
        "flame_effect": FlameConnectFlameEffectSwitch,
        "pulsating_effect": FlameConnectPulsatingEffectSwitch,
        "ambient_sensor": FlameConnectAmbientSensorSwitch,
        "timer": FlameConnectTimerSwitch,
    }
)
