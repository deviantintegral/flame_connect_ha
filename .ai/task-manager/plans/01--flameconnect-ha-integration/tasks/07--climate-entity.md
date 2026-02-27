---
id: 7
group: "entities"
dependencies: [5]
status: "pending"
created: "2026-02-27"
skills:
  - ha-entities
  - python
---
# Climate Entity

## Objective
Implement the climate entity for heat-capable fireplaces with HVAC modes, preset modes, target temperature with unit conversion, and HeatModeParam-based availability.

## Skills Required
Home Assistant ClimateEntity patterns, temperature unit conversion, flameconnect HeatParam/HeatModeParam handling.

## Acceptance Criteria
- [ ] Climate entity only created for fireplaces where `Fire.with_heat is True`
- [ ] HVAC modes: OFF (HeatStatus.OFF), HEAT (HeatStatus.ON)
- [ ] Preset modes: Normal, Boost, Eco, Fan Only, Schedule (from HeatMode enum)
- [ ] Target temperature read from `HeatParam.setpoint_temperature` with Fahrenheit→Celsius conversion when fireplace uses Fahrenheit
- [ ] Temperature writes convert Celsius→Fahrenheit when fireplace uses Fahrenheit
- [ ] Entity declares `temperature_unit = UnitOfTemperature.CELSIUS`
- [ ] Supported features: `TARGET_TEMPERATURE | PRESET_MODE`
- [ ] Entity is unavailable when `HeatModeParam.heat_control` is `HARDWARE_DISABLED` or `SOFTWARE_DISABLED`
- [ ] Write operations use read-before-write pattern with `dataclasses.replace()` on `HeatParam`
- [ ] `script/check` passes

## Technical Requirements
- `HeatParam` fields: `heat_status` (HeatStatus), `heat_mode` (HeatMode), `setpoint_temperature` (float), `boost_duration` (int)
- `HeatModeParam` field: `heat_control` (HeatControl: SOFTWARE_DISABLED=0, HARDWARE_DISABLED=1, ENABLED=2)
- `TempUnitParam` field: `unit` (TempUnit enum — check if Celsius or Fahrenheit)
- `HeatParam` is `frozen=True` — use `dataclasses.replace()`
- Temperature conversion: if fireplace is in Fahrenheit, convert API values to Celsius for HA, and convert back when writing

## Input Dependencies
- Task 5: Base entity class with `_get_param()` helper

## Output Artifacts
- `climate/__init__.py` — platform setup
- `climate/` — climate entity class

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Platform setup**: In `async_setup_entry`, only create climate entities for fires where `fire.with_heat is True`.

**State reading**:
- `hvac_mode`: From `_get_param(HeatParam).heat_status` — `HeatStatus.ON` → `HVACMode.HEAT`, `HeatStatus.OFF` → `HVACMode.OFF`
- `preset_mode`: From `_get_param(HeatParam).heat_mode` — map `HeatMode` enum values to string names
- `target_temperature`: From `_get_param(HeatParam).setpoint_temperature`. If the fireplace's `TempUnitParam.unit` indicates Fahrenheit, convert the API value from Fahrenheit to Celsius before returning (since the entity declares Celsius).
- `current_temperature`: Not available from the API (fireplaces don't report ambient temperature)

**Temperature unit handling**:
- The climate entity sets `_attr_temperature_unit = UnitOfTemperature.CELSIUS`
- HA handles display conversion to the user's preferred unit
- When reading from API: if `TempUnitParam.unit` is Fahrenheit, convert the `setpoint_temperature` from F→C
- When writing to API: if `TempUnitParam.unit` is Fahrenheit, convert the Celsius value from HA back to F
- Standard conversion: `celsius = (fahrenheit - 32) * 5 / 9`, `fahrenheit = celsius * 9 / 5 + 32`

**Availability**:
```python
@property
def available(self) -> bool:
    if not super().available:
        return False
    heat_mode = self._get_param(HeatModeParam)
    if heat_mode is None:
        return False
    return heat_mode.heat_control == HeatControl.ENABLED
```

**Write operations** (set_hvac_mode, set_preset_mode, set_temperature):
1. Fresh read: `overview = await client.get_fire_overview(self._fire_id)`
2. Extract `HeatParam` from the fresh overview's parameters
3. `new_param = dataclasses.replace(param, heat_status=HeatStatus.ON)` (or target field)
4. For temperature: convert from Celsius to the fireplace's native unit if needed
5. `await client.write_parameters(self._fire_id, [new_param])`
6. `await self.coordinator.async_request_refresh()`

**Important**: `boost_duration` is part of `HeatParam` but is NOT settable via CLI and should not be exposed. The read-before-write pattern preserves it automatically via `dataclasses.replace()`.
</details>
