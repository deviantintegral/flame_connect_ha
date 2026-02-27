"""Shared test fixtures for the FlameConnect integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from flameconnect import ConnectionState, Fire, FireOverview
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "flameconnect"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> None:
    return


@pytest.fixture
def mock_fire() -> Fire:
    return Fire(
        fire_id="abc123",
        friendly_name="Living Room",
        brand="Dimplex",
        product_type="Bold Ignite XL",
        product_model="BIX-50",
        item_code="ITEM001",
        connection_state=ConnectionState.CONNECTED,
        with_heat=True,
        is_iot_fire=True,
    )


@pytest.fixture
def mock_fire_overview(mock_fire: Fire) -> FireOverview:
    return FireOverview(fire=mock_fire, parameters=[])


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        data={"token_cache": "fake-cache-data"},
        unique_id="user_example_com",
        title="user@example.com",
    )


@pytest.fixture
def mock_flameconnect_client(mock_fire: Fire, mock_fire_overview: FireOverview) -> AsyncMock:
    client = AsyncMock()
    client.get_fires = AsyncMock(return_value=[mock_fire])
    client.get_fire_overview = AsyncMock(return_value=mock_fire_overview)
    client.write_parameters = AsyncMock()
    client.turn_on = AsyncMock()
    client.turn_off = AsyncMock()
    return client


@pytest.fixture
def mock_setup_entry():
    with patch(
        "custom_components.flameconnect.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock
