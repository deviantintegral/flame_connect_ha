"""Shared test fixtures for the FlameConnect integration."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, patch

from flameconnect import (
    Brightness,
    ConnectionState,
    ErrorParam,
    Fire,
    FireFeatures,
    FireMode,
    FireOverview,
    FlameColor,
    FlameEffect,
    FlameEffectParam,
    HeatControl,
    HeatMode,
    HeatModeParam,
    HeatParam,
    HeatStatus,
    LightStatus,
    LogEffect,
    LogEffectParam,
    MediaTheme,
    ModeParam,
    PulsatingEffect,
    RGBWColor,
    SoftwareVersionParam,
    SoundParam,
    TempUnit,
    TempUnitParam,
    TimerParam,
    TimerStatus,
)
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.flameconnect.coordinator import FlameConnectDataUpdateCoordinator
from homeassistant.core import HomeAssistant

if TYPE_CHECKING:
    from collections.abc import Coroutine

DOMAIN = "flameconnect"


class CancellationHelper:
    """Park a mocked client call, then cancel the task awaiting it.

    Reproduces what Home Assistant does to a service call when the script
    or automation that issued it is stopped -- a ``mode: restart`` script
    cancels its own in-flight call every time it re-triggers.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Bind the helper to the running Home Assistant instance."""
        self._hass = hass

    def block(self, mock_client: AsyncMock, method: str, result: Any = None) -> tuple[asyncio.Event, asyncio.Event]:
        """Make *method* park until released.

        Returns the event set once the call is in flight and the event
        that lets it return.
        """
        entered = asyncio.Event()
        release = asyncio.Event()

        async def blocked(*_args: object, **_kwargs: object) -> Any:
            entered.set()
            await release.wait()
            return result

        setattr(mock_client, method, AsyncMock(side_effect=blocked))
        return entered, release

    async def cancel_in_flight(self, coro: Coroutine[Any, Any, object], entered: asyncio.Event) -> None:
        """Run *coro* as a task and cancel it once it has reached *entered*."""
        caller = self._hass.async_create_task(coro)
        await entered.wait()
        caller.cancel()
        with pytest.raises(asyncio.CancelledError):
            await caller


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
        features=FireFeatures(
            sound=True,
            simple_heat=True,
            advanced_heat=True,
            count_down_timer=True,
            moods=True,
            rgb_flame_accent=True,
            flame_dimming=True,
            rgb_fuel_bed=True,
            flame_fan_speed=True,
            rgb_back_light=True,
            pir_toggle_smart_sense=True,
            rgb_log_effect=True,
            power_boost=True,
            fan_only=True,
        ),
    )


@pytest.fixture
def mock_fire_overview(mock_fire: Fire) -> FireOverview:
    return FireOverview(
        fire=mock_fire,
        parameters=[
            ModeParam(mode=FireMode.MANUAL, target_temperature=21.0),
            FlameEffectParam(
                flame_effect=FlameEffect.ON,
                flame_speed=3,
                brightness=Brightness.HIGH,
                pulsating_effect=PulsatingEffect.OFF,
                media_theme=MediaTheme.WHITE,
                media_light=LightStatus.ON,
                media_color=RGBWColor(255, 0, 0, 128),
                overhead_light=LightStatus.OFF,
                overhead_color=RGBWColor(255, 255, 255, 255),
                light_status=LightStatus.ON,
                flame_color=FlameColor.YELLOW,
                ambient_sensor=LightStatus.OFF,
            ),
            HeatParam(
                heat_status=HeatStatus.ON,
                heat_mode=HeatMode.NORMAL,
                setpoint_temperature=22.0,
                boost_duration=30,
            ),
            HeatModeParam(heat_control=HeatControl.ENABLED),
            TimerParam(timer_status=TimerStatus.DISABLED, duration=60),
            TempUnitParam(unit=TempUnit.CELSIUS),
            SoftwareVersionParam(
                ui_major=1,
                ui_minor=2,
                ui_test=3,
                control_major=4,
                control_minor=5,
                control_test=6,
                relay_major=7,
                relay_minor=8,
                relay_test=9,
            ),
            ErrorParam(error_byte1=0, error_byte2=0, error_byte3=0, error_byte4=0),
            SoundParam(volume=50, sound_file=1),
            LogEffectParam(
                log_effect=LogEffect.OFF,
                color=RGBWColor(0, 255, 0, 0),
                pattern=0,
            ),
        ],
    )


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


@pytest.fixture
def cancellation(hass: HomeAssistant) -> CancellationHelper:
    """Return the helper for cancelling a caller mid-request."""
    return CancellationHelper(hass)


@pytest.fixture
async def coordinator(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> FlameConnectDataUpdateCoordinator:
    """Return a coordinator that has completed one successful refresh.

    ``coordinator.client`` is ``mock_flameconnect_client``, so a test can
    reach the mocked API through the coordinator it is given.
    """
    config_entry.add_to_hass(hass)
    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire]
    await coordinator.async_refresh()
    assert coordinator.last_update_success is True
    return coordinator
