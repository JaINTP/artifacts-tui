"""Responsive stat bar widget for character cards."""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static


class ResponsiveStatBar(Static):
    """Width-responsive progress bar for Textual layouts."""

    percent = reactive(0)

    def __init__(self, fill_bg: str, empty_bg: str, **kwargs: Any) -> None:
        """Initialize the bar with fill and empty background colors."""
        super().__init__(**kwargs)
        self._fill_style = f"on {fill_bg}"
        self._empty_style = f"on {empty_bg}"

    def watch_percent(self, value: int) -> None:
        """Refresh the bar when the percentage changes."""
        self.refresh()

    def on_resize(self) -> None:
        """Refresh the bar on layout size changes."""
        self.refresh()

    def render(self) -> Text:
        """Render the bar using the current width and percent value."""
        width = max(1, int(self.size.width or 1))
        clamped = max(0, min(100, int(self.percent)))
        filled = int(round((clamped / 100.0) * width))
        empty = max(0, width - filled)

        bar = Text()
        if filled:
            bar.append(" " * filled, style=self._fill_style)
        if empty:
            bar.append(" " * empty, style=self._empty_style)
        return bar
