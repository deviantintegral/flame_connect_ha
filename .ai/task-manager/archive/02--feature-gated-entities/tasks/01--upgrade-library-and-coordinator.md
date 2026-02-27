---
id: 1
group: "infrastructure"
dependencies: []
status: "completed"
created: "2026-02-27"
skills:
  - python
  - ha-integration
---
# Upgrade flameconnect Library and Update Coordinator Logging

## Objective
Upgrade the flameconnect dependency from 0.3.0 to 0.4.0 in manifest.json, and enhance coordinator discovery logging to include feature flags.

## Skills Required
Python, Home Assistant manifest and coordinator patterns.

## Acceptance Criteria
- [ ] `manifest.json` requires `flameconnect==0.4.0`
- [ ] `coordinator/base.py` logs enabled features for each fire during `_async_setup()`
- [ ] `script/check` passes with no new errors

## Technical Requirements

**manifest.json**: Change `"flameconnect==0.3.0"` to `"flameconnect==0.4.0"` in the requirements array.

**coordinator/base.py**: In `_async_setup()`, after the existing debug log for each fire, add a log line showing the names of all feature flags that are `True` on `fire.features`. Import `FireFeatures` from flameconnect. Use `dataclasses.fields()` to iterate over the `FireFeatures` fields and collect names where the value is `True`, then log as a comma-separated string (or "none" if all are False).

Example log output: `"Fire MyFire (abc123): features=sound, advanced_heat, count_down_timer, rgb_fuel_bed"`

## Input Dependencies
None — this is the first task.

## Output Artifacts
- Updated `manifest.json` with 0.4.0 requirement
- Enhanced coordinator logging for feature flag visibility
