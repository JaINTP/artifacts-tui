"""Mission entry formatting for character cards."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sentient_artifacts.tui.widgets.character_card.formatting.icons import (
    TaskIconResolver,
)
from sentient_artifacts.tui.widgets.character_card.formatting.normalization import (
    TextNormalizer,
)


class MissionFormatter:
    """Format mission entries for task list rendering."""

    def __init__(
        self,
        normalizer: TextNormalizer,
        icon_resolver: TaskIconResolver,
    ) -> None:
        """Store shared format helpers."""
        self._normalizer = normalizer
        self._icons = icon_resolver

    def format_mission(self, mission: Mapping[str, Any]) -> str:
        """Format a mission entry into a single display line."""
        task_type = self._extract_mission_type(mission).upper()
        args = mission.get("args", {}) or {}

        if task_type == "CRAFT":
            item = self._normalizer.humanize_code(
                args.get("item") or args.get("code") or mission.get("target")
            )
            qty = args.get("quantity") or mission.get("quantity") or 1
            icon = self._icons.task_icon_tag("craft", target=item)
            return f"{icon} Craft {item}{self._qty_suffix(qty)}"
        if task_type == "GATHER":
            skill = self._normalizer.humanize_code(
                args.get("skill") or mission.get("skill")
            )
            raw_resource = (
                args.get("resource")
                or args.get("target")
                or mission.get("resource")
                or mission.get("target")
            )
            resource = self._normalizer.humanize_code(raw_resource)
            qty = args.get("quantity") or mission.get("quantity")
            icon = self._icons.task_icon_tag(
                "gather",
                skill=args.get("skill") or mission.get("skill"),
                target=raw_resource,
            )
            base = f"{icon} Gather {resource}{self._qty_suffix(qty)}"
            return f"{base} ({skill})" if skill != "?" else base
        if task_type == "COMBAT":
            raw_target = (
                args.get("monster")
                or args.get("target")
                or mission.get("target")
            )
            target = self._normalizer.humanize_code(raw_target)
            qty = args.get("quantity") or mission.get("quantity")
            icon = self._icons.task_icon_tag("combat", target=raw_target)
            return f"{icon} Fight {target}{self._qty_suffix(qty)}"
        if task_type == "BANK_ROUTINE":
            return f"{self._icons.task_icon_tag('bank_routine')} Bank Run"
        if task_type == "EQUIP":
            item = self._normalizer.humanize_code(
                args.get("code") or args.get("item") or mission.get("target")
            )
            return f"{self._icons.task_icon_tag('equip', target=item)} Equip {item}"
        if task_type == "TASK_NEW":
            return f"{self._icons.task_icon_tag('task_new')} Get New Task"
        if task_type == "TASK_COMPLETE":
            return f"{self._icons.task_icon_tag('task_complete')} Complete Task"
        if task_type == "TASK_EXCHANGE":
            return f"{self._icons.task_icon_tag('task_exchange')} Exchange Task"
        if task_type == "REST":
            return f"{self._icons.task_icon_tag('rest')} Rest"
        if task_type in {"WAIT", "IDLE"}:
            return f"{self._icons.task_icon_tag('wait')} Wait"

        fallback_target = self._normalizer.humanize_code(
            args.get("target")
            or args.get("resource")
            or args.get("item")
            or args.get("monster")
            or mission.get("target")
        )
        if task_type == "UNKNOWN":
            if fallback_target != "?":
                return f"Mission: {fallback_target}"
            return "Mission"
        return (
            f"{self._icons.task_icon_tag(task_type.lower(), target=fallback_target)} "
            f"{self._normalizer.humanize_code(task_type.lower())}"
        )

    def _extract_mission_type(self, mission: Mapping[str, Any]) -> str:
        """Return the mission type token to drive formatting rules."""
        mission_type = (
            mission.get("task")
            or mission.get("type")
            or mission.get("action")
        )
        if mission_type:
            return str(mission_type)
        tool = mission.get("tool")
        if isinstance(tool, str) and tool.lower().startswith("mission:"):
            return tool.split(":", 1)[1].strip()
        return "unknown"

    def _qty_suffix(self, qty: Any) -> str:
        """Format optional quantity values for display."""
        return f" x{qty}" if qty not in (None, "", 0) else ""
