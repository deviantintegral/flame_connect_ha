"""Tests that hacs.json stays in sync with the Home Assistant version under test."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.const import MAJOR_VERSION, MINOR_VERSION

HACS_JSON = Path(__file__).parent.parent / "hacs.json"


def test_hacs_minimum_matches_tested_home_assistant() -> None:
    """The hacs.json minimum must be the YEAR.MONTH.0 release of the tested Home Assistant.

    Renovate updates hacs.json and pytest-homeassistant-custom-component in one
    group, but the hacs.json update can arrive before the test harness update.
    Failing here keeps that PR from automerging until both match, so we never
    declare support for a Home Assistant release we don't test against.
    """
    minimum = json.loads(HACS_JSON.read_text(encoding="utf-8"))["homeassistant"]

    assert minimum == f"{MAJOR_VERSION}.{MINOR_VERSION}.0"
