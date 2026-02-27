---
id: 4
group: "entity-gating"
dependencies: [1]
status: "completed"
created: "2026-02-27"
skills:
  - python
  - ha-integration
---
# Gate Select, Number, Sensor, and Climate Entities on Feature Flags

## Objective
Modify the select, number, sensor, and climate platforms to conditionally create entities and dynamically configure presets based on feature flags.

## Skills Required
Python, Home Assistant entity platform setup patterns, climate entity configuration.

## Acceptance Criteria
- [ ] **Select**: `flame_color` gated on `rgb_flame_accent`, `brightness` on `flame_dimming`, `media_theme` on `moods`
- [ ] **Number**: `flame_speed` gated on `flame_fan_speed`, `timer_duration` on `count_down_timer`, `sound_volume` and `sound_file` on `sound`
- [ ] **Sensor**: `timer_end` gated on `count_down_timer`; connection_state, software_version, error_codes always created
- [ ] **Climate**: Creation gated on `fire.features.simple_heat or fire.features.advanced_heat` (replacing current HeatParam/HeatModeParam check); preset_modes dynamically built based on `power_boost` and `fan_only` flags
- [ ] `script/check` passes with no new errors

## Technical Requirements

### Select platform (`select/__init__.py`)

Define a mapping from description key to feature flag:
- `"flame_color"` -> `"rgb_flame_accent"`
- `"brightness"` -> `"flame_dimming"`
- `"media_theme"` -> `"moods"`

In `async_setup_entry()`, filter descriptions per fire based on features.

### Number platform (`number/__init__.py`)

Define a mapping from description key to feature flag:
- `"flame_speed"` -> `"flame_fan_speed"`
- `"timer_duration"` -> `"count_down_timer"`
- `"sound_volume"` -> `"sound"`
- `"sound_file"` -> `"sound"`

In `async_setup_entry()`, filter descriptions per fire based on features.

### Sensor platform (`sensor/__init__.py`)

The `timer_end` sensor should only be created when `fire.features.count_down_timer` is `True`. The three diagnostic sensors (connection_state, software_version, error_codes) are always created.

Refactor `async_setup_entry()`: always add the three diagnostic sensors, and conditionally add `FlameConnectTimerEndSensor` only when `fire.features.count_down_timer` is `True`.

### Climate platform (`climate/__init__.py`)

Two changes:

1. **Entity creation gating**: Replace the current check (`any(isinstance(p, (HeatParam, HeatModeParam)) ...)`) with a feature flag check: `fire.features.simple_heat or fire.features.advanced_heat`. Remove the `overview` lookup and parameter presence check.

2. **Dynamic preset modes**: Change `_attr_preset_modes` from a class attribute to an instance attribute set in `__init__()`. The constructor should:
   - Accept the `fire` parameter (already passed from base entity)
   - Build preset list: always include `"normal"`, `"eco"`, `"schedule"`
   - Add `"boost"` if `fire.features.power_boost` is `True`
   - Add `"fan_only"` if `fire.features.fan_only` is `True`
   - Set `self._attr_preset_modes = presets`

   The entity needs to override `__init__` to access `fire.features` — after calling `super().__init__()`. The `Fire` object is passed as the `fire` parameter.

## Input Dependencies
Task 1 — library upgraded to 0.4.0 so `fire.features` is available.

## Output Artifacts
- Updated `select/__init__.py`, `number/__init__.py`, `sensor/__init__.py`, `climate/__init__.py`
