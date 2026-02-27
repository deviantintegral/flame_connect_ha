"""Sensor platform for FlameConnect."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from custom_components.flameconnect.entity import FlameConnectEntity
from flameconnect import ErrorParam, SoftwareVersionParam, TimerParam, TimerStatus
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from custom_components.flameconnect.coordinator import FlameConnectDataUpdateCoordinator
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from flameconnect import Fire
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity import EntityDescription
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="connection_state",
        name="Connection State",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:cloud-check-outline",
    ),
    SensorEntityDescription(
        key="software_version",
        name="Software Version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:chip",
    ),
    SensorEntityDescription(
        key="error_codes",
        name="Error Codes",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:alert-circle-outline",
    ),
)

TIMER_END_DESCRIPTION = SensorEntityDescription(
    key="timer_end",
    name="Timer End",
    device_class=SensorDeviceClass.TIMESTAMP,
    icon="mdi:timer-sand-complete",
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
        if fire.features.count_down_timer:
            entities.append(FlameConnectTimerEndSensor(coordinator, TIMER_END_DESCRIPTION, fire))

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


class FlameConnectTimerEndSensor(SensorEntity, FlameConnectEntity):
    """Sensor showing when the fireplace timer will turn off.

    Computes the end time locally when the timer is enabled. The HA
    frontend displays timestamp sensors as relative time ("in 30 min")
    that counts down automatically.
    """

    _timer_end: datetime | None = None
    _last_status: TimerStatus | None = None
    _last_duration: int | None = None

    def __init__(
        self,
        coordinator: FlameConnectDataUpdateCoordinator,
        description: EntityDescription,
        fire: Fire,
    ) -> None:
        """Initialise and compute the initial timer end time."""
        super().__init__(coordinator, description, fire)
        self._update_timer_end()

    def _update_timer_end(self) -> None:
        """Recompute the timer end time if the timer state changed."""
        param = self._get_param(TimerParam)
        if param is None:
            self._timer_end = None
            self._last_status = None
            self._last_duration = None
            return

        status = param.timer_status
        duration = param.duration

        if status != TimerStatus.ENABLED:
            self._timer_end = None
        elif status != self._last_status or duration != self._last_duration:
            # Timer was just enabled or duration changed — compute new end time.
            self._timer_end = dt_util.utcnow() + timedelta(minutes=duration)

        self._last_status = status
        self._last_duration = duration

    def _handle_coordinator_update(self) -> None:
        """Handle coordinator data update by recomputing the timer end."""
        self._update_timer_end()
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> datetime | None:
        """Return the timer end time, or None if expired or inactive."""
        if self._timer_end is not None and self._timer_end <= dt_util.utcnow():
            self._timer_end = None
        return self._timer_end
