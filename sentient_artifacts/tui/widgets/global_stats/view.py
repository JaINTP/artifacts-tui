"""Global stats widget for displaying overall system status."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Grid
from textual.reactive import reactive
from textual.widgets import Label, Static

from sentient_artifacts.tui.widgets.global_stats.clock import ServerTimeProvider
from sentient_artifacts.tui.widgets.global_stats.formatting import StatsFormatter


class GlobalStats(Static):
    """A widget displaying global system statistics."""

    DEFAULT_CSS = """
    GlobalStats {
        width: 1fr;
        height: auto;
        padding: 1;
        border: solid $primary-lighten-2;
        background: $surface-darken-1;
    }
    GlobalStats > .stats-grid {
        layout: grid;
        grid-size: 3;
        height: auto;
    }
    GlobalStats > .stat-item {
        padding: 1;
        text-align: center;
    }
    GlobalStats > .stat-label {
        color: $text-muted;
        text-style: bold;
    }
    GlobalStats > .stat-value {
        color: $text-accent;
        text-style: bold;
        margin-top: 1;
    }
    GlobalStats > .gold-value {
        color: $warning;
    }
    GlobalStats > .bots-value {
        color: $success;
    }
    GlobalStats > .time-value {
        color: $primary;
    }
    """

    total_gold = reactive(0)
    active_bots = reactive(0)
    server_time = reactive("")
    total_xp = reactive(0)

    def __init__(self, *, max_bots: int = 5, **kwargs: Any) -> None:
        """Initialize the global stats widget."""
        super().__init__(**kwargs)
        self._max_bots = max_bots
        self._formatter = StatsFormatter()
        self._time_provider = ServerTimeProvider()
        self.update_server_time()

    def update_server_time(self) -> None:
        """Update the server time display."""
        self.server_time = self._time_provider.formatted()

    def compose(self) -> ComposeResult:
        """Compose the global stats layout."""
        with Grid(classes="stats-grid"):
            with Static(classes="stat-item"):
                yield Label("Total Gold", classes="stat-label")
                yield Label(str(self.total_gold), classes="stat-value gold-value")
            with Static(classes="stat-item"):
                yield Label("Active Bots", classes="stat-label")
                bots_display = self._formatter.format_active_bots(
                    self.active_bots,
                    self._max_bots,
                )
                yield Label(bots_display, classes="stat-value bots-value")
            with Static(classes="stat-item"):
                yield Label("Server Time", classes="stat-label")
                yield Label(self.server_time, classes="stat-value time-value")

    def watch_total_gold(self, value: int) -> None:
        """React to total gold changes."""
        try:
            values = list(self.query(".stat-value"))
            if values:
                values[0].update(self._formatter.format_number(value))
        except Exception:
            pass

    def watch_active_bots(self, value: int) -> None:
        """React to active bots changes."""
        try:
            values = list(self.query(".stat-value"))
            if len(values) > 1:
                values[1].update(
                    self._formatter.format_active_bots(value, self._max_bots)
                )
        except Exception:
            pass

    def watch_server_time(self, value: str) -> None:
        """React to server time changes."""
        try:
            values = list(self.query(".stat-value"))
            if len(values) > 2:
                values[2].update(value)
        except Exception:
            pass

    def update_stats(
        self,
        total_gold: int | None = None,
        active_bots: int | None = None,
        total_xp: int | None = None,
    ) -> None:
        """Update multiple stats at once."""
        if total_gold is not None:
            self.total_gold = total_gold
        if active_bots is not None:
            self.active_bots = active_bots
        if total_xp is not None:
            self.total_xp = total_xp
        self.update_server_time()
