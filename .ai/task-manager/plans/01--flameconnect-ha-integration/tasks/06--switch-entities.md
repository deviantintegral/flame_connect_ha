---
id: 6
group: "entities"
dependencies: [5]
status: "pending"
created: "2026-02-27"
skills:
  - ha-entities
---
# Switch Entities

## Objective
Implement the 5 switch entities per fireplace: power (STANDBY/MANUAL), flame effect, pulsating effect, ambient sensor, and timer — all with read-before-write operations.

## Skills Required
Home Assistant SwitchEntity patterns, flameconnect parameter manipulation with `dataclasses.replace()`.

## Acceptance Criteria
- [ ] Power switch: ON writes `ModeParam(mode=MANUAL)`, OFF writes `ModeParam(mode=STANDBY)`, preserves `target_temperature`
- [ ] Flame effect switch: On/off via `FlameEffectParam.flame_effect`
- [ ] Pulsating effect switch: On/off via `FlameEffectParam.pulsating_effect`
- [ ] Ambient sensor switch: On/off via `FlameEffectParam.ambient_sensor`
- [ ] Timer switch: Enable/disable via `TimerParam.timer_status`
- [ ] All FlameEffectParam-based switches use read-before-write (fresh `get_fire_overview()` → `dataclasses.replace()` → `write_parameters()`)
- [ ] Timer switch can construct `TimerParam` directly (no read-before-write needed)
- [ ] All switches call `coordinator.async_request_refresh()` after writing
- [ ] Platform `__init__.py` creates entities for each fireplace from `coordinator.fires`
- [ ] `script/check` passes

## Technical Requirements
- `FlameEffectParam` is `frozen=True` — use `dataclasses.replace()` for modifications
- `FlameEffectParam` bundles 12 fields — write must preserve all non-target fields
- Power switch may use `client.turn_on()`/`client.turn_off()` (which do read-before-write internally) OR manual `ModeParam` write
- `TimerParam` has only 2 fields (`timer_status`, `duration`), both user-specified — can construct from scratch

## Input Dependencies
- Task 5: Base entity class with `_get_param()` helper and device registration

## Output Artifacts
- `switch/__init__.py` — platform setup with `async_setup_entry`
- `switch/` — switch entity classes (power, flame effect, pulsating, ambient sensor, timer)

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Platform setup** (`switch/__init__.py`):
- `async_setup_entry(hass, entry, async_add_entities)`:
  - Get `FlameConnectData` from `entry.runtime_data`
  - For each fire in `coordinator.fires`: create all 5 switch entities
  - Call `async_add_entities(entities)`

**Entity descriptions** using `SwitchEntityDescription`:
- Power: `key="power"`, `name="Power"`
- Flame effect: `key="flame_effect"`, `name="Flame Effect"`
- Pulsating: `key="pulsating_effect"`, `name="Pulsating Effect"`
- Ambient sensor: `key="ambient_sensor"`, `name="Ambient Sensor"`
- Timer: `key="timer"`, `name="Timer"`

**Power switch write pattern**:
The library's `client.turn_on(fire_id)` and `client.turn_off(fire_id)` already perform read-before-write internally. The power switch can use these convenience methods directly. `is_on` reads from `_get_param(ModeParam)` — `True` if `mode == FireMode.MANUAL`, `False` if `mode == FireMode.STANDBY`.

**FlameEffectParam-based switch write pattern** (flame effect, pulsating, ambient sensor):
1. `overview = await client.get_fire_overview(self._fire_id)` — fresh read
2. Extract `FlameEffectParam` from `overview.parameters`
3. `new_param = dataclasses.replace(param, flame_effect=True)` (or the target field)
4. `await client.write_parameters(self._fire_id, [new_param])`
5. `await self.coordinator.async_request_refresh()`

**Timer switch write pattern**:
Timer can be constructed directly: `TimerParam(timer_status=True, duration=<current_duration>)`. Read the current duration from the cached `_get_param(TimerParam)` so the user doesn't lose their set duration when toggling.

**Entity organization**: One file per entity class (e.g., `switch/power.py`, `switch/flame_effect.py`, etc.) OR all in `switch/__init__.py` if they share enough structure. Follow the project's AGENTS.md guideline: "One entity class per file for clarity."

**Access to client**: Via `self.coordinator` → back to the runtime data. Or store a reference to the client on the entity. The coordinator has access to the client (it uses it for `get_fire_overview`), so entities can access it via `entry.runtime_data.client`.
</details>
