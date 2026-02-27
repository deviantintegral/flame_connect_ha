"""Config flow handler package for flameconnect.

This package implements the configuration flows for the integration:
- config_flow.py: Main configuration flow (user setup, reauth)
- schemas/: Voluptuous schemas for all forms
- validators/: Credential validation via Azure AD B2C
"""

from __future__ import annotations

from .config_flow import FlameConnectConfigFlowHandler

__all__ = [
    "FlameConnectConfigFlowHandler",
]
