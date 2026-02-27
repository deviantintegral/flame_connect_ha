---
id: 1
group: "infrastructure"
dependencies: []
status: "pending"
created: "2026-02-27"
skills:
  - python
  - ha-integration
---
# Scaffold Cleanup and Project Infrastructure

## Objective
Remove all demo/placeholder files from the scaffolded integration and set up the foundational infrastructure files (const.py, data.py, manifest.json) that all subsequent tasks depend on.

## Skills Required
Python file management and Home Assistant integration structure knowledge.

## Acceptance Criteria
- [ ] All scaffold files listed in the plan's "Scaffold Cleanup" section are deleted
- [ ] Directories `fan/`, `binary_sensor/`, `service_actions/` are removed entirely
- [ ] Directories `climate/`, `light/` are created with `__init__.py` files
- [ ] `services.yaml` is deleted
- [ ] `const.py` is rewritten with flameconnect-specific constants (DOMAIN, PLATFORMS list)
- [ ] `manifest.json` includes `"requirements": ["flameconnect==0.3.0"]`
- [ ] `data.py` defines `FlameConnectData` runtime dataclass with `client` and `coordinator` fields
- [ ] `script/check` passes on the modified files (no lint/type errors)

## Technical Requirements
- Domain: `flameconnect`
- PLATFORMS list: `BUTTON`, `CLIMATE`, `LIGHT`, `NUMBER`, `SELECT`, `SENSOR`, `SWITCH`
- `FlameConnectData` dataclass: `client: FlameConnectClient`, `coordinator: FlameConnectDataUpdateCoordinator` (forward references are acceptable at this stage)

## Input Dependencies
None — this is the first task.

## Output Artifacts
- Clean workspace with no scaffold demo code
- `const.py` with DOMAIN and PLATFORMS
- `manifest.json` with flameconnect requirement
- `data.py` with FlameConnectData
- `climate/` and `light/` directories with `__init__.py`

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Files to delete** (all paths relative to `custom_components/flameconnect/`):
- `api/client.py`
- `sensor/air_quality.py`, `sensor/diagnostic.py`
- `binary_sensor/connectivity.py`, `binary_sensor/filter.py`
- `switch/example_switch.py`
- `button/reset_filter.py`
- `select/fan_speed.py`
- `fan/air_purifier_fan.py`
- `number/target_humidity.py`
- `service_actions/example_service.py`, `service_actions/__init__.py`
- `services.yaml`
- `config_flow_handler/options_flow.py`, `config_flow_handler/subentry_flow.py`
- `coordinator/data_processing.py`, `coordinator/error_handling.py`, `coordinator/listeners.py`
- `entity_utils/device_info.py`, `entity_utils/state_helpers.py`
- `utils/validators.py`, `utils/string_helpers.py`

**Directories to remove entirely**: `fan/`, `binary_sensor/`, `service_actions/`

**Directories to create**: `climate/__init__.py`, `light/__init__.py` (empty platform init files — the actual entity code will be added in later tasks).

**const.py** should define:
- `DOMAIN = "flameconnect"`
- `PLATFORMS` list with the 7 Platform enums
- Remove any scaffold constants (ATTRIBUTION for jsonplaceholder, DEFAULT_UPDATE_INTERVAL_HOURS, etc.)

**manifest.json** updates:
- Add `"requirements": ["flameconnect==0.3.0"]`
- Keep existing fields (domain, name, integration_type=hub, iot_class=cloud_polling, etc.)

**data.py** should define a `FlameConnectData` dataclass (or NamedTuple) with two fields:
- `client`: typed as `FlameConnectClient` (from `flameconnect`)
- `coordinator`: typed as `FlameConnectDataUpdateCoordinator` (use `TYPE_CHECKING` imports to avoid circular imports since the coordinator class doesn't exist yet)

**Important**: Do NOT modify `__init__.py`, `config_flow.py`, `coordinator/base.py`, or `entity/base.py` in this task — those will be rewritten in subsequent tasks. Only delete scaffold files and update the infrastructure files listed above.

After cleanup, existing files that reference deleted modules will have import errors — this is expected and will be resolved by subsequent tasks.
</details>
