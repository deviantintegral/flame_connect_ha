---
id: 2
group: "authentication"
dependencies: [1]
status: "completed"
created: "2026-02-27"
skills:
  - python
  - authentication
---
# Token Management Module

## Objective
Create the token management module in the `api/` package that provides an async callable for MSAL token refresh, suitable for use with the flameconnect library's `TokenAuth`.

## Skills Required
Python async programming, MSAL (Microsoft Authentication Library) token management, Azure AD B2C OAuth flows.

## Acceptance Criteria
- [ ] `api/` package contains a token provider module with an async callable that returns an access token string
- [ ] Token provider deserializes the MSAL cache from config entry data, calls `acquire_token_silent`, and returns the access token
- [ ] If the MSAL cache state changes (token rotated), the config entry data is updated via `hass.config_entries.async_update_entry()`
- [ ] If `acquire_token_silent` fails (no accounts or token refresh failure), an `AuthenticationError` is raised
- [ ] All MSAL synchronous calls are wrapped in `asyncio.to_thread()` to avoid blocking the event loop
- [ ] Constants (`CLIENT_ID`, `AUTHORITY`, `SCOPES`) are imported from `flameconnect.const`
- [ ] `script/check` passes on the new module

## Technical Requirements
- `msal.PublicClientApplication` with `msal.SerializableTokenCache`
- `flameconnect.TokenAuth` accepts `async Callable[[], str]`
- Config entry data key: `"token_cache"` (serialized JSON string from `cache.serialize()`)
- Redirect URI format: `msal{CLIENT_ID}://auth`

## Input Dependencies
- Task 1: Clean `api/` package (scaffold `client.py` deleted)

## Output Artifacts
- `api/` package with token provider module
- Async callable signature: `async def get_token() -> str`
- Factory function that creates the callable given `hass` and `config_entry`

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Module location**: `custom_components/flameconnect/api/` — replace the deleted `client.py` with a token management module (e.g., `token.py` or keep in `__init__.py`).

**Token provider factory pattern**:
```
def create_token_provider(hass, entry) -> Callable[[], Coroutine[Any, Any, str]]:
    # Returns an async callable that FlameConnectClient's TokenAuth can use
```

**Runtime token refresh flow**:
1. Deserialize the token cache: `cache = msal.SerializableTokenCache()`, `cache.deserialize(entry.data["token_cache"])`
2. Create MSAL app: `app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)` — wrap in `asyncio.to_thread()`
3. Get accounts: `accounts = app.get_accounts()` — if empty, raise `flameconnect.AuthenticationError`
4. Call `app.acquire_token_silent(SCOPES, account=accounts[0])` — wrap in `asyncio.to_thread()`
5. If result is None or contains "error", raise `flameconnect.AuthenticationError`
6. If `cache.has_state_changed`: serialize and update config entry data via `hass.config_entries.async_update_entry(entry, data={**entry.data, "token_cache": cache.serialize()})`
7. Return `result["access_token"]`

**Critical**: All `msal.PublicClientApplication` operations are synchronous and may perform network I/O (token refresh). They MUST be wrapped in `asyncio.to_thread()` to avoid blocking the HA event loop. This matches the pattern used by the library's own `MsalAuth` class.

**Constants** from `flameconnect.const`: `CLIENT_ID`, `AUTHORITY`, `SCOPES`. The redirect URI format is `f"msal{CLIENT_ID}://auth"`.

**Error handling**: When `acquire_token_silent` fails, raise `flameconnect.AuthenticationError` — the coordinator will catch this and raise `ConfigEntryAuthFailed`.
</details>
