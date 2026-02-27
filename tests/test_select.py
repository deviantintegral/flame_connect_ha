"""Tests for FlameConnect select entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from flameconnect import FlameColor, FlameEffectParam
from pytest_homeassistant_custom_component.common import MockConfigEntry

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


async def test_flame_color_select_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test flame color select reports current option from FlameEffectParam."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("select.living_room_flame_color")
    assert state is not None
    assert state.state == "yellow"


async def test_brightness_select_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test brightness select reports current option from FlameEffectParam."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("select.living_room_brightness")
    assert state is not None
    assert state.state == "high"


async def test_select_option_writes(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test selecting an option uses read-before-write to update FlameEffectParam."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.living_room_flame_color", "option": "blue"},
        blocking=True,
    )

    mock_flameconnect_client.get_fire_overview.assert_called()
    mock_flameconnect_client.write_parameters.assert_called_once()
    param = mock_flameconnect_client.write_parameters.call_args[0][1][0]
    assert isinstance(param, FlameEffectParam)
    assert param.flame_color == FlameColor.BLUE
