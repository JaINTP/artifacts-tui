"""Matrix view entry models and storage utilities."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class MatrixEntry:
    """A single Matrix view entry."""

    timestamp: datetime
    source: str
    data: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        """Convert the entry into a JSON-serializable payload."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data,
        }

    def display_timestamp(self) -> str:
        """Format the timestamp for on-screen display."""
        return self.timestamp.strftime("%H:%M:%S")


class MatrixEntryStore:
    """Manage Matrix view entries with bounded history."""

    def __init__(self, max_entries: int = 100) -> None:
        """Initialize the store with a maximum entry count."""
        self._max_entries = max_entries
        self._entries: list[MatrixEntry] = []

    def add(self, data: dict[str, Any], source: str) -> MatrixEntry:
        """Add a new entry and return it."""
        entry = MatrixEntry(timestamp=datetime.now(), source=source, data=data)
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries :]
        return entry

    def clear(self) -> None:
        """Remove all entries from the store."""
        self._entries = []

    def entries(self) -> tuple[MatrixEntry, ...]:
        """Return a snapshot of all stored entries."""
        return tuple(self._entries)

    def recent(self, limit: int) -> Iterable[MatrixEntry]:
        """Return the most recent entries up to the provided limit."""
        if limit <= 0:
            return []
        return self._entries[-limit:]
