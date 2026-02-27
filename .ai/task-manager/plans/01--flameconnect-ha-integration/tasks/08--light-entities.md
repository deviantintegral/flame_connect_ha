---
id: 8
group: "entities"
dependencies: [5]
status: "pending"
created: "2026-02-27"
skills:
  - ha-entities
---
# Light Entities

## Objective
Implement the 3 light entities per fireplace: media light, overhead light, and log effect light — all with RGBW color support and appropriate on/off controls.

## Skills Required
Home Assistant LightEntity patterns with RGBW color mode, flameconnect FlameEffectParam and LogEffectParam handling.

## Acceptance Criteria
- [ ] Media light: on/off via `FlameEffectParam.media_light`, color via `FlameEffectParam.media_color`, effects from `MediaTheme` enum
- [ ] Overhead light: on/off via `FlameEffectParam.light_status` (NOT `overhead_light`), color via `FlameEffectParam.overhead_color`
- [ ] Log effect light: on/off via `LogEffectParam.log_effect`, color via `LogEffectParam.color`
- [ ] All lights support RGBW color mode
- [ ] Media and overhead lights use read-before-write on `FlameEffectParam` (12-field bundle)
- [ ] Log effect light uses read-before-write on `LogEffectParam`
- [ ] All lights call `coordinator.async_request_refresh()` after writing
- [ ] `script/check` passes

## Technical Requirements
- `FlameEffectParam` fields for media: `media_light` (bool), `media_color` (RGBW tuple/object)
- `FlameEffectParam` fields for overhead: `light_status` (bool — the actual on/off control), `overhead_color` (RGBW)
- `LogEffectParam` fields: `log_effect` (bool), `color` (RGBW)
- RGBW color: Check the library's color representation and map to HA's `(r, g, b, w)` tuple
- `ColorMode.RGBW` for supported color modes
- `LightEntityFeature.EFFECT` for media light (MediaTheme as effects)

## Input Dependencies
- Task 5: Base entity class with `_get_param()` helper

## Output Artifacts
- `light/__init__.py` — platform setup
- `light/` — light entity classes (media, overhead, log effect)

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Critical: Overhead light on/off control**:
The overhead light entity MUST use `FlameEffectParam.light_status` (wire byte 18) for on/off — NOT `FlameEffectParam.overhead_light` (wire byte 13). This was confirmed by library source analysis: all TUI/CLI code uses `light_status` for overhead light control. `overhead_light` is decoded/encoded for wire round-trip correctness but is never used for display or control. Do NOT expose `overhead_light` as a separate entity.

**Media light**:
- `is_on`: `_get_param(FlameEffectParam).media_light`
- `rgbw_color`: From `FlameEffectParam.media_color` — check the library's color type and convert to HA's `(r, g, b, w)` tuple
- `effect_list`: Names from `MediaTheme` enum values
- `effect`: Current `FlameEffectParam.media_theme` mapped to string
- `turn_on(rgbw_color=..., effect=...)`: Read-before-write on `FlameEffectParam`, set `media_light=True` and optionally `media_color`/`media_theme`
- `turn_off()`: Read-before-write, set `media_light=False`

**Overhead light**:
- `is_on`: `_get_param(FlameEffectParam).light_status`
- `rgbw_color`: From `FlameEffectParam.overhead_color`
- `turn_on(rgbw_color=...)`: Read-before-write, set `light_status=True` and optionally `overhead_color`
- `turn_off()`: Read-before-write, set `light_status=False`

**Log effect light**:
- `is_on`: `_get_param(LogEffectParam).log_effect`
- `rgbw_color`: From `LogEffectParam.color`
- `turn_on(rgbw_color=...)`: Read-before-write on `LogEffectParam`, set `log_effect=True` and optionally `color`
- `turn_off()`: Read-before-write, set `log_effect=False`

**Color type investigation**: Check how the flameconnect library represents RGBW colors in `FlameEffectParam.media_color`, `overhead_color`, and `LogEffectParam.color`. They might be tuples, named tuples, or custom classes. Map to HA's `tuple[int, int, int, int]` RGBW format.

**Write pattern** (shared for media and overhead — both in `FlameEffectParam`):
1. `overview = await client.get_fire_overview(self._fire_id)`
2. Extract `FlameEffectParam` from overview.parameters
3. `new_param = dataclasses.replace(param, media_light=True, media_color=new_color)` (only set the fields being changed)
4. `await client.write_parameters(self._fire_id, [new_param])`
5. `await self.coordinator.async_request_refresh()`
</details>
