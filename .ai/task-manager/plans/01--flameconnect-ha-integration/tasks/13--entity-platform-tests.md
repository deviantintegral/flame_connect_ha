---
id: 13
group: "testing"
dependencies: [6, 7, 8, 9, 10, 12]
status: "completed"
created: "2026-02-27"
skills:
  - python-testing
  - ha-testing
---
# Entity Platform Tests

## Objective
Write integration tests for all 7 entity platforms, verifying state reporting, write operations, device info, and disabled-by-default behavior through HA core interfaces.

## Skills Required
pytest with pytest-homeassistant-custom-component, HA entity/service testing patterns, Syrupy snapshots.

## Acceptance Criteria
- [ ] `test_switch.py`: Power on/off, flame effect toggle, timer toggle — verify state changes and API calls
- [ ] `test_climate.py`: HVAC mode, preset mode, target temperature with unit conversion — verify write operations
- [ ] `test_light.py`: Media/overhead/log light on/off, RGBW color setting — verify correct param fields written
- [ ] `test_select.py`: Flame color, brightness, media theme selection — verify enum mapping
- [ ] `test_number.py`: Flame speed, timer duration setting — verify range and write operations
- [ ] `test_sensor.py`: Connection state, software version, error codes — verify read-only state
- [ ] `test_button.py`: Refresh button press triggers coordinator refresh
- [ ] Device info verified for at least one entity (identifiers, manufacturer, model)
- [ ] Disabled-by-default entities verified (sound volume, sound file, sensors)
- [ ] All tests pass via `script/test`

## Technical Requirements
- Test through `hass.states.get()` and `hass.services.async_call()`, not entity internals
- Mock `FlameConnectClient.get_fire_overview()` and `write_parameters()` to verify read-before-write
- Use device registry (`dr.async_get(hass)`) and entity registry (`er.async_get(hass)`) for registry checks
- Syrupy snapshots for entity state verification where appropriate

## Input Dependencies
- Task 12: Test fixtures in conftest.py (mock client, config entry, factories)
- Tasks 6–10: All entity platform implementations

## Output Artifacts
- `tests/switch/test_switch.py`
- `tests/climate/test_climate.py`
- `tests/light/test_light.py`
- `tests/select/test_select.py`
- `tests/number/test_number.py`
- `tests/sensor/test_sensor.py`
- `tests/button/test_button.py`

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Meaningful Test Strategy Guidelines** (CRITICAL — apply these rules):
- "Write a few tests, mostly integration"
- Test YOUR code's business logic, not framework/library functionality
- Focus on: state reporting accuracy, write operation correctness (read-before-write), entity availability logic
- Do NOT test: HA's entity registry internals, basic entity property access, HA's temperature conversion

**Test pattern for all entity platforms**:
1. Set up integration: `config_entry.add_to_hass(hass)` → `await hass.config_entries.async_setup(config_entry.entry_id)` → `await hass.async_block_till_done()`
2. Verify state: `state = hass.states.get("switch.living_room_power")` → assert state/attributes
3. Verify writes: `await hass.services.async_call("switch", "turn_on", {"entity_id": "..."})` → assert `mock_client.get_fire_overview.called` (read-before-write) → assert `mock_client.write_parameters.called_with(...)` (correct params)

**Switch tests (`test_switch.py`)**:
- `test_power_switch_on`: Verify `client.turn_on()` called (or ModeParam write)
- `test_power_switch_off`: Verify `client.turn_off()` called
- `test_flame_effect_toggle`: Verify read-before-write on FlameEffectParam, only `flame_effect` field changed
- `test_timer_switch`: Verify TimerParam constructed directly (no read-before-write)

**Climate tests (`test_climate.py`)**:
- `test_hvac_mode_heat`: Set HVAC mode → verify HeatParam written with `heat_status=ON`
- `test_set_temperature`: Set temp → verify Celsius value written (or F→C conversion if applicable)
- `test_preset_mode`: Set preset → verify HeatParam.heat_mode set correctly
- `test_unavailable_when_heat_disabled`: Mock HeatModeParam with HARDWARE_DISABLED → verify entity unavailable

**Light tests (`test_light.py`)**:
- `test_overhead_light_uses_light_status`: Verify on/off uses `light_status` field, NOT `overhead_light`
- `test_media_light_on_with_color`: Verify RGBW color written to `media_color`
- `test_log_effect_light`: Verify LogEffectParam written

**Select/Number tests** (`test_select.py`, `test_number.py`):
- `test_flame_color_select`: Select option → verify correct FlameColor enum written
- `test_flame_speed_number`: Set value → verify FlameEffectParam.flame_speed updated
- `test_sound_volume_disabled_by_default`: Verify entity_registry entry has `disabled_by`

**Sensor tests (`test_sensor.py`)**:
- `test_connection_state_sensor`: Verify reads from `coordinator.data[fire_id].fire.connection_state`
- `test_sensors_disabled_by_default`: Verify all sensors have `entity_registry_enabled_default=False`

**Button tests (`test_button.py`)**:
- `test_refresh_button_press`: Press → verify `coordinator.async_request_refresh()` called

**Device info test** (in any platform test file):
- Verify device has correct identifiers `{(DOMAIN, fire_id)}`, manufacturer, model, model_id

**Entity ID format**: Entity IDs will be like `switch.{friendly_name}_{key}` (e.g., `switch.living_room_power`). The exact format depends on how HA generates entity_ids from device name + entity name.
</details>
