"""Formatting helpers for log console output."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from rich.text import Text


@dataclass(frozen=True)
class LogFormatTheme:
    """Theme configuration for log output."""

    level_colors: Mapping[str, str]
    timestamp_style: str = "grey50"
    matrix_timestamp_style: str = "green3"
    matrix_arrow_style: str = "bright_green"
    matrix_line_style: str = "bright_green"
    separator_style: str = "grey50"


class LogTimeFormatter:
    """Provide formatted timestamps for log output."""

    def __init__(
        self,
        *,
        time_format: str = "%H:%M:%S",
        ms_format: str = "%H:%M:%S.%f",
    ) -> None:
        """Initialize timestamp format patterns."""
        self._time_format = time_format
        self._ms_format = ms_format

    def timestamp(self) -> str:
        """Return a timestamp formatted without milliseconds."""
        return datetime.now().strftime(self._time_format)

    def timestamp_ms(self) -> str:
        """Return a timestamp formatted with milliseconds."""
        return datetime.now().strftime(self._ms_format)[:-3]


class LogFormatter:
    """Build Rich text payloads for log output."""

    def __init__(self, theme: LogFormatTheme, time_formatter: LogTimeFormatter) -> None:
        """Initialize the formatter with theme and time helpers."""
        self._theme = theme
        self._time_formatter = time_formatter

    def format_event(self, event: str, level: str) -> Text:
        """Format a standard log event line."""
        timestamp = self._time_formatter.timestamp()
        color = self._theme.level_colors.get(level.lower(), "white")

        text = Text()
        text.append(f"[{timestamp}] ", style=self._theme.timestamp_style)
        text.append(f"[{level.upper():<8}] ", style=color)
        text.append(event)
        return text

    def format_matrix_lines(self, data: dict | str) -> list[Text | str]:
        """Format a Matrix-style JSON payload as multiple log lines."""
        if isinstance(data, dict):
            formatted = json.dumps(data, indent=2)
        else:
            formatted = str(data)

        timestamp = self._time_formatter.timestamp_ms()
        text = Text()
        text.append(
            f"[{timestamp}] ",
            style=self._theme.matrix_timestamp_style,
        )
        text.append("► ", style=self._theme.matrix_arrow_style)

        lines = formatted.split("\n")
        for index, line in enumerate(lines):
            if index > 0:
                text.append("\n")
                text.append(" " * 12)
            text.append(line, style=self._theme.matrix_line_style)

        return [text, ""]

    def format_separator(self, title: str = "") -> Text:
        """Format a separator line with an optional title."""
        if title:
            line = f"═══ {title} ".ljust(60, "═")
        else:
            line = "═" * 60
        return Text(line, style=self._theme.separator_style)
