---
id: 11
group: "ui"
dependencies: [3, 6, 7, 8, 9, 10]
status: "pending"
created: "2026-02-27"
skills:
  - ha-translations
---
# Translations

## Objective
Write the English translations file (`translations/en.json`) covering config flow steps, entity names, select options, and error messages.

## Skills Required
Home Assistant translation file structure and naming conventions.

## Acceptance Criteria
- [ ] Config flow: `step.user` with email/password field labels, `step.reauth_confirm` with re-enter labels
- [ ] Config flow errors: `invalid_auth`, `cannot_connect`, `unknown`
- [ ] Config flow abort: `already_configured`, `reauth_successful`
- [ ] Entity names for all entity platforms (switch, climate, light, select, number, sensor, button)
- [ ] Select options for flame color, brightness, media theme (human-readable)
- [ ] Repair issue translation: `auth_expired` with title and description
- [ ] `script/check` passes (translations validated)

## Technical Requirements
- File: `custom_components/flameconnect/translations/en.json`
- Structure follows HA translation schema: `config.step`, `config.error`, `config.abort`, `entity.{platform}.{key}.name`, `issues`
- Entity names must be human-friendly (e.g., "Media Light", "Flame Speed", "Overhead Light")
- Select option labels must match the option values used in select entities

## Input Dependencies
- Task 3: Config flow step IDs and error keys
- Tasks 6–10: Entity description keys and names for all platforms

## Output Artifacts
- `translations/en.json` — complete English translations

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Translation file structure** (`translations/en.json`):

```json
{
  "config": {
    "step": {
      "user": {
        "title": "FlameConnect Login",
        "description": "Enter your FlameConnect account credentials.",
        "data": {
          "email": "Email",
          "password": "Password"
        }
      },
      "reauth_confirm": {
        "title": "Re-authenticate FlameConnect",
        "description": "Your session has expired. Please re-enter your credentials.",
        "data": {
          "email": "Email",
          "password": "Password"
        }
      }
    },
    "error": {
      "invalid_auth": "Invalid email or password",
      "cannot_connect": "Unable to connect to FlameConnect service",
      "unknown": "An unexpected error occurred"
    },
    "abort": {
      "already_configured": "This account is already configured",
      "reauth_successful": "Re-authentication successful"
    }
  },
  "entity": {
    "switch": {
      "power": { "name": "Power" },
      "flame_effect": { "name": "Flame Effect" },
      "pulsating_effect": { "name": "Pulsating Effect" },
      "ambient_sensor": { "name": "Ambient Sensor" },
      "timer": { "name": "Timer" }
    },
    "climate": {
      "heat": { "name": "Heat" }
    },
    "light": {
      "media_light": { "name": "Media Light" },
      "overhead_light": { "name": "Overhead Light" },
      "log_effect_light": { "name": "Log Effect Light" }
    },
    "select": {
      "flame_color": { "name": "Flame Color" },
      "brightness": { "name": "Brightness" },
      "media_theme": { "name": "Media Theme" }
    },
    "number": {
      "flame_speed": { "name": "Flame Speed" },
      "timer_duration": { "name": "Timer Duration" },
      "sound_volume": { "name": "Sound Volume" },
      "sound_file": { "name": "Sound File" }
    },
    "sensor": {
      "connection_state": { "name": "Connection State" },
      "software_version": { "name": "Software Version" },
      "error_codes": { "name": "Error Codes" }
    },
    "button": {
      "refresh": { "name": "Refresh Data" }
    }
  },
  "issues": {
    "auth_expired": {
      "title": "FlameConnect authentication expired",
      "description": "Your FlameConnect session has expired. Please re-authenticate to restore connectivity to your fireplaces."
    }
  }
}
```

**Important**: The entity keys in translations must match the `key` field in each entity's `EntityDescription`. Verify alignment with the actual entity implementations from Tasks 6-10.

**Select options**: If the select entities use translated option labels, add them under the entity's translation key. Check the select entity implementations to see how options are defined.
</details>
