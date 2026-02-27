---
id: 5
group: "entities"
dependencies: [4]
status: "completed"
created: "2026-02-27"
skills:
  - ha-entities
---
# Base Entity and Device Registration

## Objective
Rewrite the base entity class to support multi-device (per-fireplace) operation with proper unique IDs, device info from the Fire model, and a helper method to extract parameters from coordinator data.

## Skills Required
Home Assistant entity patterns, device registry, EntityDescription dataclasses.

## Acceptance Criteria
- [ ] `FlameConnectEntity` accepts `fire_id` parameter for per-fireplace support
- [ ] Unique IDs generated as `{fire_id}_{entity_description.key}`
- [ ] `device_info` property returns correct identifiers, name, manufacturer, model, model_id, sw_version from the Fire/FireOverview data
- [ ] `_get_param(param_type)` helper extracts a specific parameter type from `coordinator.data[fire_id].parameters`, returns the instance or `None`
- [ ] Entity is unavailable when `fire_id` is missing from coordinator data
- [ ] `script/check` passes

## Technical Requirements
- `DeviceInfo` with `identifiers={(DOMAIN, fire_id)}`, `name=fire.friendly_name`, `manufacturer=fire.brand`, `model=fire.product_type`, `model_id=fire.product_model`
- `sw_version` from `SoftwareVersionParam` if available in parameters
- `coordinator.data[fire_id]` returns `FireOverview`
- `FireOverview.parameters` is `list[Parameter]` — search by type

## Input Dependencies
- Task 4: Coordinator with `coordinator.data[fire_id]` returning `FireOverview`, `coordinator.fires` for initial setup

## Output Artifacts
- `entity/base.py` — `FlameConnectEntity` base class used by all platform entities

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**`FlameConnectEntity` constructor**:
- Accepts: `coordinator: FlameConnectDataUpdateCoordinator`, `description: EntityDescription`, `fire: Fire` (from `coordinator.fires`)
- Stores `self._fire_id = fire.fire_id`
- Sets `self._attr_unique_id = f"{fire.fire_id}_{description.key}"`
- Sets `self._attr_has_entity_name = True`

**`device_info` property**:
```python
@property
def device_info(self) -> DeviceInfo:
    fire = self.coordinator.data[self._fire_id].fire
    info = DeviceInfo(
        identifiers={(DOMAIN, self._fire_id)},
        name=fire.friendly_name,
        manufacturer=fire.brand,
        model=fire.product_type,
        model_id=fire.product_model,
    )
    # Add sw_version if SoftwareVersionParam available
    sw = self._get_param(SoftwareVersionParam)
    if sw:
        info["sw_version"] = f"UI:{sw.ui_version} Ctrl:{sw.control_version} Relay:{sw.relay_version}"
    return info
```

**`_get_param` helper**:
```python
def _get_param(self, param_type: type[T]) -> T | None:
    overview = self.coordinator.data.get(self._fire_id)
    if overview is None:
        return None
    for param in overview.parameters:
        if isinstance(param, param_type):
            return param
    return None
```

**Availability**: Override `available` property — return `False` if `self._fire_id not in self.coordinator.data` or coordinator's last update failed.

**Important**: The base entity inherits from `CoordinatorEntity[FlameConnectDataUpdateCoordinator]`. All platform entities will inherit from both the HA platform base (e.g., `SwitchEntity`) and `FlameConnectEntity`.

**DeviceInfo sw_version**: Read from coordinator data (refreshed each update), not from the stale `coordinator.fires` list.
</details>
