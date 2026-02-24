"""Rendering helpers for the Matrix view widget."""

from __future__ import annotations

import json
from collections.abc import Iterable

from rich.panel import Panel
from rich.style import Style
from rich.syntax import Syntax

from sentient_artifacts.tui.widgets.matrix_view.entries import MatrixEntry


class MatrixRenderer:
    """Render Matrix view entries using Rich components."""

    def __init__(
        self,
        *,
        max_visible_entries: int = 50,
        theme: str = "monokai",
        background_color: str = "#000000",
        title: str = "[bright_green]◈ MATRIX MODE ◈[/bright_green]",
        border_color: str = "#00ff00",
    ) -> None:
        """Configure renderer appearance and entry limits."""
        self._max_visible_entries = max_visible_entries
        self._theme = theme
        self._background_color = background_color
        self._title = title
        self._border_color = border_color

    def render(self, entries: Iterable[MatrixEntry]) -> Panel:
        """Render entries into a Rich panel."""
        content = self._build_content(list(entries))
        syntax = Syntax(
            content,
            "json",
            theme=self._theme,
            background_color=self._background_color,
            line_numbers=False,
        )
        return Panel(
            syntax,
            title=self._title,
            border_style=Style(color=self._border_color),
            title_align="center",
        )

    def _build_content(self, entries: list[MatrixEntry]) -> str:
        """Build a JSON-like text block from entry data."""
        lines: list[str] = []
        for entry in entries[-self._max_visible_entries :]:
            lines.append(f"[{entry.display_timestamp()}] [{entry.source.upper()}]")
            json_str = json.dumps(entry.data, indent=2, default=str)
            lines.extend(json_str.split("\n"))
            lines.append("")
        if not lines:
            return ""
        return "\n".join(lines)
