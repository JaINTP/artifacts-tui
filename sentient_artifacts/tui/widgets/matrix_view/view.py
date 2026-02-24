"""Matrix view widget for displaying raw JSON decision streams."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Label, Static

from sentient_artifacts.tui.widgets.matrix_view.entries import (
    MatrixEntry,
    MatrixEntryStore,
)
from sentient_artifacts.tui.widgets.matrix_view.rendering import MatrixRenderer


class MatrixView(Static):
    """A widget displaying raw JSON data in Matrix-style formatting."""

    DEFAULT_CSS = """
    MatrixView {
        width: 1fr;
        height: 1fr;
        background: #000000;
        color: #00ff00;
        padding: 1;
        overflow: auto scroll;
    }
    MatrixView > .matrix-line {
        color: #00ff00;
        text-style: dim;
    }
    MatrixView > .matrix-timestamp {
        color: #008800;
        text-style: dim;
    }
    MatrixView > .matrix-highlight {
        color: #00ff00;
        text-style: bold;
    }
    """

    entries: reactive[list[MatrixEntry]] = reactive(list)

    def __init__(self, *, max_entries: int = 100, **kwargs: Any) -> None:
        """Initialize the matrix view widget."""
        super().__init__(**kwargs)
        self._store = MatrixEntryStore(max_entries=max_entries)
        self._renderer = MatrixRenderer()
        self.entries = []

    def compose(self) -> ComposeResult:
        """Compose the matrix view layout."""
        yield Label("MATRIX MODE - RAW JSON STREAM", classes="matrix-header")

    def add_entry(self, data: dict[str, Any], source: str = "system") -> None:
        """Add a new JSON entry to the matrix view."""
        self._store.add(data, source)
        self.entries = list(self._store.entries())

    def _render_entries(self) -> None:
        """Render all entries to the display."""
        panel = self._renderer.render(self._store.recent(50))
        self.update(panel)

    def watch_entries(self, entries: list[MatrixEntry]) -> None:
        """React to entries changes."""
        self._render_entries()

    def clear(self) -> None:
        """Clear all entries."""
        self._store.clear()
        self.entries = []
        self.update("")

    def add_decision(self, decision: dict[str, Any], character_name: str = "") -> None:
        """Add a decision entry with character context."""
        entry_data = {
            "type": "decision",
            "character": character_name,
            "decision": decision,
        }
        self.add_entry(entry_data, source="system")

    def add_api_response(self, endpoint: str, response: dict[str, Any]) -> None:
        """Add an API response entry."""
        entry_data = {
            "type": "api_response",
            "endpoint": endpoint,
            "response": response,
        }
        self.add_entry(entry_data, source="api")
