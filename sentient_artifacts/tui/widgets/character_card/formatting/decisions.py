"""Decision signal formatting for character cards."""

from __future__ import annotations

from typing import Any

from sentient_artifacts.tui.widgets.character_card.formatting.normalization import (
    TextNormalizer,
)


class DecisionFormatter:
    """Format decision payloads into compact signal strings."""

    def __init__(self, normalizer: TextNormalizer) -> None:
        """Store the normalizer used for target formatting."""
        self._normalizer = normalizer

    def format(self, decision: Any) -> str:
        """Format a decision dictionary into a readable summary string."""
        if not isinstance(decision, dict):
            return str(decision)[:50]

        tool = decision.get("tool", "")
        if isinstance(tool, str) and tool.startswith("Mission:"):
            task = tool.replace("Mission:", "").strip()
            args = decision.get("args", {}) or {}
            skill = args.get("skill") or decision.get("skill", "")
            target = (
                args.get("monster")
                or args.get("resource")
                or args.get("item")
                or args.get("target")
                or decision.get("monster")
                or decision.get("target")
                or decision.get("resource", "")
            )
            qty = args.get("quantity") or decision.get("quantity")
        else:
            task = (
                decision.get("task")
                or decision.get("action")
                or decision.get("type", "Unknown")
            )
            skill = decision.get("skill")
            target = (
                decision.get("monster")
                or decision.get("target")
                or decision.get("resource")
                or decision.get("item")
                or decision.get("destination")
            )
            qty = decision.get("quantity")

        task = str(task).upper()
        parts: list[str] = [f"SIG {task}"]

        if skill:
            parts.append(f"({str(skill).title()})")
        if target:
            parts.append("->")
            target_display = self._normalizer.humanize_code(target)
            parts.append(target_display)
        if qty:
            parts.append(f"x{qty}")

        return " ".join(parts)
