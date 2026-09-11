"""DataUpdateCoordinator for the FlameConnect integration.

Fetches fire discovery data once at setup, then polls per-fire overview
data on a 24-hour interval with random jitter to avoid thundering-herd
effects across multiple installations.  While the last refresh failed the
interval drops to :data:`RETRY_INTERVAL` so a transient error cannot take
the fireplace out of service until the next daily poll.

All entity writes are routed through this coordinator to prevent races
(per-fire ``asyncio.Lock``) and to debounce rapid slider changes.

Refreshes and writes both run in tasks this integration owns rather than
inline in the caller's task, because Home Assistant cancels the task of a
service call whenever the script or automation that issued it is stopped.
Left inline, that turns a ``mode: restart`` script re-triggering itself
into a failed coordinator update or a half-finished write.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Callable, Coroutine
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
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

if TYPE_CHECKING:
    from custom_components.flameconnect.data import FlameConnectConfigEntry
    from flameconnect import Fire, Parameter
    from homeassistant.core import HomeAssistant

# Steady-state polling interval.  Overview data changes rarely and the
# fireplace pushes nothing, so a long interval keeps cloud load low.
POLL_INTERVAL = timedelta(hours=24)

# Upper bound of the random jitter added to POLL_INTERVAL, spreading the
# daily poll of every installation across an hour.
MAX_JITTER_MINUTES = 60

# Interval used while the last refresh failed.  DataUpdateCoordinator has
# no backoff of its own, it simply re-arms ``update_interval``, so without
# this a single transient failure would leave every entity unavailable
# (and every service call to it silently dropped) until the next daily
# poll.
RETRY_INTERVAL = timedelta(minutes=5)


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
        self._poll_interval = POLL_INTERVAL + timedelta(minutes=randint(0, MAX_JITTER_MINUTES))
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=self._poll_interval,
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
        all_fires = await self.client.get_fires()
        self.fires = [fire for fire in all_fires if fire is not None and fire.fire_id]
        skipped = len(all_fires) - len(self.fires)
        if skipped:
            LOGGER.warning(
                "Skipped %d fire(s) with missing or empty fire ID",
                skipped,
            )
        if not self.fires:
            raise UpdateFailed("No fires with valid fire IDs found in account")
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
        skip_reason: Exception | None = None
        try:
            result: dict[str, FireOverview] = {}
            for fire in self.fires:
                try:
                    overview = await self.client.get_fire_overview(fire.fire_id)
                except (TypeError, KeyError) as err:
                    # The library raises these when ``WifiFireOverview`` is
                    # missing or null, which is how a Bluetooth-only fire
                    # presents.  The same exception types would also be
                    # raised by a cloud response-shape change or a bug in
                    # the decode path, so keep the exception: it is chained
                    # onto the UpdateFailed below and would otherwise be
                    # reported as a benign "no WiFi overview".
                    skip_reason = err
                    LOGGER.debug(
                        "Fire %s (%s) has no WiFi overview, skipping",
                        fire.friendly_name,
                        fire.fire_id,
                        exc_info=True,
                    )
                    continue
                if overview is None:
                    LOGGER.warning(
                        "Received empty overview for fire %s (%s), skipping",
                        fire.friendly_name,
                        fire.fire_id,
                    )
                    continue
                result[fire.fire_id] = overview
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
            if not result:
                message = "All fire overviews returned empty data"
                if skip_reason is not None:
                    message = f"{message} ({type(skip_reason).__name__}: {skip_reason})"
                raise UpdateFailed(message) from skip_reason
            return result

    # ------------------------------------------------------------------
    # Refresh scheduling and failure visibility
    # ------------------------------------------------------------------

    @callback
    def _schedule_refresh(self) -> None:
        """Schedule the next refresh, retrying quickly after a failure.

        ``DataUpdateCoordinator`` implements no retry or backoff of its
        own: after a failed update it simply re-arms ``update_interval``.
        With the steady-state 24 h interval that means one transient
        failure removes the fireplace from service for a day, because
        every entity reports ``available is False`` while
        ``last_update_success`` is False and Home Assistant drops service
        calls to unavailable entities.  Poll on the short
        :data:`RETRY_INTERVAL` until a refresh succeeds again.
        """
        self.update_interval = self._poll_interval if self.last_update_success else RETRY_INTERVAL
        super()._schedule_refresh()

    async def _async_refresh(
        self,
        log_failures: bool = True,
        raise_on_auth_failed: bool = False,
        scheduled: bool = False,
        raise_on_entry_error: bool = False,
    ) -> None:
        """Refresh data, separating caller cancellation from device failure.

        ``DataUpdateCoordinator`` treats ``asyncio.CancelledError`` as a
        failed update: ``last_update_success`` goes False, every entity
        reports ``available is False`` — so Home Assistant silently drops
        service calls to them — and :meth:`_schedule_refresh` drops to
        :data:`RETRY_INTERVAL`.  It distinguishes two cases by whether the
        running task was itself cancelled, and both need handling:

        * **The awaiting task was cancelled** (``task.cancelling() > 0``),
          so Home Assistant re-raises.  This is not evidence about the
          fireplace: the caller simply went away, usually before a single
          request was sent.  A ``mode: restart`` script cancels its own
          in-flight ``button.press`` every time it re-triggers, which would
          otherwise take the whole integration unavailable for
          :data:`RETRY_INTERVAL`.  Restore the previous state — the last
          known good data is a better answer than "unavailable".

        * **Something inside the update was cancelled** while this task was
          not.  Home Assistant swallows that one, and it is a genuine
          failure — the fireplace state is unknown — but it is the only
          failure mode Home Assistant logs nothing at all for, so every
          entity going ``unavailable`` would have no explanation anywhere.
          Log it; the listener broadcast is Home Assistant's own.
        """
        was_successful = self.last_update_success
        previous_exception = self.last_exception
        try:
            await super()._async_refresh(
                log_failures=log_failures,
                raise_on_auth_failed=raise_on_auth_failed,
                scheduled=scheduled,
                raise_on_entry_error=raise_on_entry_error,
            )
        except asyncio.CancelledError:
            self._restore_after_caller_cancellation(was_successful, previous_exception)
            raise

        if (
            was_successful
            and not self.last_update_success
            and isinstance(self.last_exception, asyncio.CancelledError)
            and not self._shutdown_requested
            and not self.hass.is_stopping
        ):
            LOGGER.warning(
                "Refresh of %s data was cancelled; entities are now unavailable, retrying in %s",
                self.name,
                RETRY_INTERVAL,
            )

    @callback
    def _restore_after_caller_cancellation(
        self,
        was_successful: bool,
        previous_exception: BaseException | None,
    ) -> None:
        """Undo the update failure recorded for a cancelled caller.

        Called when ``asyncio.CancelledError`` propagated out of
        ``DataUpdateCoordinator._async_refresh``, which only happens when
        the task awaiting the refresh was cancelled.  Roll back the failure
        it recorded, and where that failure had shortened the poll to
        :data:`RETRY_INTERVAL`, re-arm the schedule.  Shutdown is left
        alone: there is nothing left to schedule and nothing left to
        report.
        """
        if self.last_update_success or self._shutdown_requested or self.hass.is_stopping:
            return
        self.last_update_success = was_successful
        self.last_exception = previous_exception
        if was_successful and self._listeners:
            self._schedule_refresh()
        LOGGER.debug(
            "Refresh of %s data was cancelled by its caller; keeping the previous state",
            self.name,
        )

    # ------------------------------------------------------------------
    # Cancellation-proof entry points
    # ------------------------------------------------------------------

    async def _async_shielded(self, coro: Coroutine[Any, Any, None]) -> None:
        """Run *coro* in a task this integration owns and await it shielded.

        Entity service handlers run inside the task of whoever called
        them, and Home Assistant cancels that task as a matter of normal
        operation — a ``mode: restart`` script cancels its own in-flight
        service call every time it re-triggers.  A cancellation landing
        between the read and the write of a read-modify-write cycle
        abandons the write *after* the API has already been read, with the
        per-fire lock released by unwinding and nothing logged anywhere:
        the automation trace shows the step as run and the fireplace never
        hears about it.

        The task is created on the config entry, so an unload waits for an
        in-flight write instead of cancelling it.
        """
        await asyncio.shield(
            self.config_entry.async_create_task(self.hass, coro, eager_start=True),
        )

    async def async_refresh_shielded(self) -> None:
        """Refresh now, completing even if the caller is cancelled.

        The counterpart of ``async_refresh`` for callers that run inside a
        task Home Assistant may cancel; see :meth:`_async_shielded`.
        """
        await self._async_shielded(self.async_refresh())

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
        back, then immediately pushes the written values into
        ``coordinator.data`` so entities reflect the new state without
        waiting for the confirmation refresh.  A follow-up
        ``async_request_refresh`` re-reads the API to confirm (or
        correct) the optimistic state.

        Any pending debounced writes for the same ``(fire_id, param_type)``
        are absorbed into this write so they are not lost.

        The cycle itself runs shielded, see :meth:`_async_shielded`.
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

        await self._async_shielded(self._async_read_modify_write(fire_id, param_type, changes))

    async def _async_read_modify_write(
        self,
        fire_id: str,
        param_type: type[Parameter],
        changes: dict[str, Any],
    ) -> None:
        """Perform one read-modify-write cycle; see :meth:`async_write_fields`.

        Callers must either be running shielded already or not care about
        being cancelled part way through.
        """
        async with self._write_locks[fire_id]:
            overview = await self.client.get_fire_overview(fire_id)
            param = next((p for p in overview.parameters if isinstance(p, param_type)), None)
            if param is None:
                # Without a default, ``next`` would raise a bare
                # StopIteration inside a coroutine, which Python turns
                # into an opaque RuntimeError.
                msg = f"Fire {fire_id} does not report {param_type.__name__}, cannot write {sorted(changes)}"
                raise HomeAssistantError(msg)
            new_param = dataclasses.replace(param, **changes)
            await self.client.write_parameters(fire_id, [new_param])
        self._apply_optimistic_param_update(fire_id, param_type, new_param, overview)
        await self.async_request_refresh()

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
            # Already an integration-owned task, so no shield is needed.
            self.hass.async_create_task(self._async_read_modify_write(fire_id, param_type, changes))

    async def _async_flush_pending_writes(self, fire_id: str) -> None:
        """Immediately flush all pending debounced writes for a fire.

        Only ever called from inside an already shielded write, so the
        individual cycles use the unshielded helper.
        """
        keys = [k for k in self._pending_writes if k[0] == fire_id]
        for key in keys:
            cancel = self._debounce_timers.pop(key, None)
            if cancel is not None:
                cancel()
            changes = self._pending_writes.pop(key, None)
            if changes:
                await self._async_read_modify_write(key[0], key[1], changes)

    async def async_turn_on_fire(self, fire_id: str) -> None:
        """Flush pending writes, then turn the fire on under lock."""
        await self._async_shielded(self._async_set_fire_power(fire_id, on=True))

    async def async_turn_off_fire(self, fire_id: str) -> None:
        """Flush pending writes, then turn the fire off under lock."""
        await self._async_shielded(self._async_set_fire_power(fire_id, on=False))

    async def _async_set_fire_power(self, fire_id: str, *, on: bool) -> None:
        """Flush pending writes, then switch the fire on or off under lock.

        Runs shielded, see :meth:`_async_shielded`: a cancellation between
        the flush and the power command would leave the flushed settings
        written to a fireplace that was never switched.
        """
        await self._async_flush_pending_writes(fire_id)
        async with self._write_locks[fire_id]:
            if on:
                await self.client.turn_on(fire_id)
            else:
                await self.client.turn_off(fire_id)
        self._apply_optimistic_mode_update(fire_id, FireMode.MANUAL if on else FireMode.STANDBY)
        await self.async_request_refresh()

    @callback
    def _apply_optimistic_param_update(
        self,
        fire_id: str,
        param_type: type[Parameter],
        new_param: Parameter,
        base_overview: FireOverview,
    ) -> None:
        """Push the just-written parameter into coordinator data immediately.

        After a successful API write, this replaces the old parameter in
        the coordinator data with the value we just wrote so entities
        reflect the new state right away, before the follow-up
        ``async_request_refresh`` confirms the value from the API.
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
