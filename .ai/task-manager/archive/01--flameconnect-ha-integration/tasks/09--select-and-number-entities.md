---
id: 9
group: "entities"
dependencies: [5]
status: "completed"
created: "2026-02-27"
skills:
  - ha-entities
---
# Select and Number Entities

## Objective
Implement the 3 select entities (flame color, brightness, media theme) and 4 number entities (flame speed, timer duration, sound volume, sound file) with appropriate read-before-write operations.

## Skills Required
Home Assistant SelectEntity and NumberEntity patterns, flameconnect enum/parameter mapping.

## Acceptance Criteria
- [ ] Flame color select: Options from `FlameColor` enum, writes `FlameEffectParam.flame_color`
- [ ] Brightness select: Options from `Brightness` enum, writes `FlameEffectParam.brightness`
- [ ] Media theme select: Options from `MediaTheme` enum, writes `FlameEffectParam.media_theme`
- [ ] Flame speed number: Range 1–5, step 1, writes `FlameEffectParam.flame_speed`
- [ ] Timer duration number: Range 1–480, step 1, writes `TimerParam.duration`
- [ ] Sound volume number: disabled by default, entity_category=CONFIG, writes `SoundParam.volume`
- [ ] Sound file number: disabled by default, entity_category=CONFIG, writes `SoundParam.sound_file`
- [ ] FlameEffectParam-based entities use read-before-write
- [ ] TimerParam can be constructed directly (no read needed)
- [ ] SoundParam uses read-before-write
- [ ] `script/check` passes

## Technical Requirements
- `FlameColor`, `Brightness`, `MediaTheme` enums from `flameconnect.models`
- `SoundParam` fields: `volume`, `sound_file`
- Selects: map enum members to human-readable option strings
- Numbers: `NumberEntityDescription` with `native_min_value`, `native_max_value`, `native_step`
- Disabled-by-default entities: `entity_registry_enabled_default=False`

## Input Dependencies
- Task 5: Base entity class with `_get_param()` helper

## Output Artifacts
- `select/__init__.py` — platform setup with select entities
- `number/__init__.py` — platform setup with number entities
- Individual entity files per AGENTS.md guidelines

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Select entities**:

Each select maps an enum to a list of human-readable options. The `current_option` reads from the relevant parameter field, and `async_select_option` writes back.

- **Flame color** (`key="flame_color"`): `FlameColor` enum → options list. Read from `_get_param(FlameEffectParam).flame_color`. Write: read-before-write on FlameEffectParam, replace `flame_color`.
- **Brightness** (`key="brightness"`): `Brightness` enum → options. Read from `_get_param(FlameEffectParam).brightness`. Write: read-before-write, replace `brightness`.
- **Media theme** (`key="media_theme"`): `MediaTheme` enum → options. Read from `_get_param(FlameEffectParam).media_theme`. Write: read-before-write, replace `media_theme`.

**Enum-to-option mapping**: Use the enum's `.name` (lowercased, spaces) or `.value` — check the flameconnect enum definitions. Create a bidirectional mapping between HA option strings and enum members.

**Number entities**:

- **Flame speed** (`key="flame_speed"`): min=1, max=5, step=1. Read from `_get_param(FlameEffectParam).flame_speed`. Write: read-before-write on FlameEffectParam, replace `flame_speed` with `int(value)`.
- **Timer duration** (`key="timer_duration"`): min=1, max=480, step=1, unit=minutes. Read from `_get_param(TimerParam).duration`. Write: construct `TimerParam(timer_status=current_status, duration=int(value))` directly (no read-before-write needed for TimerParam).
- **Sound volume** (`key="sound_volume"`): disabled by default, entity_category=CONFIG. Read from `_get_param(SoundParam).volume`. Write: read-before-write on SoundParam.
- **Sound file** (`key="sound_file"`): disabled by default, entity_category=CONFIG. Read from `_get_param(SoundParam).sound_file`. Write: read-before-write on SoundParam.

**Disabled-by-default pattern**: Set `entity_registry_enabled_default=False` in the EntityDescription for sound volume and sound file. Set `entity_category=EntityCategory.CONFIG`.

**Write pattern for FlameEffectParam entities** (selects + flame speed):
Same as other FlameEffectParam entities: fresh `get_fire_overview()` → extract param → `dataclasses.replace()` → `write_parameters()` → `async_request_refresh()`.
</details>
