"""Sensor platform for FlameConnect."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.flameconnect.entity import FlameConnectEntity
from flameconnect import ErrorParam, SoftwareVersionParam
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory

if TYPE_CHECKING:
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="connection_state",
        name="Connection State",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="software_version",
        name="Software Version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="error_codes",
        name="Error Codes",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FlameConnectConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FlameConnect sensor entities."""
    data = entry.runtime_data
    coordinator = data.coordinator

    entities: list[SensorEntity] = []
    for fire in coordinator.fires:
        entities.extend(
            [
                FlameConnectConnectionStateSensor(coordinator, SENSOR_DESCRIPTIONS[0], fire),
                FlameConnectSoftwareVersionSensor(coordinator, SENSOR_DESCRIPTIONS[1], fire),
                FlameConnectErrorCodesSensor(coordinator, SENSOR_DESCRIPTIONS[2], fire),
            ]
        )

    async_add_entities(entities)


class FlameConnectConnectionStateSensor(SensorEntity, FlameConnectEntity):
    """Sensor showing the fireplace connection state."""

    @property
    def native_value(self) -> str | None:
        """Return the connection state as a human-readable string."""
        overview = self.coordinator.data.get(self._fire_id)
        if overview is None:
            return None
        return overview.fire.connection_state.name.replace("_", " ").title()


class FlameConnectSoftwareVersionSensor(SensorEntity, FlameConnectEntity):
    """Sensor showing the fireplace software version."""

    @property
    def native_value(self) -> str | None:
        """Return the formatted software version string."""
        sw = self._get_param(SoftwareVersionParam)
        if sw is None:
            return None
        return (
            f"UI:{sw.ui_major}.{sw.ui_minor}.{sw.ui_test} "
            f"Ctrl:{sw.control_major}.{sw.control_minor}.{sw.control_test} "
            f"Relay:{sw.relay_major}.{sw.relay_minor}.{sw.relay_test}"
        )


class FlameConnectErrorCodesSensor(SensorEntity, FlameConnectEntity):
    """Sensor showing the fireplace error codes."""

    @property
    def native_value(self) -> str | None:
        """Return the formatted error code string."""
        err = self._get_param(ErrorParam)
        if err is None:
            return None
        return f"{err.error_byte1:02X}:{err.error_byte2:02X}:{err.error_byte3:02X}:{err.error_byte4:02X}"
