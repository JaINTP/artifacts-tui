"""Textual application entry point for the dashboard TUI."""

from __future__ import annotations

import asyncio
import math
from typing import Any, Protocol

from textual.app import App, ComposeResult
from textual.containers import Container, Grid
from textual.theme import Theme
from textual.widgets import Footer, Header
from sentient_artifacts.tui.widgets.character_card import CharacterCard
from sentient_artifacts.tui.widgets.crafting_demand_panel import CraftingDemandPanel
from sentient_artifacts.tui.widgets.log_console import LogConsole


class BotManagerProtocol(Protocol):
    """Protocol defining bot manager behavior expected by the TUI."""

    def get_shared_state(self) -> dict[str, Any]:
        """Return the shared state snapshot."""
        ...

    def execute_command(self, command: str, target_bot: str = "all") -> str:
        """Execute a command on a bot or the entire swarm."""
        ...

    def rest_all(self) -> None:
        """Trigger a rest-all action."""
        ...

    def add_state_listener(self, callback: Any) -> None:
        """Register a state listener callback."""
        ...

    def remove_state_listener(self, callback: Any) -> None:
        """Remove a state listener callback."""
        ...

    def add_log_listener(self, callback: Any) -> None:
        """Register a log listener callback."""
        ...

    def remove_log_listener(self, callback: Any) -> None:
        """Remove a log listener callback."""
        ...

    def get_all_summaries(self) -> list[dict[str, Any]]:
        """Return summaries for all bots."""
        ...

    def get_swarm_demand_snapshot(self) -> dict[str, Any]:
        """Return the current swarm demand snapshot."""
        ...

class TUI(App):
    """TUI Dashboard for the Artifacts MMORPG bot swarm."""

    CSS_PATH = "app.css"
    CUSTOM_THEME_NAME = "artifacts-dark"
    DEFAULT_THEME_NAME = "textual-dark"
    LAYOUT_MODES = (
        ("auto", "Auto (Responsive)"),
        ("balanced", "Balanced 3-Column"),
        ("dense", "Dense 5-Column"),
        ("focus", "Focus 2-Column"),
    )
    LAYOUT_GRIDS = {
        "balanced": (3, 2),
        "dense": (5, 1),
        "focus": (2, 3),
    }
    GRID_GUTTER = 1
    CARD_MIN_WIDTH = 32
    CARD_MIN_HEIGHT = 27
    BINDINGS = [
        ("T", "toggle_dark_theme", "Toggle Dark Theme"),
        ("t", "cycle_theme", "Cycle Theme"),
        ("L", "toggle_log", "Toggle Log"),
        ("D", "toggle_demand", "Toggle Demand"),
        ("M", "cycle_layout", "Cycle layout"),
        ("h", "log_narrower", "Demand Wider"),
        ("l", "log_wider", "Log Wider"),
        ("=", "reset_log_split", "Reset Split"),
        ("j", "panels_shorter", "Panels Shorter"),
        ("k", "panels_taller", "Panels Taller"),
        ("0", "reset_panel_height", "Reset Panel Height"),
        ("q", "quit", "Quit"),
    ]
    STATE_POLL_INTERVAL = 1.0
    DEMAND_POLL_INTERVAL = 2.0
    LOG_POLL_INTERVAL = 0.75

    def __init__(self, bot_manager: BotManagerProtocol | None = None, **kwargs):
        """Initialize the TUI with an optional bot manager."""
        super().__init__(**kwargs)
        self.bot_manager = bot_manager
        self.cards: list[CharacterCard] = []
        self.cards_by_name: dict[str, CharacterCard] = {}
        self.default_names = [
            "Atlas_Core",
            "Ignis_Prime",
            "Aqua_Flow",
            "Viper_Mix",
            "Baker_Street",
        ]
        self.default_skins = ["men1", "men2", "women1", "men3", "women2"]
        # Start in responsive mode for better scaling.
        self.layout_mode_index = 0
        self._state_poll_inflight = False
        self._logs_poll_inflight = False
        self._demand_poll_inflight = False
        self._split_total_units = 8
        self._split_min_units = 1
        self._log_width_units = 3
        self._default_log_width_units = self._log_width_units
        self._bottom_base_heights = {
            "auto": 30,
            "dense": 30,
            "balanced": 30,
            "focus": 12,
        }
        self._bottom_min_height = 6
        self._bottom_height_override: int | None = None
        self._log_visible = True
        self._demand_visible = True
        self._register_custom_themes()
        self.theme = self.CUSTOM_THEME_NAME

    def _register_custom_themes(self) -> None:
        """Register project-specific theme alongside Textual defaults."""
        if self.CUSTOM_THEME_NAME in self.available_themes:
            return

        self.register_theme(
            Theme(
                name=self.CUSTOM_THEME_NAME,
                primary="#2ad56b",
                secondary="#37d8ff",
                warning="#ffe869",
                error="#ff5b6d",
                success="#47f08f",
                accent="#ff74f2",
                foreground="#d8ffe5",
                background="#06080a",
                surface="#0f1318",
                panel="#0b1014",
                boost="#23cc61",
                dark=True,
                luminosity_spread=0.18,
                text_alpha=0.96,
            )
        )

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)
        
        # Determine actual names if manager is available
        names = self.default_names
        skins = self.default_skins
        
        if self.bot_manager and getattr(self.bot_manager, "roster", None):
            roster_names = [c.name for c in self.bot_manager.roster.get_all_characters()]
            if roster_names:
                names = roster_names[:5]

        with Container(id="main-container"):
            with Grid(id="top-section"):
                for i in range(len(names)):
                    card = CharacterCard(
                        character_name=names[i],
                        skin_id=skins[i] if i < len(skins) else "men1",
                        id=f"card-{i}",
                    )
                    self.cards.append(card)
                    self.cards_by_name[names[i]] = card
                    yield card
            
            with Container(id="bottom-section"):
                yield LogConsole(id="system-log")
                yield CraftingDemandPanel(id="demand-panel")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize simulation and listeners."""
        self.log_widget = self.query_one(LogConsole)
        self.demand_widget = self.query_one(CraftingDemandPanel)
        self.top_section = self.query_one("#top-section", Grid)
        self.bottom_section = self.query_one("#bottom-section", Container)
        self._apply_layout_mode(notify=False)
        self._apply_bottom_split()
        self._apply_log_visibility()
        self._apply_demand_visibility()
        self._apply_bottom_visibility()
        self._apply_bottom_height()
        
        # Start state polling (fallback for sparse events)
        self.set_interval(self.STATE_POLL_INTERVAL, self.poll_bot_states)
        self.set_interval(self.DEMAND_POLL_INTERVAL, self.poll_swarm_demand)
        
        # Start log polling for client mode (server mode uses direct listener)
        if hasattr(self.bot_manager, 'poll_logs'):
            self.set_interval(self.LOG_POLL_INTERVAL, self.poll_logs)
        
        self.log_widget.log_event("SYSTEM INITIALIZED. SCANNING SWARM...", "info")
        self.log_widget.log_event("DASHBOARD V6.0.0 ACTIVE.", "info")
        self.log_widget.log_event(f"THEME ACTIVE: {self.theme}", "info")

        if self.bot_manager:
            self.bot_manager.add_log_listener(self.on_bot_log)
            self.bot_manager.add_state_listener(self.on_bot_state)
            self.log_widget.log_event("CONNECTED TO BOT MANAGER. SYNCING...", "success")

    def _is_remote_client_mode(self) -> bool:
        """True when manager is HTTP client backed (blocking network calls)."""
        return bool(self.bot_manager and hasattr(self.bot_manager, "client") and hasattr(self.bot_manager, "base_url"))

    async def poll_bot_states(self) -> None:
        """Force a state refresh from the manager."""
        if not self.bot_manager or self._state_poll_inflight:
            return
        self._state_poll_inflight = True
        try:
            # If manager provides absolute summaries, use them
            if self._is_remote_client_mode():
                summaries = await asyncio.to_thread(self.bot_manager.get_all_summaries)
            else:
                summaries = self.bot_manager.get_all_summaries()

            for summary in summaries:
                name = summary.get("name")
                card = self.cards_by_name.get(str(name))
                if card is not None:
                    card.update_from_state(summary)
        except Exception:
            pass
        finally:
            self._state_poll_inflight = False

    async def poll_logs(self) -> None:
        """Poll logs from the server (client mode only)."""
        if (
            not self.bot_manager
            or not hasattr(self.bot_manager, 'poll_logs')
            or self._logs_poll_inflight
        ):
            return
        self._logs_poll_inflight = True
        try:
            if self._is_remote_client_mode():
                await asyncio.to_thread(self.bot_manager.poll_logs)
            else:
                self.bot_manager.poll_logs()
        except Exception:
            pass  # Silently ignore polling errors
        finally:
            self._logs_poll_inflight = False

    def poll_swarm_demand(self) -> None:
        """Refresh bottom-right crafting demand panel from API snapshot."""
        if self._demand_poll_inflight:
            return
        self._demand_poll_inflight = True

        def _apply_snapshot(snapshot: object) -> None:
            """Apply a snapshot when available."""
            if isinstance(snapshot, dict):
                self.demand_widget.update_from_snapshot(snapshot)

        if not self.bot_manager or not hasattr(self.bot_manager, "get_swarm_demand_snapshot"):
            self._demand_poll_inflight = False
            return

        if self._is_remote_client_mode():
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                try:
                    snapshot = self.bot_manager.get_swarm_demand_snapshot()
                    _apply_snapshot(snapshot)
                except Exception:
                    pass
                finally:
                    self._demand_poll_inflight = False
                return

            async def _poll_remote() -> None:
                try:
                    snapshot = await asyncio.to_thread(
                        self.bot_manager.get_swarm_demand_snapshot
                    )
                    _apply_snapshot(snapshot)
                except Exception:
                    pass
                finally:
                    self._demand_poll_inflight = False

            loop.create_task(_poll_remote())
            return

        try:
            snapshot = self.bot_manager.get_swarm_demand_snapshot()
            _apply_snapshot(snapshot)
        except Exception:
            pass
        finally:
            self._demand_poll_inflight = False

    def on_bot_log(self, character_name: str, message: str, level: str) -> None:
        """Handle real log events."""
        if not hasattr(self, "log_widget") or self.log_widget is None:
            return
        self.log_widget.log_event(f"[{character_name}] {message}", level)
        clean_message = str(message or "").strip()
        for card in self.cards:
            if card.character_name == character_name:
                if clean_message:
                    card.last_msg = clean_message
                break

    def on_bot_state(self, bot: Any) -> None:
        """Handle real state changes."""
        # Find matching card and update
        summary = bot.get_summary()
        card = self.cards_by_name.get(str(bot.character_name))
        if card is not None:
            card.update_from_state(summary)

    def action_toggle_log(self) -> None:
        """Toggle the visibility of the log console."""
        self._log_visible = not self._log_visible
        self._apply_log_visibility()
        self._apply_bottom_visibility()
        self._apply_bottom_split()
        self._apply_bottom_height()
        if self._current_layout_key() == "auto":
            self._apply_responsive_grid()

    def action_toggle_demand(self) -> None:
        """Toggle the visibility of the demand panel."""
        self._demand_visible = not self._demand_visible
        self._apply_demand_visibility()
        self._apply_bottom_visibility()
        self._apply_bottom_split()
        self._apply_bottom_height()
        if self._current_layout_key() == "auto":
            self._apply_responsive_grid()

    def action_toggle_dark_theme(self) -> None:
        """Toggle between Textual default dark and project dark theme."""
        self.theme = (
            self.DEFAULT_THEME_NAME
            if self.theme == self.CUSTOM_THEME_NAME
            else self.CUSTOM_THEME_NAME
        )
        if hasattr(self, "log_widget"):
            self.log_widget.log_event(f"Theme switched to {self.theme}", "info")

    def action_cycle_theme(self) -> None:
        """Cycle through all available registered themes."""
        names = sorted(self.available_themes.keys())
        if not names:
            return
        try:
            idx = names.index(self.theme)
        except ValueError:
            idx = -1
        self.theme = names[(idx + 1) % len(names)]
        if hasattr(self, "log_widget"):
            self.log_widget.log_event(f"Theme switched to {self.theme}", "info")

    def action_cycle_layout(self) -> None:
        """Cycle between readability-focused dashboard layouts."""
        self.layout_mode_index = (self.layout_mode_index + 1) % len(self.LAYOUT_MODES)
        self._apply_layout_mode()

    def _current_layout_key(self) -> str:
        """Return the active layout key."""
        return self.LAYOUT_MODES[self.layout_mode_index][0]

    def _apply_layout_mode(self, notify: bool = True) -> None:
        """Apply CSS classes for the selected layout mode."""
        if not hasattr(self, "top_section") or not hasattr(self, "bottom_section"):
            return

        for cls in ("layout-dense", "layout-balanced", "layout-focus"):
            self.top_section.remove_class(cls)
            self.bottom_section.remove_class(cls)

        mode_key, mode_label = self.LAYOUT_MODES[self.layout_mode_index]
        if mode_key != "auto":
            css_class = f"layout-{mode_key}"
            self.top_section.add_class(css_class)
            self.bottom_section.add_class(css_class)

        if mode_key == "auto":
            self._apply_responsive_grid()
        else:
            cols, rows = self.LAYOUT_GRIDS.get(mode_key, (3, 2))
            self._set_top_grid(cols, rows)

        if notify and hasattr(self, "log_widget"):
            self.log_widget.log_event(f"Layout switched to {mode_label}", "info")
        self._apply_bottom_height()

    def _set_top_grid(self, columns: int, rows: int) -> None:
        """Set the top grid template explicitly."""
        columns = max(1, int(columns))
        rows = max(1, int(rows))
        self._grid_columns = columns
        self._grid_rows = rows
        self.top_section.styles.grid_columns = " ".join(["1fr"] * columns)
        self.top_section.styles.grid_rows = " ".join(["1fr"] * rows)
        if hasattr(self.top_section.styles, "grid_size"):
            self.top_section.styles.grid_size = (columns, rows)

    def _apply_responsive_grid(self) -> None:
        """Compute a grid that best fits the available space."""
        if not hasattr(self, "top_section"):
            return
        card_count = max(1, len(self.cards))
        width = int(getattr(self.top_section.size, "width", 0) or 0)
        height = int(getattr(self.top_section.size, "height", 0) or 0)
        if width <= 0 or height <= 0:
            return

        gutter = self.GRID_GUTTER
        min_width = self.CARD_MIN_WIDTH
        min_height = self.CARD_MIN_HEIGHT

        max_cols_by_width = max(
            1,
            min(
                card_count,
                (width + gutter) // (min_width + gutter),
            ),
        )
        max_rows_by_height = max(
            1,
            (height + gutter) // (min_height + gutter),
        )
        min_cols_by_height = max(1, math.ceil(card_count / max_rows_by_height))

        columns = max(min_cols_by_height, 1)
        if columns > max_cols_by_width:
            columns = max_cols_by_width
        rows = max(1, math.ceil(card_count / columns))
        self._set_top_grid(columns, rows)

    def _apply_bottom_split(self) -> None:
        """Apply width ratios for the log and demand panels."""
        if not hasattr(self, "log_widget") or not hasattr(self, "demand_widget"):
            return
        if not self._log_visible and not self._demand_visible:
            self.log_widget.styles.width = "0fr"
            self.demand_widget.styles.width = "0fr"
            return
        if not self._log_visible:
            self.log_widget.styles.width = "0fr"
            self.demand_widget.styles.width = "1fr"
            return
        if not self._demand_visible:
            self.log_widget.styles.width = "1fr"
            self.demand_widget.styles.width = "0fr"
            return
        max_log = self._split_total_units - self._split_min_units
        self._log_width_units = max(
            self._split_min_units, min(self._log_width_units, max_log)
        )
        demand_units = self._split_total_units - self._log_width_units
        self.log_widget.styles.width = f"{self._log_width_units}fr"
        self.demand_widget.styles.width = f"{demand_units}fr"

    def _current_bottom_base_height(self) -> int:
        """Get the default bottom-section height for the active layout."""
        return self._bottom_base_heights.get(self._current_layout_key(), 30)

    def _max_bottom_height(self) -> int | None:
        """Compute a reasonable maximum based on available screen height."""
        total_height = int(getattr(self.size, "height", 0) or 0)
        if total_height <= 0:
            return None
        reserved = 6  # Header/footer plus minimal breathing room.
        return max(self._bottom_min_height, total_height - reserved)

    def _apply_bottom_height(self) -> None:
        """Apply the height for the log/demand panel container."""
        if not hasattr(self, "bottom_section"):
            return
        base_height = self._current_bottom_base_height()
        height = (
            base_height
            if self._bottom_height_override is None
            else self._bottom_height_override
        )
        height = max(self._bottom_min_height, height)
        max_height = self._max_bottom_height()
        if max_height is not None:
            height = min(height, max_height)
        self.bottom_section.styles.height = height
        if self._bottom_height_override is not None:
            self._bottom_height_override = height

    def _apply_log_visibility(self) -> None:
        """Show or hide the log widget without collapsing the demand panel."""
        if not hasattr(self, "log_widget"):
            return
        if self._log_visible:
            self.log_widget.remove_class("hidden")
        else:
            self.log_widget.add_class("hidden")

    def _apply_demand_visibility(self) -> None:
        """Show or hide the demand panel without collapsing the log."""
        if not hasattr(self, "demand_widget"):
            return
        if self._demand_visible:
            self.demand_widget.remove_class("hidden")
        else:
            self.demand_widget.add_class("hidden")

    def _apply_bottom_visibility(self) -> None:
        """Hide the entire bottom section when no panels are visible."""
        if not hasattr(self, "bottom_section"):
            return
        if self._log_visible or self._demand_visible:
            self.bottom_section.remove_class("hidden")
        else:
            self.bottom_section.add_class("hidden")

    def action_log_wider(self) -> None:
        """Increase log panel width and shrink demand panel."""
        max_log = self._split_total_units - self._split_min_units
        if self._log_width_units >= max_log:
            return
        self._log_width_units += 1
        self._apply_bottom_split()

    def action_log_narrower(self) -> None:
        """Decrease log panel width and widen demand panel."""
        if self._log_width_units <= self._split_min_units:
            return
        self._log_width_units -= 1
        self._apply_bottom_split()

    def action_reset_log_split(self) -> None:
        """Reset the log/demand split to the default ratio."""
        self._log_width_units = self._default_log_width_units
        self._apply_bottom_split()

    def action_panels_taller(self) -> None:
        """Increase the bottom panel height."""
        base_height = self._current_bottom_base_height()
        current = (
            base_height
            if self._bottom_height_override is None
            else self._bottom_height_override
        )
        self._bottom_height_override = current + 1
        self._apply_bottom_height()

    def action_panels_shorter(self) -> None:
        """Decrease the bottom panel height."""
        base_height = self._current_bottom_base_height()
        current = (
            base_height
            if self._bottom_height_override is None
            else self._bottom_height_override
        )
        self._bottom_height_override = current - 1
        self._apply_bottom_height()

    def action_reset_panel_height(self) -> None:
        """Reset the bottom panel height to the layout default."""
        self._bottom_height_override = None
        self._apply_bottom_height()

    def on_resize(self) -> None:
        """Keep height constraints sensible on terminal resize."""
        self._apply_bottom_height()
        if self._current_layout_key() == "auto":
            self._apply_responsive_grid()

if __name__ == "__main__":
    app = TUI()
    app.run()
