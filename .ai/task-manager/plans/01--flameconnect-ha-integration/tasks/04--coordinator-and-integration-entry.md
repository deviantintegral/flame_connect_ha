---
id: 4
group: "core"
dependencies: [2]
status: "pending"
created: "2026-02-27"
skills:
  - ha-coordinator
  - python
---
# Coordinator, Integration Entry, Repair Flow, and Diagnostics

## Objective
Rewrite the coordinator for fireplace data fetching with 24h+jitter polling, the integration entry point (`__init__.py`) for setup/teardown, the repair flow for auth failure notification, and diagnostics for safe data export.

## Skills Required
Home Assistant DataUpdateCoordinator patterns, integration lifecycle (async_setup_entry/async_unload_entry), repair flows, diagnostics redaction.

## Acceptance Criteria
- [ ] `coordinator/base.py` implements `FlameConnectDataUpdateCoordinator` with `_async_setup` (fire discovery) and `_async_update_data` (per-fire overview fetch)
- [ ] Coordinator `update_interval` is `timedelta(hours=24) + timedelta(minutes=randint(0, 60))`, jitter computed once at creation
- [ ] `_async_setup` calls `client.get_fires()` and stores result as `self.fires` attribute
- [ ] `_async_update_data` returns `dict[str, FireOverview]` mapping fire_id to overview
- [ ] `AuthenticationError` → `ConfigEntryAuthFailed` + creates repair issue
- [ ] `ApiError` / `FlameConnectError` → `UpdateFailed`
- [ ] `__init__.py` creates `FlameConnectClient` with `TokenAuth` and HA's shared `aiohttp.ClientSession`
- [ ] `__init__.py` creates coordinator, calls `async_config_entry_first_refresh()`, stores `FlameConnectData` on the entry
- [ ] `__init__.py` forwards setup to all 7 platforms, handles unload
- [ ] `repairs.py` implements `RepairsFlow` with `async_create_issue()` (severity ERROR) and deletion after reauth
- [ ] `diagnostics.py` exports config entry data with `token_cache` redacted
- [ ] `script/check` passes

## Technical Requirements
- `FlameConnectClient(auth=TokenAuth(get_token), session=async_get_clientsession(hass))`
- `DataUpdateCoordinator[dict[str, FireOverview]]`
- `flameconnect.AuthenticationError`, `flameconnect.ApiError`, `flameconnect.FlameConnectError`
- `homeassistant.helpers.issue_registry.async_create_issue`, `async_delete_issue`
- `homeassistant.components.diagnostics.async_redact_data`
- `random.randint(0, 60)` for jitter minutes

## Input Dependencies
- Task 1: Clean workspace, const.py (DOMAIN, PLATFORMS), data.py (FlameConnectData), manifest.json
- Task 2: Token management module (creates the token provider callable)

## Output Artifacts
- `coordinator/base.py` — FlameConnectDataUpdateCoordinator
- `__init__.py` — async_setup_entry, async_unload_entry
- `repairs.py` — FlameConnectRepairsFlow, async_create_issue helper
- `diagnostics.py` — async_get_config_entry_diagnostics with redaction

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Coordinator (`coordinator/base.py`)**:

`FlameConnectDataUpdateCoordinator(DataUpdateCoordinator[dict[str, FireOverview]])`:
- Constructor: accepts `hass`, `client: FlameConnectClient`, `entry: ConfigEntry`. Computes jitter once: `jitter = timedelta(minutes=randint(0, 60))`. Sets `update_interval=timedelta(hours=24) + jitter`.
- `_async_setup()`: `self.fires = await self.client.get_fires()`. This runs once before the first `_async_update_data`.
- `_async_update_data()`: For each fire in `self.fires`, call `await self.client.get_fire_overview(fire.fire_id)`. Return `{fire.fire_id: overview for ...}`.
- Exception handling in `_async_update_data`:
  - `flameconnect.AuthenticationError` → `async_create_issue(hass, DOMAIN, "auth_expired", ...)` then `raise ConfigEntryAuthFailed`
  - `flameconnect.ApiError` → `raise UpdateFailed(str(err))`
  - `flameconnect.FlameConnectError` → `raise UpdateFailed(str(err))`

**Entity data access paths** (document in class docstring):
- `coordinator.fires` — `list[Fire]` from `_async_setup`; for initial device/entity creation
- `coordinator.data[fire_id].fire` — fresh `Fire` per update; for current metadata
- `coordinator.data[fire_id].parameters` — fresh parameter list per update

**Integration entry (`__init__.py`)**:

`async_setup_entry`:
1. Import and call token provider factory: `get_token = create_token_provider(hass, entry)`
2. Create client: `client = FlameConnectClient(auth=TokenAuth(get_token), session=async_get_clientsession(hass))`
3. Create coordinator: `coordinator = FlameConnectDataUpdateCoordinator(hass, client, entry)`
4. `await coordinator.async_config_entry_first_refresh()`
5. Store runtime data: `entry.runtime_data = FlameConnectData(client=client, coordinator=coordinator)`
6. `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)`

`async_unload_entry`:
1. `return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)`

Remove `async_setup_services` import/call. Remove `Platform.BINARY_SENSOR` and `Platform.FAN`.

**Repair flow (`repairs.py`)**:

When coordinator catches `AuthenticationError`:
- `async_create_issue(hass, DOMAIN, "auth_expired", is_fixable=True, severity=IssueSeverity.ERROR, translation_key="auth_expired")`

`FlameConnectRepairsFlow(RepairsFlow)`:
- `async_step_init`: Starts the reauth flow via `self.hass.config_entries.async_get_entry(self.issue_id_or_entry_id).async_start_reauth(self.hass)`. Or simply confirm to direct user to the reauth flow.

The config flow (Task 3) handles deletion of the repair issue after successful reauth.

**Diagnostics (`diagnostics.py`)**:

`async_get_config_entry_diagnostics(hass, entry)`:
- Use `async_redact_data(entry.data, {"token_cache"})` to redact the token cache
- Return the redacted data dict
</details>
