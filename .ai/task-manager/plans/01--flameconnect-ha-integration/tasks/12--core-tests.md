---
id: 12
group: "testing"
dependencies: [3, 4]
status: "pending"
created: "2026-02-27"
skills:
  - python-testing
  - ha-testing
---
# Test Fixtures and Core Integration Tests

## Objective
Create the shared test fixtures (`conftest.py`) and write tests for config flow, coordinator, and integration setup/teardown.

## Skills Required
pytest with pytest-homeassistant-custom-component, MockConfigEntry, async testing patterns, mocking with unittest.mock.

## Acceptance Criteria
- [ ] `conftest.py` with mock FlameConnectClient, mock MSAL, MockConfigEntry, and helper factories
- [ ] `test_config_flow.py`: user step happy path, reauth step, error paths (invalid credentials, network error, duplicate account)
- [ ] `test_coordinator.py`: successful data fetch, auth error → ConfigEntryAuthFailed, API error → UpdateFailed, fire discovery
- [ ] `test_init.py`: async_setup_entry success, async_unload_entry success
- [ ] All tests pass via `script/test`
- [ ] Tests use HA core interfaces (`hass.states`, `hass.config_entries.flow`), not integration internals

## Technical Requirements
- `pytest-homeassistant-custom-component` provides `hass` fixture, `MockConfigEntry`, `enable_custom_integrations`
- Mock `FlameConnectClient` at module level where it's instantiated
- Mock `b2c_login_with_credentials` and `msal.PublicClientApplication`
- `asyncio_mode="auto"` (configured in pyproject.toml)
- Use `@pytest.mark.unit` / `@pytest.mark.integration` markers

## Input Dependencies
- Task 3: Config flow implementation (to test against)
- Task 4: Coordinator and __init__.py implementation (to test against)

## Output Artifacts
- `tests/conftest.py` — shared fixtures
- `tests/test_config_flow.py`
- `tests/test_coordinator.py`
- `tests/test_init.py`

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Meaningful Test Strategy Guidelines** (CRITICAL — apply these rules):
- "Write a few tests, mostly integration"
- Test YOUR code's business logic, not framework/library functionality
- Focus on critical paths and error conditions
- Combine related test scenarios into single test functions where appropriate

**`conftest.py` fixtures**:

1. **`mock_flameconnect_client`**: `AsyncMock` of `FlameConnectClient`. Preconfigure:
   - `get_fires()` → returns `[Fire(fire_id="abc123", friendly_name="Living Room", brand="Dimplex", product_type="Bold Ignite XL", product_model="BIX-50", with_heat=True, connection_state=ConnectionState.CONNECTED)]`
   - `get_fire_overview("abc123")` → returns `FireOverview` with realistic parameter instances
   - `write_parameters()` → returns None
   - `turn_on()` / `turn_off()` → returns None
   - Patch at the module where `FlameConnectClient` is imported (e.g., `custom_components.flameconnect.__init__`)

2. **`mock_msal`**: Patches `msal.PublicClientApplication` to return a mock app with:
   - `get_accounts()` → `[{"username": "user@example.com"}]`
   - `acquire_token_silent()` → `{"access_token": "fake-token"}`
   - `initiate_auth_code_flow()` → `{"auth_uri": "https://fake.b2clogin.com/..."}`
   - `acquire_token_by_auth_code_flow()` → `{"access_token": "fake-token"}`
   - Also patch `b2c_login_with_credentials` → return fake redirect URL
   - Also patch `SerializableTokenCache` with `serialize()` → `"fake-cache"`, `has_state_changed` → False

3. **`config_entry`**: `MockConfigEntry(domain=DOMAIN, data={"token_cache": "fake-cache"}, unique_id="user_example_com", title="user@example.com")`

4. **Helper factories**: Functions that return `Fire`, `FireOverview`, and parameter dataclass instances with sensible defaults. E.g., `make_fire(fire_id="abc123", with_heat=True)`, `make_fire_overview(fire_id="abc123")`.

**`test_config_flow.py`** tests:
- `test_user_step_success`: Init flow → provide credentials → verify entry created with token_cache, unique_id, title. Verify email/password NOT in entry data.
- `test_user_step_invalid_credentials`: Mock `b2c_login_with_credentials` to raise `AuthenticationError` → verify form error `invalid_auth`
- `test_user_step_cannot_connect`: Mock to raise connection error → verify form error `cannot_connect`
- `test_user_step_duplicate_account`: Create entry with same unique_id → verify abort `already_configured`
- `test_reauth_step_success`: Set up existing entry → init reauth flow → verify token_cache updated, entry reloaded

**`test_coordinator.py`** tests:
- `test_successful_update`: Coordinator fetches fire overviews → data contains expected fire_ids and FireOverview objects
- `test_auth_error_raises_config_entry_auth_failed`: Mock `get_fire_overview` to raise `AuthenticationError` → verify `ConfigEntryAuthFailed` raised
- `test_api_error_raises_update_failed`: Mock to raise `ApiError` → verify `UpdateFailed` raised
- `test_setup_discovers_fires`: Verify `coordinator.fires` populated after first refresh

**`test_init.py`** tests:
- `test_setup_entry`: Setup entry → verify state is LOADED, platforms forwarded
- `test_unload_entry`: Unload → verify returns True, state NOT_LOADED

**Testing patterns**:
- Test through `hass.config_entries.flow.async_init()` for config flow
- Use `await hass.async_block_till_done()` after setup operations
- Check `entry.state` for lifecycle tests
</details>
