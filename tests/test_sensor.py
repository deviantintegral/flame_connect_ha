"""Tests for FlameConnect sensor entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from flameconnect import Fire, FireOverview, HeatMode, HeatParam, HeatStatus, TimerParam, TimerStatus
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.flameconnect.sensor import (
    SENSOR_DESCRIPTIONS,
    FlameConnectConnectionStateSensor,
    FlameConnectErrorCodesSensor,
    FlameConnectSoftwareVersionSensor,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def _setup_integration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_client: AsyncMock,
) -> None:
    """Set up the integration with mocked client."""
    config_entry.add_to_hass(hass)
    with (
        patch(
            "custom_components.flameconnect.FlameConnectClient",
            return_value=mock_client,
        ),
        patch("custom_components.flameconnect.TokenAuth"),
        patch("custom_components.flameconnect.create_token_provider"),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()


async def test_sensors_disabled_by_default(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test all sensor entities are disabled by default in entity registry."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    registry = er.async_get(hass)

    for key in ("connection_state", "software_version", "error_codes"):
        entity_id = f"sensor.living_room_{key}"
        entry = registry.async_get(entity_id)
        assert entry is not None, f"{entity_id} not in registry"
        assert entry.disabled_by is not None, f"{entity_id} should be disabled"


async def test_connection_state_sensor_native_value(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test connection state sensor native_value property reads from coordinator data."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    coordinator = config_entry.runtime_data.coordinator
    sensor = FlameConnectConnectionStateSensor(coordinator, SENSOR_DESCRIPTIONS[0], mock_fire)
    assert sensor.native_value == "Connected"


async def test_software_version_sensor_native_value(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test software version sensor formats version string correctly."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    coordinator = config_entry.runtime_data.coordinator
    sensor = FlameConnectSoftwareVersionSensor(coordinator, SENSOR_DESCRIPTIONS[1], mock_fire)
    assert sensor.native_value == "UI:1.2.3 Ctrl:4.5.6 Relay:7.8.9"


async def test_error_codes_sensor_native_value(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test error codes sensor formats hex values correctly."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    coordinator = config_entry.runtime_data.coordinator
    sensor = FlameConnectErrorCodesSensor(coordinator, SENSOR_DESCRIPTIONS[2], mock_fire)
    assert sensor.native_value == "00:00:00:00"


async def test_timer_end_sensor_setup_with_timer_enabled(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire_overview: FireOverview,
) -> None:
    """Test timer end sensor initialises without error when timer is active at setup."""
    new_params = [
        TimerParam(timer_status=TimerStatus.ENABLED, duration=30) if isinstance(p, TimerParam) else p
        for p in mock_fire_overview.parameters
    ]
    enabled_overview = FireOverview(fire=mock_fire_overview.fire, parameters=new_params)
    mock_flameconnect_client.get_fire_overview.return_value = enabled_overview

    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("sensor.living_room_timer_end")
    assert state is not None
    assert state.state != "unavailable"


async def test_timer_end_sensor_unavailable_when_disabled(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test timer end sensor is unavailable when timer is disabled."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("sensor.living_room_timer_end")
    assert state is not None
    assert state.state == "unavailable"


async def test_boost_end_sensor_setup_with_boost_active(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire_overview: FireOverview,
) -> None:
    """Test boost end sensor initialises without error when boost is active at setup."""
    new_params = [
        HeatParam(heat_status=HeatStatus.ON, heat_mode=HeatMode.BOOST, setpoint_temperature=22.0, boost_duration=10)
        if isinstance(p, HeatParam)
        else p
        for p in mock_fire_overview.parameters
    ]
    boost_overview = FireOverview(fire=mock_fire_overview.fire, parameters=new_params)
    mock_flameconnect_client.get_fire_overview.return_value = boost_overview

    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("sensor.living_room_boost_end")
    assert state is not None
    assert state.state != "unavailable"


async def test_boost_end_sensor_unavailable_when_not_boosting(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test boost end sensor is unavailable when heat mode is not boost."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("sensor.living_room_boost_end")
    assert state is not None
    assert state.state == "unavailable"
