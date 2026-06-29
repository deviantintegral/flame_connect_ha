"""Climate platform for FlameConnect.

Provides HVAC control for fireplaces with heat capability, supporting
on/off, target temperature, and preset modes (normal, boost, eco,
fan_only, schedule).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from custom_components.flameconnect.const import LOGGER
from custom_components.flameconnect.entity import FlameConnectEntity
from flameconnect import HeatControl, HeatMode, HeatModeParam, HeatParam, HeatStatus
from homeassistant.components.climate import ClimateEntity, ClimateEntityDescription
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature

if TYPE_CHECKING:
    from custom_components.flameconnect.coordinator import FlameConnectDataUpdateCoordinator
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from flameconnect import Fire
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity import EntityDescription
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

CLIMATE_DESCRIPTION = ClimateEntityDescription(
    key="climate",
    name=None,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FlameConnectConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlameConnect climate entities."""
    coordinator = entry.runtime_data.coordinator
    entities = [
        FlameConnectClimate(coordinator, CLIMATE_DESCRIPTION, fire)
        for fire in coordinator.fires
        if fire.features.simple_heat or fire.features.advanced_heat
    ]
    LOGGER.debug(
        "Climate setup: %d fires discovered, %d with heat capability",
        len(coordinator.fires),
        len(entities),
    )
    async_add_entities(entities)


class FlameConnectClimate(FlameConnectEntity, ClimateEntity):
    """Climate entity for a FlameConnect fireplace with heat capability."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]

    entity_description: ClimateEntityDescription

    def __init__(
        self,
        coordinator: FlameConnectDataUpdateCoordinator,
        description: EntityDescription,
        fire: Fire,
    ) -> None:
        """Initialise climate entity with dynamic preset modes based on features."""
        super().__init__(coordinator, description, fire)
        presets = ["normal", "eco", "schedule"]
        if fire.features.power_boost:
            presets.append("boost")
        if fire.features.fan_only:
            presets.append("fan_only")
        self._attr_preset_modes = presets

    @property
    def available(self) -> bool:
        """Return True if the fireplace heat control is enabled."""
        if not super().available:
            return False
        heat_mode = self._get_param(HeatModeParam)
        if heat_mode is None:
            return False
        return heat_mode.heat_control == HeatControl.ENABLED

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return the current HVAC mode (heat or off)."""
        heat = self._get_param(HeatParam)
        if heat is None:
            return None
        if heat.heat_status == HeatStatus.ON:
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        heat = self._get_param(HeatParam)
        if heat is None:
            return None
        return heat.heat_mode.name.lower()

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature in Celsius.

        The device always stores the setpoint in Celsius on the wire; the
        ``TempUnit`` parameter is only a display preference for the
        fireplace's own UI and does not affect the stored value. Home
        Assistant converts to the user's preferred unit for display.
        """
        heat = self._get_param(HeatParam)
        if heat is None:
            return None
        return heat.setpoint_temperature

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature (not available from API)."""
        return None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode (heat or off)."""
        status = HeatStatus.ON if hvac_mode == HVACMode.HEAT else HeatStatus.OFF
        await self.coordinator.async_write_fields(self._fire_id, HeatParam, heat_status=status)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode."""
        mode = HeatMode[preset_mode.upper()]
        if mode == HeatMode.BOOST:
            stored = self.coordinator.boost_durations.get(self._fire_id)
            if stored is None:
                heat = self._get_param(HeatParam)
                stored = heat.boost_duration if heat is not None else 15
            await self.coordinator.async_write_fields(self._fire_id, HeatParam, heat_mode=mode, boost_duration=stored)
        else:
            await self.coordinator.async_write_fields(self._fire_id, HeatParam, heat_mode=mode)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature.

        Home Assistant provides the value in Celsius (the entity's unit),
        which is exactly what the device stores on the wire, so it is
        written through unchanged regardless of the device's display unit.
        """
        temperature: float | None = kwargs.get("temperature")
        if temperature is None:
            return
        await self.coordinator.async_write_fields(self._fire_id, HeatParam, setpoint_temperature=temperature)
