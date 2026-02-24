"""Log console widget for bot events."""

from __future__ import annotations

from typing import Any

from textual.widgets import RichLog

from sentient_artifacts.tui.widgets.log_console.formatting import (
    LogFormatter,
    LogFormatTheme,
    LogTimeFormatter,
)

_LEVEL_COLORS = {
    "debug": "dim cyan",
    "info": "bright_blue",
    "success": "bright_green",
    "warning": "bright_yellow",
    "error": "bright_red",
    "critical": "bold bright_red on red",
    "matrix": "bright_green",
}


class LogConsole(RichLog):
    """Extended log widget for bot events with colored log levels."""

    DEFAULT_CSS = """
    LogConsole {
        width: 1fr;
        height: 1fr;
        border: solid $primary-darken-2;
        background: $surface-darken-1;
        padding: 1;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the log console widget."""
        kwargs.setdefault("max_lines", 800)
        super().__init__(**kwargs)
        self.auto_scroll = True
        self.wrap = False
        self._formatter = LogFormatter(
            LogFormatTheme(level_colors=_LEVEL_COLORS),
            LogTimeFormatter(),
        )

    def log_event(self, event: str, level: str = "info") -> None:
        """Log an event with timestamp and color-coded level."""
        self.write(self._formatter.format_event(event, level))

    def log_matrix(self, data: dict | str) -> None:
        """Log raw JSON data for Matrix Mode."""
        for line in self._formatter.format_matrix_lines(data):
            self.write(line)

    def clear_logs(self) -> None:
        """Clear all logs from the console."""
        self.clear()

    def log_separator(self, title: str = "") -> None:
        """Log a separator line."""
        self.write(self._formatter.format_separator(title))
