"""Entity package for FlameConnect.

Architecture:
    All platform entities inherit from (PlatformEntity, FlameConnectEntity).
    MRO order matters -- platform-specific class first, then the integration base.
    Entities read data from coordinator.data and NEVER call the API client directly.
    Unique IDs follow the pattern: {fire_id}_{description.key}

See entity/base.py for the FlameConnectEntity base class.
"""

from .base import FlameConnectEntity

__all__ = ["FlameConnectEntity"]
