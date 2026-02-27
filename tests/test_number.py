"""Tests for FlameConnect number entities."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from flameconnect import FlameEffectParam
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from homeassistant.core import HomeAssistant
from homeassistant.util.dt import utcnow


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


async def test_flame_speed_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test flame speed number reports native_value from FlameEffectParam."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("number.living_room_flame_speed")
    assert state is not None
    assert float(state.state) == 3.0


async def test_timer_duration_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test timer duration number reports value from TimerParam."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("number.living_room_timer_duration")
    assert state is not None
    assert float(state.state) == 60.0


async def test_set_flame_speed_writes(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test setting flame speed uses read-before-write to update FlameEffectParam."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.living_room_flame_speed", "value": 5},
        blocking=True,
    )

    # Advance time past the debounce delay so the write flushes.
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=2))
    await hass.async_block_till_done()

    mock_flameconnect_client.get_fire_overview.assert_called()
    mock_flameconnect_client.write_parameters.assert_called_once()
    param = mock_flameconnect_client.write_parameters.call_args[0][1][0]
    assert isinstance(param, FlameEffectParam)
    assert param.flame_speed == 5
