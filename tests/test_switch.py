"""Tests for FlameConnect switch entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from flameconnect import (
    Fire,
    FireMode,
    FireOverview,
    FlameEffect,
    FlameEffectParam,
    ModeParam,
    PulsatingEffect,
    TimerParam,
    TimerStatus,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import STATE_OFF, STATE_ON
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


async def test_power_switch_state_on(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test power switch reports 'on' when mode is MANUAL."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("switch.living_room_power")
    assert state is not None
    assert state.state == STATE_ON


async def test_power_switch_state_off(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test power switch reports 'off' when mode is STANDBY."""
    # Replace the ModeParam to set STANDBY mode
    new_params = [
        ModeParam(mode=FireMode.STANDBY, target_temperature=21.0) if isinstance(p, ModeParam) else p
        for p in mock_fire_overview.parameters
    ]
    off_overview = FireOverview(fire=mock_fire, parameters=new_params)
    mock_flameconnect_client.get_fire_overview.return_value = off_overview

    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("switch.living_room_power")
    assert state is not None
    assert state.state == STATE_OFF


async def test_power_switch_turn_off(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test turning off the power switch calls client.turn_off."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.living_room_power"},
        blocking=True,
    )

    mock_flameconnect_client.turn_off.assert_called_once_with("abc123")


async def test_power_switch_turn_on(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test turning on the power switch calls client.turn_on."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.living_room_power"},
        blocking=True,
    )

    mock_flameconnect_client.turn_on.assert_called_once_with("abc123")


async def test_flame_effect_switch_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test flame effect switch reflects FlameEffectParam.flame_effect."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("switch.living_room_flame_effect")
    assert state is not None
    assert state.state == STATE_ON


async def test_flame_effect_switch_turn_off_writes(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test turning off flame effect uses read-before-write pattern."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.living_room_flame_effect"},
        blocking=True,
    )

    # Read-before-write: get_fire_overview must be called first
    mock_flameconnect_client.get_fire_overview.assert_called()
    mock_flameconnect_client.write_parameters.assert_called_once()
    written_params = mock_flameconnect_client.write_parameters.call_args[0]
    assert written_params[0] == "abc123"
    param = written_params[1][0]
    assert isinstance(param, FlameEffectParam)
    assert param.flame_effect == FlameEffect.OFF


async def test_pulsating_effect_switch_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test pulsating effect switch reflects PulsatingEffect.OFF."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("switch.living_room_pulsating_effect")
    assert state is not None
    assert state.state == STATE_OFF


async def test_pulsating_effect_switch_turn_on_writes(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test enabling pulsating effect uses read-before-write."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.living_room_pulsating_effect"},
        blocking=True,
    )

    mock_flameconnect_client.get_fire_overview.assert_called()
    mock_flameconnect_client.write_parameters.assert_called_once()
    param = mock_flameconnect_client.write_parameters.call_args[0][1][0]
    assert isinstance(param, FlameEffectParam)
    assert param.pulsating_effect == PulsatingEffect.ON


async def test_timer_switch_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test timer switch reflects TimerStatus.DISABLED."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("switch.living_room_timer")
    assert state is not None
    assert state.state == STATE_OFF


async def test_timer_switch_turn_on_preserves_duration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test enabling timer preserves the current duration."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.living_room_timer"},
        blocking=True,
    )

    mock_flameconnect_client.write_parameters.assert_called_once()
    param = mock_flameconnect_client.write_parameters.call_args[0][1][0]
    assert isinstance(param, TimerParam)
    assert param.timer_status == TimerStatus.ENABLED
    assert param.duration == 60  # preserved from fixture
