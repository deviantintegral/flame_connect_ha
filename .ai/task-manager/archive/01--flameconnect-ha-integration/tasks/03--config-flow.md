---
id: 3
group: "authentication"
dependencies: [2]
status: "completed"
created: "2026-02-27"
skills:
  - ha-config-flow
  - authentication
---
# Config Flow (User Setup + Reauth)

## Objective
Rewrite the config flow to authenticate via Azure AD B2C using the flameconnect library's `b2c_login_with_credentials`, store only the serialized MSAL token cache (discarding credentials), and support reauth when tokens expire.

## Skills Required
Home Assistant config flow patterns, MSAL authentication, Azure AD B2C credential submission.

## Acceptance Criteria
- [ ] User step collects email and password, authenticates via B2C, stores only `token_cache` in config entry data
- [ ] Email and password are NOT stored in config entry data
- [ ] Config entry `unique_id` is set to slugified email (prevents duplicate entries)
- [ ] Config entry `title` is set to the email address
- [ ] Reauth step collects new credentials, updates the token cache, and reloads the entry
- [ ] Reauth step deletes any existing repair issue via `async_delete_issue()` on success
- [ ] Auth errors (invalid credentials, network errors) show appropriate form errors
- [ ] Duplicate account (same unique_id) triggers abort
- [ ] `config_flow_handler/schemas/config.py` defines the user input schema (email + password fields)
- [ ] `config_flow_handler/validators/credentials.py` implements the B2C auth validation logic
- [ ] `script/check` passes

## Technical Requirements
- `msal.PublicClientApplication` with in-memory `SerializableTokenCache`
- `flameconnect.b2c_login.b2c_login_with_credentials(auth_uri, email, password) -> str`
- `flameconnect.const.CLIENT_ID`, `AUTHORITY`, `SCOPES`
- Redirect URI: `f"msal{CLIENT_ID}://auth"`
- Parse redirect URL to extract auth_response for `acquire_token_by_auth_code_flow`

## Input Dependencies
- Task 2: Token management module (for understanding the token cache format and MSAL patterns)

## Output Artifacts
- `config_flow_handler/config_flow.py` — FlameConnectConfigFlow with `async_step_user` and `async_step_reauth`/`async_step_reauth_confirm`
- `config_flow_handler/schemas/config.py` — vol.Schema for user input
- `config_flow_handler/validators/credentials.py` — B2C auth validation
- `config_flow.py` (root) — updated if needed for the flow class reference

## Implementation Notes

<details>
<summary>Detailed implementation guidance</summary>

**Config flow steps**:

1. **`async_step_user`**: Show form with email + password → call validator → on success, create entry with `data={"token_cache": serialized_cache}`, set `unique_id` and `title`.

2. **`async_step_reauth`** / **`async_step_reauth_confirm`**: Show form with email + password → call same validator → on success, update existing entry data with new token cache, delete repair issue if exists, reload entry.

**Validator logic** (`credentials.py`):
1. Create `msal.SerializableTokenCache()` and `msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)`
2. Call `app.initiate_auth_code_flow(scopes=SCOPES, redirect_uri=f"msal{CLIENT_ID}://auth")` to get the flow object containing `auth_uri`
3. Call `await asyncio.to_thread(b2c_login_with_credentials, flow["auth_uri"], email, password)` to get the redirect URL
4. Parse the redirect URL's query parameters into a dict (this is the `auth_response`)
5. Call `app.acquire_token_by_auth_code_flow(flow, auth_response)` to exchange the code for tokens
6. If any step fails, raise appropriate errors that the config flow maps to form errors
7. Return `cache.serialize()` on success

**Error mapping**:
- `flameconnect.AuthenticationError` → `{"base": "invalid_auth"}`
- `flameconnect.ApiError` / connection errors → `{"base": "cannot_connect"}`
- Unexpected errors → `{"base": "unknown"}`

**Reauth repair issue cleanup**: After successful reauth, call `async_delete_issue(hass, DOMAIN, "auth_expired")` to remove the repair issue if it exists.

**Schema** (`config.py`): `vol.Schema({vol.Required("email"): str, vol.Required("password"): str})`

**Important**: All MSAL calls (`PublicClientApplication()`, `initiate_auth_code_flow()`, `acquire_token_by_auth_code_flow()`) are synchronous and must be wrapped in `asyncio.to_thread()`.
</details>
