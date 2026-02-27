"""Config flow schemas for flameconnect.

Provides the email + password schema used by user and reauth steps.
"""

from __future__ import annotations

import voluptuous as vol

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("password"): str,
    }
)

__all__ = [
    "STEP_USER_DATA_SCHEMA",
]
