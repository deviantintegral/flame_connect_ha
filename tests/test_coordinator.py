"""Tests for the FlameConnect DataUpdateCoordinator."""

from __future__ import annotations

import dataclasses
from unittest.mock import AsyncMock, patch

from flameconnect import (
    ApiError,
    AuthenticationError,
    Fire,
    FireMode,
    FireOverview,
    FlameConnectError,
    FlameEffect,
    FlameEffectParam,
    ModeParam,
)
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


async def test_write_fields_optimistic_update(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test that async_write_fields updates coordinator data optimistically.

    After writing, the coordinator should reflect the new parameter value
    immediately.  A confirmation refresh is also requested to re-read the
    API and confirm (or correct) the optimistic state.
    """
    config_entry.add_to_hass(hass)

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire]
    coordinator.async_set_updated_data({"abc123": mock_fire_overview})

    with patch.object(coordinator, "async_request_refresh", new_callable=AsyncMock) as mock_refresh:
        await coordinator.async_write_fields("abc123", FlameEffectParam, flame_effect=FlameEffect.OFF)
        mock_refresh.assert_awaited_once()

    # API write must have been performed
    mock_flameconnect_client.write_parameters.assert_called_once()

    # Coordinator data should be optimistically updated
    updated_overview = coordinator.data["abc123"]
    flame_param = next(p for p in updated_overview.parameters if isinstance(p, FlameEffectParam))
    assert flame_param.flame_effect == FlameEffect.OFF


async def test_turn_on_fire_optimistic_update(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test that async_turn_on_fire optimistically sets mode to MANUAL."""
    config_entry.add_to_hass(hass)

    # Start with STANDBY mode
    standby_params = [
        dataclasses.replace(p, mode=FireMode.STANDBY) if isinstance(p, ModeParam) else p
        for p in mock_fire_overview.parameters
    ]
    standby_overview = dataclasses.replace(mock_fire_overview, parameters=standby_params)

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire]
    coordinator.async_set_updated_data({"abc123": standby_overview})

    with patch.object(coordinator, "async_request_refresh", new_callable=AsyncMock) as mock_refresh:
        await coordinator.async_turn_on_fire("abc123")
        mock_refresh.assert_awaited_once()

    # API call must have been performed
    mock_flameconnect_client.turn_on.assert_called_once_with("abc123")

    # Mode should be optimistically set to MANUAL
    updated_overview = coordinator.data["abc123"]
    mode_param = next(p for p in updated_overview.parameters if isinstance(p, ModeParam))
    assert mode_param.mode == FireMode.MANUAL


async def test_turn_off_fire_optimistic_update(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test that async_turn_off_fire optimistically sets mode to STANDBY."""
    config_entry.add_to_hass(hass)

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire]
    # Start with MANUAL mode (from fixture default)
    coordinator.async_set_updated_data({"abc123": mock_fire_overview})

    with patch.object(coordinator, "async_request_refresh", new_callable=AsyncMock) as mock_refresh:
        await coordinator.async_turn_off_fire("abc123")
        mock_refresh.assert_awaited_once()

    # API call must have been performed
    mock_flameconnect_client.turn_off.assert_called_once_with("abc123")

    # Mode should be optimistically set to STANDBY
    updated_overview = coordinator.data["abc123"]
    mode_param = next(p for p in updated_overview.parameters if isinstance(p, ModeParam))
    assert mode_param.mode == FireMode.STANDBY
