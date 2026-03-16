"""Tests for the validate_fireplaces config flow validator."""

from __future__ import annotations

import dataclasses
from unittest.mock import AsyncMock

from flameconnect import Fire, FireOverview
import pytest

from custom_components.flameconnect.config_flow_handler.validators.fireplaces import (
    NoWifiFireplacesError,
    validate_fireplaces,
)


async def test_validate_fireplaces_success(
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test that validation passes when at least one fire has a WiFi overview."""
    await validate_fireplaces(mock_flameconnect_client)

    mock_flameconnect_client.get_fires.assert_awaited_once()
    mock_flameconnect_client.get_fire_overview.assert_awaited_once_with("abc123")


async def test_validate_fireplaces_no_fires(
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test that NoWifiFireplacesError is raised when the account has no fires."""
    mock_flameconnect_client.get_fires.return_value = []

    with pytest.raises(NoWifiFireplacesError):
        await validate_fireplaces(mock_flameconnect_client)


async def test_validate_fireplaces_all_bluetooth_type_error(
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> None:
    """Test that NoWifiFireplacesError is raised when all fires raise TypeError.

    This happens when WifiFireOverview is null in the API response.
    """
    mock_flameconnect_client.get_fire_overview.side_effect = TypeError("'NoneType' object is not subscriptable")

    with pytest.raises(NoWifiFireplacesError):
        await validate_fireplaces(mock_flameconnect_client)


async def test_validate_fireplaces_all_bluetooth_key_error(
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> None:
    """Test that NoWifiFireplacesError is raised when all fires raise KeyError."""
    mock_flameconnect_client.get_fire_overview.side_effect = KeyError("WifiFireOverview")

    with pytest.raises(NoWifiFireplacesError):
        await validate_fireplaces(mock_flameconnect_client)


async def test_validate_fireplaces_mixed_wifi_and_bluetooth(
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test that validation passes when some fires are WiFi and some are Bluetooth."""
    second_fire = dataclasses.replace(mock_fire, fire_id="bt_only", friendly_name="Bluetooth Fire")
    mock_flameconnect_client.get_fires.return_value = [mock_fire, second_fire]
    # First fire raises TypeError (Bluetooth), second returns valid overview
    mock_flameconnect_client.get_fire_overview.side_effect = [
        TypeError("'NoneType' object is not subscriptable"),
        mock_fire_overview,
    ]

    # Should not raise — one fire has a valid overview
    await validate_fireplaces(mock_flameconnect_client)


async def test_validate_fireplaces_first_wifi_short_circuits(
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test that validation returns as soon as the first valid overview is found."""
    second_fire = dataclasses.replace(mock_fire, fire_id="def456", friendly_name="Bedroom")
    mock_flameconnect_client.get_fires.return_value = [mock_fire, second_fire]

    await validate_fireplaces(mock_flameconnect_client)

    # Only the first fire should be checked since it succeeded
    mock_flameconnect_client.get_fire_overview.assert_awaited_once_with("abc123")
