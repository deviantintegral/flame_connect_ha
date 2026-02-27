"""Tests for FlameConnect light entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from flameconnect import FlameEffectParam, LightStatus, LogEffect, LogEffectParam, RGBWColor
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


async def test_media_light_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test media light is on with correct RGBW colour from fixture."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("light.living_room_media_light")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes["rgbw_color"] == (255, 0, 0, 128)


async def test_media_light_effect(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test media light reports current media theme effect."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("light.living_room_media_light")
    assert state is not None
    assert state.attributes["effect"] == "white"


async def test_overhead_light_uses_light_status(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test overhead light reads from light_status, not overhead_light field.

    In the fixture: overhead_light=OFF but light_status=ON.
    The overhead light entity should use light_status for is_on.
    """
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("light.living_room_overhead_light")
    assert state is not None
    # light_status is ON in fixture, so overhead light should be on
    assert state.state == STATE_ON
    assert state.attributes["rgbw_color"] == (255, 255, 255, 255)


async def test_media_light_turn_off_writes(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test turning off media light uses read-before-write with FlameEffectParam."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": "light.living_room_media_light"},
        blocking=True,
    )

    mock_flameconnect_client.get_fire_overview.assert_called()
    mock_flameconnect_client.write_parameters.assert_called_once()
    param = mock_flameconnect_client.write_parameters.call_args[0][1][0]
    assert isinstance(param, FlameEffectParam)
    assert param.media_light == LightStatus.OFF


async def test_media_light_turn_on_with_colour(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test turning on media light with RGBW colour."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.living_room_media_light", "rgbw_color": [0, 255, 0, 64]},
        blocking=True,
    )

    mock_flameconnect_client.write_parameters.assert_called_once()
    param = mock_flameconnect_client.write_parameters.call_args[0][1][0]
    assert isinstance(param, FlameEffectParam)
    assert param.media_light == LightStatus.ON
    assert param.media_color == RGBWColor(0, 255, 0, 64)


async def test_log_effect_light_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test log effect light is off (LogEffect.OFF in fixture)."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("light.living_room_log_effect")
    assert state is not None
    assert state.state == STATE_OFF


async def test_log_effect_light_turn_on_writes(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test turning on log effect light writes LogEffectParam."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.living_room_log_effect"},
        blocking=True,
    )

    mock_flameconnect_client.get_fire_overview.assert_called()
    mock_flameconnect_client.write_parameters.assert_called_once()
    param = mock_flameconnect_client.write_parameters.call_args[0][1][0]
    assert isinstance(param, LogEffectParam)
    assert param.log_effect == LogEffect.ON
