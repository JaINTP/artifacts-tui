"""Character card widget implementation."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Label, Static

from sentient_artifacts.tui.widgets.character_card.formatting import (
    DecisionFormatter,
    TaskIconResolver,
    TaskListFormatter,
    TextNormalizer,
)
from sentient_artifacts.tui.widgets.character_card.sprite import (
    SKINS_DIR,
    SpriteRenderer,
)
from sentient_artifacts.tui.widgets.character_card.stat_bar import ResponsiveStatBar

_TEXT_NORMALIZER = TextNormalizer()
_ICON_RESOLVER = TaskIconResolver(_TEXT_NORMALIZER)
_DECISION_FORMATTER = DecisionFormatter(_TEXT_NORMALIZER)
_SPRITE_RENDERER = SpriteRenderer(SKINS_DIR)


class CharacterCard(Static):
    """RPG-style card for a single character."""

    MAX_MISSION_ROWS_DISPLAY = 8
    MAX_ACTION_ROWS_DISPLAY = 12

    hp_percent = reactive(100)
    xp_percent = reactive(0)
    current_task = reactive("Initializing...")
    task_queue = reactive([])
    mission_queue = reactive([])
    last_msg = reactive("No signals.")
    cooldown_seconds = reactive(0)
    queue_eta_seconds = reactive(None)
    queue_eta_known_actions = reactive(0)
    queue_eta_total_actions = reactive(0)

    def __init__(
        self,
        character_name: str,
        skin_id: str = "men1",
        **kwargs: Any,
    ) -> None:
        """Initialize card state, helpers, and cached render fields."""
        super().__init__(**kwargs)
        self.character_name = character_name
        self.skin_id = self._normalize_skin_id(skin_id) or "men1"
        self.sprite_image: object | None = None
        self.sprite_stack: Horizontal | None = None
        self._last_hp_raw = ""
        self._last_xp_raw = ""
        self._last_decision_raw: Any = object()
        self._task_formatter = TaskListFormatter(
            _TEXT_NORMALIZER,
            _ICON_RESOLVER,
            max_mission_rows=self.MAX_MISSION_ROWS_DISPLAY,
            max_action_rows=self.MAX_ACTION_ROWS_DISPLAY,
        )
        self._decision_formatter = _DECISION_FORMATTER

    @staticmethod
    def _humanize_code(value: Any) -> str:
        """Convert machine-ish identifiers to readable labels."""
        return _TEXT_NORMALIZER.humanize_code(value)

    @staticmethod
    def _normalize_text(value: Any, fallback: str) -> str:
        """Normalize UI-bound text to avoid empty/whitespace fields."""
        return _TEXT_NORMALIZER.normalize_text(value, fallback)

    @classmethod
    def _normalize_goal_text(cls, value: Any, fallback: str = "Idle") -> str:
        """Normalize GOAL strings with the same style as task list entries."""
        return _TEXT_NORMALIZER.normalize_goal_text(value, fallback)

    @staticmethod
    def _compact_token(value: Any) -> str:
        """Normalize identifiers for lightweight task icon classification."""
        return _TEXT_NORMALIZER.compact_token(value)

    @classmethod
    def _gather_icon_tag(cls, skill: Any = None, target: Any = None) -> str:
        """Return an ASCII icon tag for gather tasks."""
        return _ICON_RESOLVER.gather_icon_tag(skill=skill, target=target)

    @classmethod
    def _craft_icon_tag(cls, target: Any = None) -> str:
        """Return an ASCII icon tag for crafting tasks."""
        return _ICON_RESOLVER.craft_icon_tag(target=target)

    @classmethod
    def _task_icon_tag(
        cls,
        action: str,
        *,
        skill: Any = None,
        target: Any = None,
    ) -> str:
        """Return an ASCII icon tag for a mission/task action."""
        return _ICON_RESOLVER.task_icon_tag(action, skill=skill, target=target)

    @classmethod
    def _local_skin_exists(cls, skin_id: str) -> bool:
        """Return True when a local sprite file exists for this skin id."""
        return _SPRITE_RENDERER.local_skin_exists(skin_id)

    @classmethod
    def _normalize_skin_id(cls, value: Any) -> str | None:
        """Normalize API skin payloads to local sprite IDs."""
        return _SPRITE_RENDERER.normalize_skin_id(value)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical(classes="card-body"):
            with Horizontal(classes="sprite-slot"):
                with Horizontal(
                    classes="sprite-stack",
                    id=f"sprite-stack-{self.character_name}",
                ) as sprite_stack:
                    self.sprite_stack = sprite_stack
                yield Label(self.character_name, classes="card-title-inline")

            self.hp_stat_label = Label("HP 100%", classes="stat-bar-label")
            yield self.hp_stat_label
            self.hp_bar = ResponsiveStatBar(
                fill_bg="#ff5b6d",
                empty_bg="#39151a",
                classes="hp-bar",
            )
            yield self.hp_bar

            self.xp_stat_label = Label("XP 0%", classes="stat-bar-label")
            yield self.xp_stat_label
            self.xp_bar = ResponsiveStatBar(
                fill_bg="#37d8ff",
                empty_bg="#0b2130",
                classes="xp-bar",
            )
            yield self.xp_bar

            yield Label("[bold red]COOLDOWN[/]")
            self.cooldown_label = Label("Ready", classes="cooldown-display")
            yield self.cooldown_label

            yield Label("[bold yellow]ACTION QUEUE[/]", classes="section-header")
            self.queue_eta_label = Label("ETA: -", classes="queue-eta")
            yield self.queue_eta_label
            with ScrollableContainer(classes="task-scroll-container"):
                self.task_list_display = Static(
                    "No actions queued.",
                    classes="task-list-content",
                )
                yield self.task_list_display

            yield Label("[bold cyan]SIGNAL[/]", classes="section-header")
            self.msg_label = Static(self.last_msg, classes="last-message")
            yield self.msg_label

            yield Label("[bold green]GOAL[/]", classes="section-header")
            self.task_label = Label(self.current_task, classes="current-task-bottom")
            yield self.task_label

    async def on_mount(self) -> None:
        """Initialize sprite and updates."""
        await self.load_sprite()

    async def load_sprite(self) -> None:
        """Render the character sprite from the local skins directory only."""
        self.sprite_image = _SPRITE_RENDERER.load_sprite(
            self.skin_id,
            self.app,
            stack=self.sprite_stack,
            stack_lookup=self._lookup_sprite_stack,
            current_image=self.sprite_image,
        )

    def _lookup_sprite_stack(self) -> Horizontal | None:
        """Resolve and cache the sprite stack container."""
        if self.sprite_stack is not None:
            return self.sprite_stack
        try:
            stack = self.query_one(f"#sprite-stack-{self.character_name}", Horizontal)
        except Exception:
            return None
        self.sprite_stack = stack
        return stack

    def watch_hp_percent(self, value: int) -> None:
        """Sync the HP bar and label when the reactive value changes."""
        if hasattr(self, "hp_bar"):
            self.hp_bar.percent = value
        if hasattr(self, "hp_stat_label"):
            self.hp_stat_label.update(f"HP {int(value)}%")

    def watch_xp_percent(self, value: int) -> None:
        """Sync the XP bar and label when the reactive value changes."""
        if hasattr(self, "xp_bar"):
            self.xp_bar.percent = value
        if hasattr(self, "xp_stat_label"):
            self.xp_stat_label.update(f"XP {int(value)}%")

    def watch_current_task(self, value: str) -> None:
        """Update the goal label when the current task changes."""
        if hasattr(self, "task_label"):
            normalized = self._normalize_goal_text(value, "Idle")
            self.task_label.update(Text(normalized))

    def watch_task_queue(self, value: list[dict[str, Any]]) -> None:
        """Task list rendering is coalesced in update_from_state."""
        return

    def watch_mission_queue(self, value: list[dict[str, Any]]) -> None:
        """Task list rendering is coalesced in update_from_state."""
        return

    def _update_task_list(self) -> None:
        """Render the combined task and mission list with grouping."""
        if not hasattr(self, "task_list_display"):
            return
        content = self._task_formatter.format(self.mission_queue, self.task_queue)
        self.task_list_display.update(content)

    def watch_last_msg(self, value: str) -> None:
        """Update the signal display when a new message arrives."""
        if hasattr(self, "msg_label"):
            self.msg_label.update(
                Text(self._normalize_text(value, "No recent events."))
            )

    def watch_cooldown_seconds(self, value: int) -> None:
        """Update the cooldown display when the timer changes."""
        if not hasattr(self, "cooldown_label"):
            return
        if value > 0:
            mins, secs = divmod(int(value), 60)
            if mins > 0:
                self.cooldown_label.update(f"⏰ {mins}m {secs}s")
            else:
                self.cooldown_label.update(f"⏰ {secs}s")
        else:
            self.cooldown_label.update("Ready")

    def _format_queue_eta(self, seconds: float | None, known: int, total: int) -> str:
        """Format queue ETA for display."""
        if not total:
            return "ETA: -"
        if seconds is None:
            return "ETA: ?"
        secs = int(round(float(seconds)))
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            eta = f"{hours}h {mins}m"
        elif mins > 0:
            eta = f"{mins}m {secs}s"
        else:
            eta = f"{secs}s"
        if known and known < total:
            eta = f"{eta} ({known}/{total})"
        return f"ETA: {eta}"

    def refresh_state(self) -> None:
        """Refresh state hooks for external callers.

        This method is reserved for app-level callers and can be overridden.
        """
        return

    def update_from_state(self, summary: dict[str, Any]) -> None:
        """Update reactive properties from a bot summary payload."""
        new_skin = self._normalize_skin_id(summary.get("skin"))
        if new_skin and new_skin != self.skin_id:
            self.skin_id = new_skin
            asyncio.create_task(self.load_sprite())

        hp_str = str(summary.get("hp", "100/100"))
        if hp_str != self._last_hp_raw:
            self._last_hp_raw = hp_str
            if "/" in hp_str:
                curr, total = (int(part) for part in hp_str.split("/", 1))
                self.hp_percent = int((curr / total) * 100) if total > 0 else 0

        xp_str = str(summary.get("xp", "0/1000"))
        if xp_str != self._last_xp_raw:
            self._last_xp_raw = xp_str
            if "/" in xp_str:
                curr, total = (int(part) for part in xp_str.split("/", 1))
                self.xp_percent = int((curr / total) * 100) if total > 0 else 0

        goal_task = self._normalize_goal_text(summary.get("goal_task"), "")
        current_task = self._normalize_goal_text(summary.get("current_task"), "")
        if goal_task:
            self.current_task = goal_task
        elif current_task:
            self.current_task = current_task
        elif not self._normalize_text(self.current_task, ""):
            self.current_task = "Idle"

        cooldown = summary.get("cooldown", 0)
        if cooldown != self.cooldown_seconds:
            self.cooldown_seconds = cooldown

        queue_eta_seconds = summary.get("queue_eta_seconds")
        queue_eta_known = int(summary.get("queue_eta_known_actions", 0) or 0)
        queue_eta_total = int(summary.get("queue_eta_total_actions", 0) or 0)
        if (
            queue_eta_seconds != self.queue_eta_seconds
            or queue_eta_known != self.queue_eta_known_actions
            or queue_eta_total != self.queue_eta_total_actions
        ):
            self.queue_eta_seconds = queue_eta_seconds
            self.queue_eta_known_actions = queue_eta_known
            self.queue_eta_total_actions = queue_eta_total
            if hasattr(self, "queue_eta_label"):
                self.queue_eta_label.update(
                    self._format_queue_eta(
                        queue_eta_seconds,
                        queue_eta_known,
                        queue_eta_total,
                    )
                )

        queue_changed = False
        task_queue = summary.get("task_queue", [])
        mission_queue = summary.get("mission_queue", [])
        if task_queue != self.task_queue:
            self.task_queue = task_queue
            queue_changed = True
        if mission_queue != self.mission_queue:
            self.mission_queue = mission_queue
            queue_changed = True
        if queue_changed:
            self._update_task_list()

        last_decision = summary.get("last_decision")
        if last_decision != self._last_decision_raw:
            self._last_decision_raw = last_decision
        else:
            last_decision = None

        if last_decision:
            try:
                if isinstance(last_decision, str):
                    decision_data = json.loads(last_decision)
                else:
                    decision_data = last_decision

                formatted = self._decision_formatter.format(decision_data)
                self.last_msg = self._normalize_text(formatted, self.last_msg)
            except (json.JSONDecodeError, TypeError):
                self.last_msg = self._normalize_text(
                    str(last_decision)[:100],
                    self.last_msg,
                )
        else:
            if not self._normalize_text(self.last_msg, ""):
                self.last_msg = "No recent events."
