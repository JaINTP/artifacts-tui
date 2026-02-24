"""Tests for TUI demand polling behavior."""

from __future__ import annotations

import pytest

pytest.importorskip("textual")

from sentient_artifacts.tui.app import TUI


class _DemandWidgetStub:
    """Stub widget collecting demand updates."""

    def __init__(self):
        """Initialize capture lists."""
        self.snapshot_calls = []

    def update_from_snapshot(self, snapshot):
        """Record snapshot updates."""
        self.snapshot_calls.append(snapshot)


class _ManagerWithDemand:
    """Stub manager returning a predefined demand snapshot."""

    def __init__(self, snapshot):
        """Initialize with a static snapshot."""
        self._snapshot = snapshot

    def get_swarm_demand_snapshot(self):
        """Return the stored snapshot."""
        return self._snapshot


def test_poll_swarm_demand_uses_manager_snapshot_when_available():
    """Ensure polling uses manager snapshots when available."""
    snapshot = {
        "crafting_targets": {"iron_shield": 1},
        "character_demands": {},
        "character_requests": {},
        "bounties": [],
    }
    app = TUI(bot_manager=_ManagerWithDemand(snapshot))
    app.demand_widget = _DemandWidgetStub()

    app.poll_swarm_demand()

    assert app.demand_widget.snapshot_calls
    assert app.demand_widget.snapshot_calls[0]["crafting_targets"]["iron_shield"] == 1
