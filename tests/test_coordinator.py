"""Tests for the FlameConnect DataUpdateCoordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock

from flameconnect import ApiError, AuthenticationError, Fire, FireOverview, FlameConnectError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.flameconnect.coordinator import FlameConnectDataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed


async def test_async_setup_discovers_fires(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> None:
    config_entry.add_to_hass(hass)

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    await coordinator._async_setup()  # noqa: SLF001

    assert coordinator.fires == [mock_fire]
    mock_flameconnect_client.get_fires.assert_awaited_once()


async def test_async_update_data_success(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    config_entry.add_to_hass(hass)

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    # Simulate _async_setup having been called
    coordinator.fires = [mock_fire]

    result = await coordinator._async_update_data()  # noqa: SLF001

    assert result == {"abc123": mock_fire_overview}
    mock_flameconnect_client.get_fire_overview.assert_awaited_once_with("abc123")


async def test_async_update_data_auth_error(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> None:
    config_entry.add_to_hass(hass)

    mock_flameconnect_client.get_fire_overview.side_effect = AuthenticationError("token expired")

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire]

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()  # noqa: SLF001


async def test_async_update_data_api_error(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> None:
    config_entry.add_to_hass(hass)

    mock_flameconnect_client.get_fire_overview.side_effect = ApiError(500, "server error")

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire]

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()  # noqa: SLF001


async def test_async_update_data_flameconnect_error(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> None:
    config_entry.add_to_hass(hass)

    mock_flameconnect_client.get_fire_overview.side_effect = FlameConnectError("generic error")

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire]

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()  # noqa: SLF001
