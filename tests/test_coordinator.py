"""Tests for the FlameConnect DataUpdateCoordinator."""

from __future__ import annotations

import asyncio
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
from custom_components.flameconnect.coordinator.base import RETRY_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

# ------------------------------------------------------------------
# _async_setup: fire filtering
# ------------------------------------------------------------------


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


async def test_async_setup_filters_none_fires(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> None:
    """Test that None entries in the fire list are filtered out."""
    config_entry.add_to_hass(hass)
    mock_flameconnect_client.get_fires.return_value = [None, mock_fire, None]

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    await coordinator._async_setup()  # noqa: SLF001

    assert coordinator.fires == [mock_fire]


async def test_async_setup_filters_fires_with_empty_id(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> None:
    """Test that fires with empty or missing fire_id are filtered out."""
    config_entry.add_to_hass(hass)
    empty_id_fire = dataclasses.replace(mock_fire, fire_id="")
    mock_flameconnect_client.get_fires.return_value = [empty_id_fire, mock_fire]

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    await coordinator._async_setup()  # noqa: SLF001

    assert coordinator.fires == [mock_fire]


async def test_async_setup_raises_when_no_valid_fires(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
) -> None:
    """Test that UpdateFailed is raised when all fires are invalid."""
    config_entry.add_to_hass(hass)
    mock_flameconnect_client.get_fires.return_value = [None]

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)

    with pytest.raises(UpdateFailed, match="No fires with valid fire IDs found"):
        await coordinator._async_setup()  # noqa: SLF001


async def test_async_setup_raises_when_all_fires_have_empty_ids(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> None:
    """Test that UpdateFailed is raised when all fires have empty IDs."""
    config_entry.add_to_hass(hass)
    empty_id_fire = dataclasses.replace(mock_fire, fire_id="")
    mock_flameconnect_client.get_fires.return_value = [empty_id_fire]

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)

    with pytest.raises(UpdateFailed, match="No fires with valid fire IDs found"):
        await coordinator._async_setup()  # noqa: SLF001


# ------------------------------------------------------------------
# _async_update_data: overview handling
# ------------------------------------------------------------------


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


async def test_async_update_data_skips_type_error_overview(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test that a TypeError from get_fire_overview is caught and the fire is skipped.

    This happens when WifiFireOverview is null in the API response, causing
    the library to crash with TypeError when accessing its fields.
    """
    config_entry.add_to_hass(hass)
    second_fire = dataclasses.replace(mock_fire, fire_id="def456", friendly_name="Bedroom")
    mock_flameconnect_client.get_fire_overview.side_effect = [
        TypeError("'NoneType' object is not subscriptable"),
        mock_fire_overview,
    ]

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire, second_fire]

    result = await coordinator._async_update_data()  # noqa: SLF001

    assert "abc123" not in result
    assert result["def456"] == mock_fire_overview


async def test_async_update_data_skips_key_error_overview(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test that a KeyError from get_fire_overview is caught and the fire is skipped."""
    config_entry.add_to_hass(hass)
    second_fire = dataclasses.replace(mock_fire, fire_id="def456", friendly_name="Bedroom")
    mock_flameconnect_client.get_fire_overview.side_effect = [
        KeyError("WifiFireOverview"),
        mock_fire_overview,
    ]

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire, second_fire]

    result = await coordinator._async_update_data()  # noqa: SLF001

    assert "abc123" not in result
    assert result["def456"] == mock_fire_overview


async def test_async_update_data_skips_none_overview(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Test that a None overview is skipped without crashing."""
    config_entry.add_to_hass(hass)
    second_fire = dataclasses.replace(mock_fire, fire_id="def456", friendly_name="Bedroom")
    mock_flameconnect_client.get_fire_overview.side_effect = [None, mock_fire_overview]

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire, second_fire]

    result = await coordinator._async_update_data()  # noqa: SLF001

    assert "abc123" not in result
    assert result["def456"] == mock_fire_overview


async def test_async_update_data_all_overviews_none(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> None:
    """Test that UpdateFailed is raised when all overviews are None."""
    config_entry.add_to_hass(hass)
    mock_flameconnect_client.get_fire_overview.return_value = None

    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire]

    with pytest.raises(UpdateFailed, match="All fire overviews returned empty data"):
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


# ------------------------------------------------------------------
# Cancellation: a caller going away is not a device failure
# ------------------------------------------------------------------


def _blocking_overview(
    mock_flameconnect_client: AsyncMock,
    overview: FireOverview,
) -> tuple[asyncio.Event, asyncio.Event]:
    """Make ``get_fire_overview`` park until released.

    Returns the event set once the call is in flight and the event that
    lets it return, so a test can cancel a caller mid-request.
    """
    entered = asyncio.Event()
    release = asyncio.Event()

    async def blocked(_fire_id: str) -> FireOverview:
        entered.set()
        await release.wait()
        return overview

    mock_flameconnect_client.get_fire_overview = AsyncMock(side_effect=blocked)
    return entered, release


async def _make_coordinator(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
) -> FlameConnectDataUpdateCoordinator:
    """Return a coordinator that has completed one successful refresh."""
    config_entry.add_to_hass(hass)
    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire]
    await coordinator.async_refresh()
    assert coordinator.last_update_success is True
    return coordinator


async def test_refresh_cancelled_by_caller_keeps_previous_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Cancelling the task that awaits a refresh must not fail the coordinator.

    Home Assistant cancels a service call task whenever the script or
    automation that issued it is stopped, which a ``mode: restart`` script
    does routinely.  ``DataUpdateCoordinator`` records that cancellation as
    a failed update, which would take every entity unavailable and drop the
    poll to RETRY_INTERVAL even though nothing is wrong with the fireplace.
    """
    coordinator = await _make_coordinator(hass, config_entry, mock_flameconnect_client, mock_fire)
    updates: list[None] = []
    unsub = coordinator.async_add_listener(lambda: updates.append(None))
    steady_interval = coordinator.update_interval

    entered, release = _blocking_overview(mock_flameconnect_client, mock_fire_overview)
    caller = hass.async_create_task(coordinator.async_refresh())
    await entered.wait()
    caller.cancel()
    with pytest.raises(asyncio.CancelledError):
        await caller

    assert coordinator.last_update_success is True
    assert coordinator.last_exception is None
    assert coordinator.data == {"abc123": mock_fire_overview}
    # Not a failure, so the daily poll must stay armed rather than RETRY_INTERVAL.
    assert coordinator.update_interval == steady_interval
    # Entities must not be told anything changed.
    assert updates == []

    release.set()
    unsub()
    await coordinator.async_shutdown()
    await hass.async_block_till_done()


async def test_refresh_cancelled_by_caller_keeps_previous_failure(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """A cancelled caller must not paper over a coordinator that is failing."""
    coordinator = await _make_coordinator(hass, config_entry, mock_flameconnect_client, mock_fire)
    unsub = coordinator.async_add_listener(lambda: None)

    mock_flameconnect_client.get_fire_overview.side_effect = ApiError(500, "server error")
    await coordinator.async_refresh()
    assert coordinator.last_update_success is False
    assert coordinator.update_interval == RETRY_INTERVAL

    entered, release = _blocking_overview(mock_flameconnect_client, mock_fire_overview)
    caller = hass.async_create_task(coordinator.async_refresh())
    await entered.wait()
    caller.cancel()
    with pytest.raises(asyncio.CancelledError):
        await caller

    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)
    assert coordinator.update_interval == RETRY_INTERVAL

    release.set()
    unsub()
    await coordinator.async_shutdown()
    await hass.async_block_till_done()


async def test_refresh_cancelled_internally_marks_entities_unavailable(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A cancellation from inside the update is a real failure and must show.

    Home Assistant only re-raises a cancellation when the running task was
    itself cancelled.  One raised from within the update is a genuine
    failure, but it is the only failure mode Home Assistant logs nothing
    for, so entities would go unavailable with no explanation anywhere.
    """
    coordinator = await _make_coordinator(hass, config_entry, mock_flameconnect_client, mock_fire)
    updates: list[None] = []
    unsub = coordinator.async_add_listener(lambda: updates.append(None))

    mock_flameconnect_client.get_fire_overview.side_effect = asyncio.CancelledError
    with caplog.at_level("WARNING"):
        await coordinator.async_refresh()

    assert coordinator.last_update_success is False
    assert coordinator.update_interval == RETRY_INTERVAL
    assert updates == [None]  # entities told to re-read availability
    assert "was cancelled; entities are now unavailable" in caplog.text

    unsub()
    await coordinator.async_shutdown()
    await hass.async_block_till_done()


async def test_write_fields_completes_when_caller_cancelled(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """A cancelled caller must not abandon a read-modify-write half way.

    ``async_write_fields`` reads a fresh overview and then writes it back.
    Cancelled between the two, the write would be dropped after the read,
    with the automation trace showing the step as run and nothing reaching
    the fireplace.
    """
    config_entry.add_to_hass(hass)
    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire]
    coordinator.async_set_updated_data({"abc123": mock_fire_overview})

    entered, release = _blocking_overview(mock_flameconnect_client, mock_fire_overview)
    with patch.object(coordinator, "async_request_refresh", new_callable=AsyncMock):
        caller = hass.async_create_task(
            coordinator.async_write_fields("abc123", FlameEffectParam, flame_effect=FlameEffect.OFF)
        )
        await entered.wait()
        caller.cancel()
        with pytest.raises(asyncio.CancelledError):
            await caller

        # The read was in flight when the caller went away; the write must
        # still be delivered.
        assert mock_flameconnect_client.write_parameters.call_count == 0
        release.set()
        await hass.async_block_till_done()

    mock_flameconnect_client.write_parameters.assert_called_once()
    written = mock_flameconnect_client.write_parameters.call_args[0][1][0]
    assert written.flame_effect == FlameEffect.OFF

    flame_param = next(p for p in coordinator.data["abc123"].parameters if isinstance(p, FlameEffectParam))
    assert flame_param.flame_effect == FlameEffect.OFF


async def test_turn_on_fire_completes_when_caller_cancelled(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_flameconnect_client: AsyncMock,
    mock_fire: Fire,
    mock_fire_overview: FireOverview,
) -> None:
    """Turning the fire on must survive its caller being cancelled."""
    config_entry.add_to_hass(hass)
    standby_params = [
        dataclasses.replace(p, mode=FireMode.STANDBY) if isinstance(p, ModeParam) else p
        for p in mock_fire_overview.parameters
    ]
    coordinator = FlameConnectDataUpdateCoordinator(hass, mock_flameconnect_client, config_entry)
    coordinator.fires = [mock_fire]
    coordinator.async_set_updated_data({"abc123": dataclasses.replace(mock_fire_overview, parameters=standby_params)})

    entered = asyncio.Event()
    release = asyncio.Event()

    async def blocked_turn_on(_fire_id: str) -> None:
        entered.set()
        await release.wait()

    mock_flameconnect_client.turn_on = AsyncMock(side_effect=blocked_turn_on)

    with patch.object(coordinator, "async_request_refresh", new_callable=AsyncMock):
        caller = hass.async_create_task(coordinator.async_turn_on_fire("abc123"))
        await entered.wait()
        caller.cancel()
        with pytest.raises(asyncio.CancelledError):
            await caller

        release.set()
        await hass.async_block_till_done()

    mock_flameconnect_client.turn_on.assert_called_once_with("abc123")
    mode_param = next(p for p in coordinator.data["abc123"].parameters if isinstance(p, ModeParam))
    assert mode_param.mode == FireMode.MANUAL
