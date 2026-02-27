"""Tests for FlameConnect button entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

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


async def test_refresh_button_exists(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test refresh button entity is created."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    state = hass.states.get("button.living_room_refresh_data")
    assert state is not None


async def test_refresh_button_press(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test pressing refresh button triggers coordinator refresh."""
    await _setup_integration(hass, config_entry, mock_flameconnect_client)

    # Reset call count since setup already called get_fire_overview
    mock_flameconnect_client.get_fire_overview.reset_mock()

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.living_room_refresh_data"},
        blocking=True,
    )

    # The coordinator refresh should trigger a new get_fire_overview call
    mock_flameconnect_client.get_fire_overview.assert_called()
