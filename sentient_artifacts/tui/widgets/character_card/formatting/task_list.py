"""Task list rendering for character cards."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sentient_artifacts.tui.widgets.character_card.formatting.actions import (
    ActionFormatter,
)
from sentient_artifacts.tui.widgets.character_card.formatting.icons import (
    TaskIconResolver,
)
from sentient_artifacts.tui.widgets.character_card.formatting.missions import (
    MissionFormatter,
)
from sentient_artifacts.tui.widgets.character_card.formatting.normalization import (
    TextNormalizer,
)


class TaskListFormatter:
    """Render mission and task queues into a multiline display string."""

    def __init__(
        self,
        normalizer: TextNormalizer,
        icon_resolver: TaskIconResolver,
        *,
        max_mission_rows: int = 8,
        max_action_rows: int = 12,
    ) -> None:
        """Configure the formatter with helpers and row limits."""
        self._mission_formatter = MissionFormatter(normalizer, icon_resolver)
        self._action_formatter = ActionFormatter(normalizer, icon_resolver)
        self._max_mission_rows = max_mission_rows
        self._max_action_rows = max_action_rows

    def format(
        self,
        mission_queue: Sequence[Mapping[str, Any]],
        task_queue: Sequence[Mapping[str, Any]],
    ) -> str:
        """Format the current queues into a rich text payload."""
        lines: list[str] = []

        if mission_queue:
            lines.append("[bold magenta]MISSIONS:[/bold magenta]")
            visible_missions = mission_queue[: self._max_mission_rows]
            for idx, mission in enumerate(visible_missions, start=1):
                mission_line = self._mission_formatter.format_mission(mission)
                lines.append(f"  {idx}. {mission_line}")
            hidden_missions = max(0, len(mission_queue) - len(visible_missions))
            if hidden_missions:
                lines.append(f"  [dim]+{hidden_missions} more missions[/dim]")

        if task_queue:
            if lines:
                lines.append("")
            lines.append("[bold cyan]ACTIONS:[/bold cyan]")
            visible_tasks = task_queue[: self._max_action_rows]
            for idx, task in enumerate(visible_tasks, start=1):
                lines.append(f"  {idx}. {self._action_formatter.format_action(task)}")
            hidden_tasks = max(0, len(task_queue) - len(visible_tasks))
            if hidden_tasks:
                lines.append(f"  [dim]+{hidden_tasks} more actions[/dim]")

        if not lines:
            lines.append("[dim]No actions queued.[/dim]")

        return "\n".join(lines)
