---
id: 3
group: "entity-gating"
dependencies: [1]
status: "completed"
created: "2026-02-27"
skills:
  - python
  - ha-integration
---
# Gate Light Entity Creation on Feature Flags

## Objective
Modify the light platform's `async_setup_entry()` to only create light entities for features the fireplace supports.

## Skills Required
Python, Home Assistant entity platform setup patterns.

## Acceptance Criteria
- [ ] `media_light` only created when `fire.features.rgb_fuel_bed` is `True`
- [ ] `overhead_light` only created when `fire.features.rgb_back_light` is `True`
- [ ] `log_effect` only created when `fire.features.rgb_log_effect` is `True`
- [ ] `script/check` passes with no new errors

## Technical Requirements

**File**: `custom_components/flameconnect/light/__init__.py`

Currently, `async_setup_entry()` unconditionally creates all three lights per fire. Change to conditional creation:

For each fire, check the respective feature flag before appending each light entity:
- `FlameConnectMediaLight` → only if `fire.features.rgb_fuel_bed`
- `FlameConnectOverheadLight` → only if `fire.features.rgb_back_light`
- `FlameConnectLogEffectLight` → only if `fire.features.rgb_log_effect`

## Input Dependencies
Task 1 — library upgraded to 0.4.0 so `fire.features` is available.

## Output Artifacts
- Updated `light/__init__.py` with feature-gated entity creation
