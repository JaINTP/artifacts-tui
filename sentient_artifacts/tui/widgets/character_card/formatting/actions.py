"""Action entry formatting for character cards."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sentient_artifacts.tui.widgets.character_card.formatting.icons import (
    TaskIconResolver,
)
from sentient_artifacts.tui.widgets.character_card.formatting.normalization import (
    TextNormalizer,
)


class ActionFormatter:
    """Format action entries for task list rendering."""

    def __init__(
        self,
        normalizer: TextNormalizer,
        icon_resolver: TaskIconResolver,
    ) -> None:
        """Store shared format helpers."""
        self._normalizer = normalizer
        self._icons = icon_resolver

    def format_action(self, task: Mapping[str, Any]) -> str:
        """Format a low-level task action into a single display line."""
        action = str(task.get("action", "unknown")).upper()
        raw_target = (
            task.get("code")
            or task.get("item")
            or task.get("monster")
            or task.get("resource")
            or task.get("target")
        )
        code = self._normalizer.humanize_code(raw_target)
        qty = task.get("quantity") or task.get("amount")

        if action == "MOVE":
            x, y = task.get("x", "?"), task.get("y", "?")
            return f"{self._icons.task_icon_tag('move')} Move to ({x}, {y})"
        if action == "GATHER":
            icon = self._icons.task_icon_tag(
                "gather",
                skill=task.get("skill"),
                target=raw_target,
            )
            return f"{icon} Gather {code}"
        if action == "CRAFT":
            icon = self._icons.task_icon_tag("craft", target=raw_target)
            return f"{icon} Craft {code} x{qty or 1}"
        if action == "FIGHT":
            icon = self._icons.task_icon_tag("fight", target=raw_target)
            return f"{icon} Fight {code}"
        if action == "REST":
            return f"{self._icons.task_icon_tag('rest')} Rest"
        if action == "DEPOSIT":
            return f"{self._icons.task_icon_tag('deposit')} Deposit {qty or 1}x {code}"
        if action == "WITHDRAW":
            icon = self._icons.task_icon_tag("withdraw")
            return f"{icon} Withdraw {qty or 1}x {code}"
        if action == "EQUIP":
            icon = self._icons.task_icon_tag("equip", target=raw_target)
            return f"{icon} Equip {code}"
        if action == "USE":
            icon = self._icons.task_icon_tag("use", target=raw_target)
            return f"{icon} Use {code} x{qty or 1}"
        return f"{self._icons.task_icon_tag(action, target=raw_target)} {action}"
