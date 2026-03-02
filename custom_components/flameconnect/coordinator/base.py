"""DataUpdateCoordinator for the FlameConnect integration.

Fetches fire discovery data once at setup, then polls per-fire overview
data on a 24-hour interval with random jitter to avoid thundering-herd
effects across multiple installations.

All entity writes are routed through this coordinator to prevent races
(per-fire ``asyncio.Lock``) and to debounce rapid slider changes.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Callable
import dataclasses
from datetime import datetime, timedelta
from functools import partial
from random import randint
from typing import TYPE_CHECKING, Any

from custom_components.flameconnect.const import DOMAIN, LOGGER
from flameconnect import (
    ApiError,
    AuthenticationError,
    FireMode,
    FireOverview,
    FlameConnectClient,
    FlameConnectError,
    ModeParam,
)
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

if TYPE_CHECKING:
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from flameconnect import Fire, Parameter
    from homeassistant.core import HomeAssistant


class FlameConnectDataUpdateCoordinator(DataUpdateCoordinator[dict[str, FireOverview]]):
    """Coordinator that polls FlameConnect cloud for fireplace data.

    All parameter writes go through ``async_write_fields`` (immediate) or
    ``async_write_fields_debounced`` (coalesced).  A per-fire
    ``asyncio.Lock`` serialises read-modify-write cycles so concurrent
    writes to the same parameter type never race.

    Attributes:
        config_entry: The config entry for this integration instance.
        fires: List of discovered fires, populated by _async_setup.
    """

    config_entry: FlameConnectConfigEntry
    fires: list[Fire]

    def __init__(
        self,
        hass: HomeAssistant,
        client: FlameConnectClient,
        entry: FlameConnectConfigEntry,
    ) -> None:
        """Initialise the coordinator with a 24 h + jitter update interval."""
        jitter = timedelta(minutes=randint(0, 60))
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(hours=24) + jitter,
        )
        self.client = client

        self._write_locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._pending_writes: dict[tuple[str, type[Parameter]], dict[str, Any]] = {}
        self._debounce_timers: dict[tuple[str, type[Parameter]], Callable[[], None]] = {}

        # Desired timer duration per fire, stored locally (not written to
        # the API until the timer switch is actually turned on).
        self.timer_durations: dict[str, int] = {}

        # Desired boost duration per fire, stored locally (not written to
        # the API until boost mode is actually activated).
        self.boost_durations: dict[str, int] = {}

    async def _async_setup(self) -> None:
        """Discover all fires during first refresh."""
        self.fires = await self.client.get_fires()
        for fire in self.fires:
            enabled_features = [f.name for f in dataclasses.fields(fire.features) if getattr(fire.features, f.name)]
            LOGGER.debug(
                "Discovered fire %s (%s): with_heat=%s, brand=%s, model=%s, features=%s",
                fire.friendly_name,
                fire.fire_id,
                fire.with_heat,
                fire.brand,
                fire.product_type,
                ", ".join(enabled_features) if enabled_features else "none",
            )

    async def _async_update_data(self) -> dict[str, FireOverview]:
        """Fetch overview data for every discovered fire."""
        try:
            result: dict[str, FireOverview] = {}
            for fire in self.fires:
                result[fire.fire_id] = await self.client.get_fire_overview(fire.fire_id)
        except AuthenticationError as err:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "auth_expired",
                is_fixable=True,
                severity=ir.IssueSeverity.ERROR,
                translation_key="auth_expired",
            )
            raise ConfigEntryAuthFailed from err
        except (ApiError, FlameConnectError) as err:
            raise UpdateFailed(str(err)) from err
        else:
            return result

    # ------------------------------------------------------------------
    # Centralised write helpers
    # ------------------------------------------------------------------

    async def async_write_fields(
        self,
        fire_id: str,
        param_type: type[Parameter],
        **changes: Any,
    ) -> None:
        """Read-modify-write a parameter under the per-fire lock.

        Acquires the lock for *fire_id*, fetches a fresh overview from
        the API, applies *changes* via ``dataclasses.replace``, writes
        back, then optimistically updates coordinator data so entities
        reflect the new state immediately without a second API poll.

        Any pending debounced writes for the same ``(fire_id, param_type)``
        are absorbed into this write so they are not lost.
        """
        key = (fire_id, param_type)
        pending = self._pending_writes.pop(key, None)
        if pending is not None:
            cancel = self._debounce_timers.pop(key, None)
            if cancel is not None:
                cancel()
            # Explicit changes are the base; pending user input wins on conflict.
            merged = dict(changes)
            merged.update(pending)
            changes = merged

        async with self._write_locks[fire_id]:
            overview = await self.client.get_fire_overview(fire_id)
            param = next(p for p in overview.parameters if isinstance(p, param_type))
            new_param = dataclasses.replace(param, **changes)
            await self.client.write_parameters(fire_id, [new_param])
        self._apply_optimistic_param_update(fire_id, param_type, new_param, overview)

    async def async_write_fields_debounced(
        self,
        fire_id: str,
        param_type: type[Parameter],
        delay: float = 1.0,
        **changes: Any,
    ) -> None:
        """Accumulate field changes and flush after *delay* seconds.

        Repeated calls within the delay window merge their changes so
        only a single API write is performed with the final values
        (e.g. rapid slider increments).
        """
        key = (fire_id, param_type)
        pending = self._pending_writes.get(key)
        if pending is not None:
            pending.update(changes)
        else:
            self._pending_writes[key] = dict(changes)

        cancel = self._debounce_timers.get(key)
        if cancel is not None:
            cancel()

        self._debounce_timers[key] = async_call_later(
            self.hass,
            delay,
            partial(self._flush_debounced_write, fire_id, param_type),
        )

    @callback
    def _flush_debounced_write(
        self,
        fire_id: str,
        param_type: type[Parameter],
        _now: datetime,
    ) -> None:
        """Pop pending changes and create an ``async_write_fields`` task."""
        key = (fire_id, param_type)
        changes = self._pending_writes.pop(key, None)
        self._debounce_timers.pop(key, None)
        if changes:
            self.hass.async_create_task(self.async_write_fields(fire_id, param_type, **changes))

    async def async_flush_pending_writes(self, fire_id: str) -> None:
        """Immediately flush all pending debounced writes for a fire."""
        keys = [k for k in self._pending_writes if k[0] == fire_id]
        for key in keys:
            cancel = self._debounce_timers.pop(key, None)
            if cancel is not None:
                cancel()
            changes = self._pending_writes.pop(key, None)
            if changes:
                await self.async_write_fields(key[0], key[1], **changes)

    async def async_turn_on_fire(self, fire_id: str) -> None:
        """Flush pending writes, then turn the fire on under lock."""
        await self.async_flush_pending_writes(fire_id)
        async with self._write_locks[fire_id]:
            await self.client.turn_on(fire_id)
        self._apply_optimistic_mode_update(fire_id, FireMode.MANUAL)

    async def async_turn_off_fire(self, fire_id: str) -> None:
        """Flush pending writes, then turn the fire off under lock."""
        await self.async_flush_pending_writes(fire_id)
        async with self._write_locks[fire_id]:
            await self.client.turn_off(fire_id)
        self._apply_optimistic_mode_update(fire_id, FireMode.STANDBY)

    @callback
    def _apply_optimistic_param_update(
        self,
        fire_id: str,
        param_type: type[Parameter],
        new_param: Parameter,
        base_overview: FireOverview,
    ) -> None:
        """Update coordinator data with written parameter to prevent state bounce.

        After a successful API write, this replaces the old parameter in
        the coordinator data with the value we just wrote, so entities
        reflect the new state immediately without waiting for the next
        API poll (which could return stale data).
        """
        new_params: list[Parameter] = [new_param if isinstance(p, param_type) else p for p in base_overview.parameters]
        new_overview = dataclasses.replace(base_overview, parameters=new_params)
        new_data = dict(self.data) if self.data else {}
        new_data[fire_id] = new_overview
        self.async_set_updated_data(new_data)

    @callback
    def _apply_optimistic_mode_update(self, fire_id: str, mode: FireMode) -> None:
        """Update coordinator data with expected fire mode after turn on/off."""
        if self.data is None or fire_id not in self.data:
            return
        overview = self.data[fire_id]
        current_mode = next((p for p in overview.parameters if isinstance(p, ModeParam)), None)
        if current_mode is None:
            return
        self._apply_optimistic_param_update(fire_id, ModeParam, dataclasses.replace(current_mode, mode=mode), overview)

    async def async_shutdown(self) -> None:
        """Cancel all debounce timers and shut down."""
        for cancel in self._debounce_timers.values():
            cancel()
        self._debounce_timers.clear()
        self._pending_writes.clear()
        await super().async_shutdown()
