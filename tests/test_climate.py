"""Tests for FlameConnect climate entity."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from flameconnect import FireOverview, HeatControl, HeatModeParam, HeatParam, HeatStatus, TempUnit, TempUnitParam
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.climate.const import HVACMode
from homeassistant.core import HomeAssistant


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


async def test_climate_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test climate entity reports heat mode, normal preset, target temp 22."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("climate.living_room")
    assert state is not None
    assert state.state == HVACMode.HEAT
    assert state.attributes["preset_mode"] == "normal"
    assert state.attributes["temperature"] == 22.0


async def test_set_temperature(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test set_temperature writes HeatParam with updated setpoint."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": "climate.living_room", "temperature": 25.0},
        blocking=True,
    )

    # Read-before-write pattern
    mock_flameconnect_client.get_fire_overview.assert_called()
    mock_flameconnect_client.write_parameters.assert_called_once()
    param = mock_flameconnect_client.write_parameters.call_args[0][1][0]
    assert isinstance(param, HeatParam)
    assert param.setpoint_temperature == 25.0


async def test_set_hvac_mode_off(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test setting HVAC mode to off writes HeatParam with OFF status."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": "climate.living_room", "hvac_mode": HVACMode.OFF},
        blocking=True,
    )

    mock_flameconnect_client.get_fire_overview.assert_called()
    mock_flameconnect_client.write_parameters.assert_called_once()
    param = mock_flameconnect_client.write_parameters.call_args[0][1][0]
    assert isinstance(param, HeatParam)
    assert param.heat_status == HeatStatus.OFF


def _with_fahrenheit_unit(overview: FireOverview) -> FireOverview:
    """Return a copy of *overview* with the device display unit set to Fahrenheit.

    The setpoint is left untouched: the device always stores it in Celsius on
    the wire, so flipping the display unit must not change the stored value.
    """
    new_params = [
        TempUnitParam(unit=TempUnit.FAHRENHEIT) if isinstance(p, TempUnitParam) else p for p in overview.parameters
    ]
    return FireOverview(fire=overview.fire, parameters=new_params)


async def test_climate_state_fahrenheit_device(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire_overview: FireOverview,
) -> None:
    """Test the Celsius setpoint is reported as-is when the device displays Fahrenheit.

    The device stores the 22.0 setpoint in Celsius regardless of its display
    unit, so the entity (which always reports Celsius) must not apply any
    conversion. Previously this path returned (22-32)*5/9 = -5.6.
    """
    mock_flameconnect_client.get_fire_overview.return_value = _with_fahrenheit_unit(mock_fire_overview)

    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("climate.living_room")
    assert state is not None
    assert state.attributes["temperature"] == 22.0


async def test_set_temperature_fahrenheit_device(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire_overview: FireOverview,
) -> None:
    """Test the requested Celsius value is written unchanged for a Fahrenheit device.

    Home Assistant supplies Celsius and the device stores Celsius, so the
    setpoint must be written through verbatim. Previously this path wrote
    25*9/5+32 = 77.0 into the device's Celsius field.
    """
    mock_flameconnect_client.get_fire_overview.return_value = _with_fahrenheit_unit(mock_fire_overview)

    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": "climate.living_room", "temperature": 25.0},
        blocking=True,
    )

    mock_flameconnect_client.write_parameters.assert_called_once()
    param = mock_flameconnect_client.write_parameters.call_args[0][1][0]
    assert isinstance(param, HeatParam)
    assert param.setpoint_temperature == 25.0


async def test_climate_unavailable_when_heat_disabled(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: object,
    mock_fire_overview: FireOverview,
) -> None:
    """Test climate entity is unavailable when heat control is disabled."""
    new_params = [
        HeatModeParam(heat_control=HeatControl.SOFTWARE_DISABLED) if isinstance(p, HeatModeParam) else p
        for p in mock_fire_overview.parameters
    ]
    disabled_overview = FireOverview(fire=mock_fire_overview.fire, parameters=new_params)
    mock_flameconnect_client.get_fire_overview.return_value = disabled_overview

    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("climate.living_room")
    assert state is not None
    assert state.state == "unavailable"
