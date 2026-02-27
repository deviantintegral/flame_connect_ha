"""Base entity for FlameConnect."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from custom_components.flameconnect.const import DOMAIN
from flameconnect import SoftwareVersionParam
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from custom_components.flameconnect.coordinator import FlameConnectDataUpdateCoordinator
    from flameconnect import Fire, Parameter
    from homeassistant.helpers.entity import EntityDescription

_T = TypeVar("_T", bound="Parameter")


class FlameConnectEntity(CoordinatorEntity["FlameConnectDataUpdateCoordinator"]):
    """Base class for FlameConnect entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FlameConnectDataUpdateCoordinator,
        description: EntityDescription,
        fire: Fire,
    ) -> None:
        """Initialise the base entity.

        Args:
            coordinator: The data update coordinator for this entity.
            description: The entity description defining characteristics.
            fire: The fireplace this entity belongs to.

        """
        super().__init__(coordinator)
        self.entity_description = description
        self._fire_id = fire.fire_id
        self._attr_unique_id = f"{fire.fire_id}_{description.key}"

    @property
    def available(self) -> bool:
        """Return True if the fireplace is present in coordinator data."""
        return super().available and self._fire_id in self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this fireplace."""
        fire = self.coordinator.data[self._fire_id].fire
        info = DeviceInfo(
            identifiers={(DOMAIN, self._fire_id)},
            name=fire.friendly_name,
            manufacturer=fire.brand,
            model=fire.product_type,
            model_id=fire.product_model,
        )
        sw = self._get_param(SoftwareVersionParam)
        if sw is not None:
            info["sw_version"] = (
                f"UI:{sw.ui_major}.{sw.ui_minor}.{sw.ui_test} "
                f"Ctrl:{sw.control_major}.{sw.control_minor}.{sw.control_test} "
                f"Relay:{sw.relay_major}.{sw.relay_minor}.{sw.relay_test}"
            )
        return info

    def _get_param(self, param_type: type[_T]) -> _T | None:
        """Extract a parameter of the given type from coordinator data.

        Args:
            param_type: The parameter class to search for.

        Returns:
            The matching parameter instance, or None if not found.

        """
        overview = self.coordinator.data.get(self._fire_id)
        if overview is None:
            return None
        for param in overview.parameters:
            if isinstance(param, param_type):
                return param  # type: ignore[return-value]
        return None
