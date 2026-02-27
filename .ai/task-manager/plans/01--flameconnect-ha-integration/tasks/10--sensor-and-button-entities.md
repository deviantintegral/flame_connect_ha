---
id: 10
group: "entities"
dependencies: [5]
status: "pending"
created: "2026-02-27"
skills:
  - ha-entities
---
# Sensor and Button Entities

## Objective
Implement the 3 diagnostic sensor entities (connection state, software version, error codes) and the refresh data button entity.

## Skills Required
Home Assistant SensorEntity and ButtonEntity patterns.

## Acceptance Criteria
- [ ] Connection state sensor: reads `coordinator.data[fire_id].fire.connection_state`, maps to human-readable string
- [ ] Software version sensor: combines UI, control, and relay versions from `SoftwareVersionParam`
- [ ] Error codes sensor: reads from `ErrorParam`, displays error byte values
- [ ] All sensors are `entity_category=DIAGNOSTIC` and `entity_registry_enabled_default=False`
- [ ] Refresh button: `async_press` calls `coordinator.async_request_refresh()`
- [ ] Refresh button is enabled by default
- [ ] `script/check` passes

## Technical Requirements
- `SoftwareVersionParam` fields: `ui_version`, `control_version`, `relay_version`
- `ErrorParam`: 4 error bytes
- `Fire.connection_state`: `ConnectionState` enum (UNKNOWN=0, NOT_CONNECTED=1, CONNECTED=2, UPDATING_FIRMWARE=3)
- Connection state comes from `coordinator.data[fire_id].fire.connection_state` (fresh per update, since `FireOverview` contains a `Fire` object)
- `ButtonEntity` with `async_press` method

## Input Dependencies
- Task 5: Base entity class with `_get_param()` helper

## Output Artifacts
- `sensor/__init__.py` — platform setup with sensor entities
- `button/__init__.py` — platform setup with button entity
- Individual entity files per AGENTS.md guidelines

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Sensor entities**:

All sensors share: `entity_category=EntityCategory.DIAGNOSTIC`, `entity_registry_enabled_default=False`.

- **Connection state** (`key="connection_state"`, `name="Connection State"`):
  - `native_value`: `self.coordinator.data[self._fire_id].fire.connection_state.name` — maps enum to "UNKNOWN", "NOT_CONNECTED", "CONNECTED", "UPDATING_FIRMWARE". Consider formatting to title case: "Connected", "Not Connected", etc.
  - `device_class`: None (custom states)

- **Software version** (`key="software_version"`, `name="Software Version"`):
  - `native_value`: Extract `SoftwareVersionParam` via `_get_param()`. Format as `"UI:{ui} Ctrl:{ctrl} Relay:{relay}"` or similar.
  - If param is None, return None.

- **Error codes** (`key="error_codes"`, `name="Error Codes"`):
  - `native_value`: Extract `ErrorParam` via `_get_param()`. Format the 4 error bytes as a string.
  - If param is None, return None.

**Button entity**:

- **Refresh data** (`key="refresh"`, `name="Refresh Data"`):
  - `async_press(self)`: `await self.coordinator.async_request_refresh()`
  - Enabled by default (no entity_category, no disabled-by-default)
  - Icon: `mdi:refresh`

**Platform setup**: Both `sensor/__init__.py` and `button/__init__.py` iterate over `coordinator.fires` and create entities for each fireplace.

**Note**: The connection state sensor reads from `coordinator.data[fire_id].fire.connection_state`, NOT from `coordinator.fires`. The `FireOverview` returned by `get_fire_overview()` contains a fresh `Fire` object, so connection state refreshes with every coordinator update.
</details>
