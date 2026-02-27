"""Repairs platform for FlameConnect."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.repairs import RepairsFlow
from homeassistant.data_entry_flow import FlowResult

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create a repair flow for the given issue."""
    return FlameConnectReauthRepairFlow()


class FlameConnectReauthRepairFlow(RepairsFlow):
    """Repair flow that directs the user to re-authenticate."""

    async def async_step_init(self, user_input: dict[str, str] | None = None) -> FlowResult:
        """Handle the repair confirmation step."""
        if user_input is not None:
            entry = self.hass.config_entries.async_get_entry(self.handler)
            if entry:
                entry.async_start_reauth(self.hass)
            return self.async_create_entry(data={})

        return self.async_show_form(step_id="init")
