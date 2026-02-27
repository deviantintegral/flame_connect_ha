"""Config flow for flameconnect.

Implements Azure AD B2C authentication. The user step collects email and
password, authenticates via B2C, and stores only the serialized MSAL token
cache (credentials are discarded). The reauth flow re-authenticates and
updates the stored token cache.
"""

from __future__ import annotations

from typing import Any

from slugify import slugify

from custom_components.flameconnect.api.token import CONF_TOKEN_CACHE
from custom_components.flameconnect.config_flow_handler.schemas import STEP_USER_DATA_SCHEMA
from custom_components.flameconnect.config_flow_handler.validators import validate_credentials
from custom_components.flameconnect.const import DOMAIN, LOGGER
from flameconnect import ApiError, AuthenticationError  # type: ignore[attr-defined]
from homeassistant import config_entries
from homeassistant.helpers import issue_registry as ir


class FlameConnectConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for flameconnect.

    Supports:
    - user: Initial setup via email + password (B2C authentication).
    - reauth: Re-authenticate when tokens expire.
    """

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle user-initiated setup.

        Collects email and password, authenticates via Azure AD B2C,
        and creates a config entry storing only the serialized token cache.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                token_cache = await validate_credentials(
                    email=user_input["email"],
                    password=user_input["password"],
                )
            except AuthenticationError:
                LOGGER.warning("Authentication failed during config flow")
                errors["base"] = "invalid_auth"
            except (ApiError, OSError):
                LOGGER.warning("Connection error during config flow")
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                email = user_input["email"]
                await self.async_set_unique_id(slugify(email))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=email,
                    data={CONF_TOKEN_CACHE: token_cache},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle reauthentication triggered by expired tokens."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle reauthentication confirmation.

        Collects new credentials, re-authenticates, updates the token cache
        in the config entry, and deletes the auth_expired repair issue.
        """
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                token_cache = await validate_credentials(
                    email=user_input["email"],
                    password=user_input["password"],
                )
            except AuthenticationError:
                LOGGER.warning("Authentication failed during reauth")
                errors["base"] = "invalid_auth"
            except (ApiError, OSError):
                LOGGER.warning("Connection error during reauth")
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected error during reauth")
                errors["base"] = "unknown"
            else:
                ir.async_delete_issue(self.hass, DOMAIN, "auth_expired")

                return self.async_update_reload_and_abort(
                    entry,
                    data={CONF_TOKEN_CACHE: token_cache},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


__all__ = ["FlameConnectConfigFlowHandler"]
