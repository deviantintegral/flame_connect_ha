"""Tests for the FlameConnect config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flameconnect import ApiError, AuthenticationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

DOMAIN = "flameconnect"

VALID_USER_INPUT = {
    "email": "user@example.com",
    "password": "secret123",
}

CREDENTIALS_MODULE = "custom_components.flameconnect.config_flow_handler.validators.credentials"

# Patch validate_credentials where it is looked up by config_flow.py
VALIDATE_CREDENTIALS_PATCH = "custom_components.flameconnect.config_flow_handler.config_flow.validate_credentials"


def _make_credential_mocks():
    """Build the set of mocks needed for the credential validator.

    Returns a tuple of (mock_pca_class, mock_b2c_login, mock_cache_class)
    ready to be used as side_effect/return_value.
    """
    mock_cache = MagicMock()
    mock_cache.serialize.return_value = "fake-serialized-cache"

    mock_app = MagicMock()
    mock_app.initiate_auth_code_flow.return_value = {
        "auth_uri": "https://fake.b2c/auth",
    }
    mock_app.acquire_token_by_auth_code_flow.return_value = {
        "access_token": "fake-token",
    }

    mock_pca_class = MagicMock(return_value=mock_app)
    mock_b2c_login = MagicMock(return_value="https://redirect.example.com?code=fake-code&state=fake-state")
    mock_cache_class = MagicMock(return_value=mock_cache)

    return mock_pca_class, mock_b2c_login, mock_cache_class


async def test_user_step_shows_form(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_step_happy_path(hass: HomeAssistant, mock_setup_entry: MagicMock) -> None:
    mock_pca, mock_b2c, mock_cache_cls = _make_credential_mocks()

    with (
        patch(f"{CREDENTIALS_MODULE}.msal.PublicClientApplication", mock_pca),
        patch(f"{CREDENTIALS_MODULE}.b2c_login_with_credentials", mock_b2c),
        patch(f"{CREDENTIALS_MODULE}.msal.SerializableTokenCache", mock_cache_cls),
        patch(
            f"{CREDENTIALS_MODULE}.asyncio.to_thread",
            side_effect=lambda fn, *a, **kw: fn(*a, **kw),
        ),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "user@example.com"
    assert result["data"] == {"token_cache": "fake-serialized-cache"}


async def test_user_step_invalid_auth(hass: HomeAssistant) -> None:
    with patch(
        VALIDATE_CREDENTIALS_PATCH,
        side_effect=AuthenticationError("bad creds"),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_step_cannot_connect(hass: HomeAssistant) -> None:
    with patch(
        VALIDATE_CREDENTIALS_PATCH,
        side_effect=ApiError(500, "timeout"),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_step_cannot_connect_os_error(hass: HomeAssistant) -> None:
    with patch(
        VALIDATE_CREDENTIALS_PATCH,
        side_effect=OSError("network down"),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_step_unknown_error(hass: HomeAssistant) -> None:
    with patch(
        VALIDATE_CREDENTIALS_PATCH,
        side_effect=RuntimeError("unexpected"),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_reauth_step_happy_path(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    config_entry.add_to_hass(hass)
    mock_pca, mock_b2c, mock_cache_cls = _make_credential_mocks()

    with (
        patch(f"{CREDENTIALS_MODULE}.msal.PublicClientApplication", mock_pca),
        patch(f"{CREDENTIALS_MODULE}.b2c_login_with_credentials", mock_b2c),
        patch(f"{CREDENTIALS_MODULE}.msal.SerializableTokenCache", mock_cache_cls),
        patch(
            f"{CREDENTIALS_MODULE}.asyncio.to_thread",
            side_effect=lambda fn, *a, **kw: fn(*a, **kw),
        ),
    ):
        result = await config_entry.start_reauth_flow(hass)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data["token_cache"] == "fake-serialized-cache"


async def test_reauth_step_invalid_auth(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    config_entry.add_to_hass(hass)

    with patch(
        VALIDATE_CREDENTIALS_PATCH,
        side_effect=AuthenticationError("bad creds"),
    ):
        result = await config_entry.start_reauth_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_USER_INPUT,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
