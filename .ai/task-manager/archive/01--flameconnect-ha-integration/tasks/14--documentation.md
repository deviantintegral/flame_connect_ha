---
id: 14
group: "documentation"
dependencies: [11]
status: "completed"
created: "2026-02-27"
skills:
  - documentation
---
# Documentation Updates

## Objective
Update README.md with installation and setup instructions, and update AGENTS.md to reflect the actual integration architecture (replacing scaffold-oriented language).

## Skills Required
Technical writing, Home Assistant integration documentation patterns.

## Acceptance Criteria
- [ ] `README.md` includes: integration overview, installation instructions (HACS), setup instructions (email/password → token-only storage), supported features list, entity descriptions
- [ ] `AGENTS.md` updated to reflect actual architecture: flameconnect library (not JSONPlaceholder), token-based auth (not username/password storage), actual entity platforms (not scaffold examples), correct package structure
- [ ] Remove references to scaffold/demo code from both files
- [ ] `script/check` passes (spell check)

## Technical Requirements
- README should describe HACS installation, manual installation alternative, config flow setup steps
- AGENTS.md Integration Structure section should list actual packages/files, not scaffold ones
- Remove references to `fan/`, `binary_sensor/`, `service_actions/` from AGENTS.md

## Input Dependencies
- Task 11: Translations (entity names finalized)
- All implementation tasks implicitly (documentation reflects final architecture)

## Output Artifacts
- Updated `README.md`
- Updated `AGENTS.md`

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**README.md updates**:
- **Overview**: FlameConnect integration for controlling fireplaces via the Flame Connect cloud API
- **Features**: List all entity types (power switch, climate, lights, selects, numbers, sensors, refresh button)
- **Installation**: HACS custom repository or manual copy to `custom_components/flameconnect/`
- **Setup**: Explain the config flow — enter email/password, credentials are used once for authentication and then discarded, only OAuth tokens are stored
- **Entities**: Brief description of each entity type and what it controls
- **Note about polling**: Explain 24h automatic refresh + manual refresh button

**AGENTS.md updates**:
- Replace "JSONPlaceholder API" references with "flameconnect library"
- Update Integration Structure section:
  - `api/` — Token management (not "API client and exceptions")
  - Remove `service_actions/` from the package list
  - Remove `fan/`, `binary_sensor/` from platform directories
  - Add `climate/`, `light/` to platform directories
- Update Key patterns to reflect actual flow: Entities → Coordinator → FlameConnectClient (via library)
- Remove references to `services.yaml`, options flow, example services
- Update entity examples to use actual fireplace entities

**Important**: Do NOT add unnecessary documentation. Keep it concise and focused on what users/developers need to know. Follow the existing documentation style.
</details>
