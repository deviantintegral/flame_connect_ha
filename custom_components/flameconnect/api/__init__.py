"""
API package for flameconnect.

Architecture:
    Three-layer data flow: Entities → Coordinator → API Client.
    Only the coordinator should call the API client. Entities must never
    import or call the API client directly.

Exception hierarchy:
    FlameConnectApiClientError (base)
    ├── FlameConnectApiClientCommunicationError (network/timeout)
    └── FlameConnectApiClientAuthenticationError (401/403)

Coordinator exception mapping:
    ApiClientAuthenticationError → ConfigEntryAuthFailed (triggers reauth)
    ApiClientCommunicationError → UpdateFailed (auto-retry)
    ApiClientError             → UpdateFailed (auto-retry)
"""

from .client import (
    FlameConnectApiClient,
    FlameConnectApiClientAuthenticationError,
    FlameConnectApiClientCommunicationError,
    FlameConnectApiClientError,
)

__all__ = [
    "FlameConnectApiClient",
    "FlameConnectApiClientAuthenticationError",
    "FlameConnectApiClientCommunicationError",
    "FlameConnectApiClientError",
]
