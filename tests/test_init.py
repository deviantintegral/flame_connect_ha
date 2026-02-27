"""Tests for FlameConnect integration setup and teardown."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

DOMAIN = "flameconnect"


async def test_async_setup_entry(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.flameconnect.create_token_provider",
            return_value=AsyncMock(return_value="fake-token"),
        ),
        patch(
            "custom_components.flameconnect.FlameConnectClient",
            return_value=mock_flameconnect_client,
        ),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state.name == "LOADED"
    assert config_entry.runtime_data is not None
    assert config_entry.runtime_data.client is mock_flameconnect_client


async def test_async_unload_entry(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.flameconnect.create_token_provider",
            return_value=AsyncMock(return_value="fake-token"),
        ),
        patch(
            "custom_components.flameconnect.FlameConnectClient",
            return_value=mock_flameconnect_client,
        ),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state.name == "LOADED"

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state.name == "NOT_LOADED"
