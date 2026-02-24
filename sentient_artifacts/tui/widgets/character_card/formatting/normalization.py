"""Text normalization helpers for character card formatting."""

from __future__ import annotations

import re
from typing import Any

_MISSION_PATTERN = re.compile(r"mission:\s*([a-z0-9_-]+)", re.IGNORECASE)
_CODE_PATTERN = re.compile(r"[a-z0-9_-]+", re.IGNORECASE)


class TextNormalizer:
    """Normalize machine-oriented strings into user-facing labels."""

    def humanize_code(self, value: Any) -> str:
        """Convert machine-ish identifiers to readable labels."""
        if value in (None, ""):
            return "?"
        text = str(value).strip().replace("_", " ").replace("-", " ")
        text = " ".join(text.split())
        return text.title()

    def normalize_text(self, value: Any, fallback: str) -> str:
        """Normalize UI-bound text to avoid empty/whitespace fields."""
        if value is None:
            return fallback
        text = str(value).strip()
        return text if text else fallback

    def normalize_goal_text(self, value: Any, fallback: str = "Idle") -> str:
        """Normalize GOAL strings with the same style as task list entries."""
        text = self.normalize_text(value, "")
        if not text:
            return fallback

        mission_match = _MISSION_PATTERN.fullmatch(text)
        if mission_match:
            return f"Mission: {self.humanize_code(mission_match.group(1))}"

        if _CODE_PATTERN.fullmatch(text):
            return self.humanize_code(text)

        return text

    def compact_token(self, value: Any) -> str:
        """Normalize identifiers for lightweight task icon classification."""
        if value in (None, ""):
            return ""
        return "".join(ch for ch in str(value).lower() if ch.isalnum())
