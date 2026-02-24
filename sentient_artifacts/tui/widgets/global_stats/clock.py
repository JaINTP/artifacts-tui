"""Time providers for the global stats widget."""

from __future__ import annotations

from datetime import datetime


class ServerTimeProvider:
    """Provide formatted server time values."""

    def __init__(self, *, time_format: str = "%Y-%m-%d %H:%M:%S") -> None:
        """Initialize the provider with a time format."""
        self._time_format = time_format

    def now(self) -> datetime:
        """Return the current timestamp."""
        return datetime.now()

    def formatted(self) -> str:
        """Return the current timestamp formatted for display."""
        return self.now().strftime(self._time_format)
