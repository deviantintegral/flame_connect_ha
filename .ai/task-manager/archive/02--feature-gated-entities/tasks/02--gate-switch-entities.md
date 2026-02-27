---
id: 2
group: "entity-gating"
dependencies: [1]
status: "completed"
created: "2026-02-27"
skills:
  - python
  - ha-integration
---
# Gate Switch Entity Creation on Feature Flags

## Objective
Modify the switch platform's `async_setup_entry()` to only create entities for features the fireplace supports.

## Skills Required
Python, Home Assistant entity platform setup patterns.

## Acceptance Criteria
- [ ] `ambient_sensor` switch only created when `fire.features.pir_toggle_smart_sense` is `True`
- [ ] `timer` switch only created when `fire.features.count_down_timer` is `True`
- [ ] `power`, `flame_effect`, `pulsating_effect` switches always created (no gating)
- [ ] `script/check` passes with no new errors

## Technical Requirements

**File**: `custom_components/flameconnect/switch/__init__.py`

Modify `async_setup_entry()` to check feature flags before creating gated entities. The approach:

1. Define a mapping from entity description key to the required feature flag attribute name on `FireFeatures`:
   - `"ambient_sensor"` -> `"pir_toggle_smart_sense"`
   - `"timer"` -> `"count_down_timer"`

2. In the loop over fires and descriptions, check if the description key is in the mapping. If so, verify `getattr(fire.features, flag_name)` is `True` before creating the entity.

3. Entities not in the mapping (power, flame_effect, pulsating_effect) are always created.

## Input Dependencies
Task 1 — library upgraded to 0.4.0 so `fire.features` is available.

## Output Artifacts
- Updated `switch/__init__.py` with feature-gated entity creation
