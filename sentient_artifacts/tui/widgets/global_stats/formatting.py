"""Formatting helpers for the global stats widget."""

from __future__ import annotations


class StatsFormatter:
    """Format numeric values for the stats display."""

    def format_number(self, num: int) -> str:
        """Format a number with comma grouping."""
        return f"{num:,}"

    def format_active_bots(self, value: int, total: int) -> str:
        """Format the active bot count display."""
        return f"{value}/{total}"
