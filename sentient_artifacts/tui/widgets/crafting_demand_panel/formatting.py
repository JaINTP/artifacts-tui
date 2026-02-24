"""Formatting helpers for the crafting demand panel."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class CodeFormatter:
    """Format internal codes into display-friendly labels."""

    def humanize(self, value: Any) -> str:
        """Convert machine-oriented identifiers into human-friendly labels."""
        if value in (None, ""):
            return "?"
        text = str(value).strip().replace("_", " ").replace("-", " ")
        return " ".join(text.split()).title()


class ActorAnalytics:
    """Analyze actor mappings for display."""

    def primary_actor(self, mapping: Mapping[str, Any] | None, fallback: str) -> str:
        """Return the top-ranked actor name from a mapping."""
        if not isinstance(mapping, dict) or not mapping:
            return fallback
        ranked = sorted(
            ((str(name), int(qty or 0)) for name, qty in mapping.items()),
            key=lambda item: (-item[1], item[0]),
        )
        return ranked[0][0]

    def actor_preview(
        self,
        mapping: Mapping[str, Any] | None,
        *,
        fallback: str = "-",
        max_names: int = 2,
    ) -> str:
        """Return a compact preview of actor names from a mapping."""
        if not isinstance(mapping, dict) or not mapping:
            return fallback
        ranked = sorted(
            ((str(name), int(qty or 0)) for name, qty in mapping.items()),
            key=lambda item: (-item[1], item[0]),
        )
        names = [name for name, _ in ranked[:max_names]]
        extra = len(ranked) - max_names
        text = ", ".join(names)
        if extra > 0:
            text = f"{text} +{extra}"
        return text or fallback
