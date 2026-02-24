"""Official API Client for Artifacts MMO."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
import websockets

logger = logging.getLogger(__name__)


class BotProxy:
    """Lightweight proxy that presents a bot summary as a named object.

    Used by the TUI to display character state without requiring a full
    BotInstance from the bot manager.
    """
    
    def __init__(self, summary: dict[str, Any]) -> None:
        """Initialize a proxy with a bot summary payload."""
        self.summary = summary
        self.character_name = summary.get("name", "Unknown")
        
    def get_summary(self) -> dict[str, Any]:
        """Return the cached summary payload."""
        return self.summary


class OfficialApiClient:
    """A client that connects to the official Artifacts MMO API.
    
    This implements `BotManagerProtocol` to integrate natively with the TUI,
    providing view-only capabilities for characters on this token.
    """

    def __init__(self, token: str) -> None:
        """Initialize the official client with the user's game token."""
        self.token = token
        self.view_only = True
        self.base_url = "https://api.artifactsmmo.com"
        
        self._state_listeners: list[Any] = []
        self._log_listeners: list[Any] = []

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        self.client = httpx.Client(base_url=self.base_url, headers=headers, timeout=5.0)
        self._bot_cache: dict[str, dict[str, Any]] = {}
        self._swarm_demand_cache: dict[str, Any] = {
            "crafting_targets": {},
            "character_demands": {},
            "character_requests": {},
            "bounties": [],
        }

        self._ws_task: asyncio.Task[None] | None = None
        
    async def _ws_listener_loop(self) -> None:
        """Maintain a persistent WebSocket connection for real-time events.

        Authenticates with the official realtime API, parses incoming events
        into structured log messages, and updates the bot cache when an event
        carries character data.  Automatically reconnects on failure.
        """
        url = "wss://realtime.artifactsmmo.com/"
        while True:
            try:
                async with websockets.connect(url) as ws:
                    auth_payload = json.dumps({"token": self.token})
                    await ws.send(auth_payload)
                    
                    self._emit_log("System", "WebSocket connected to official servers.", "success")
                    
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            msg_type = data.get("type", "unknown")
                            content = data.get("data", data)
                            
                            char_name, log_msg, level = self._format_ws_event(
                                msg_type, content,
                            )
                            self._emit_log(char_name, log_msg, level)

                            if isinstance(content, dict):
                                char = content.get("character") or content.get("name")
                                if char and char in self._bot_cache:
                                    self._bot_cache[char]["last_decision"] = log_msg
                                    self._notify_state_listeners(char)
                                
                        except json.JSONDecodeError:
                            self._emit_log("System", f"WS raw: {message}", "info")
                            
            except Exception as e:
                self._emit_log("System", f"WS Disconnected: {e}. Reconnecting...", "error")
                await asyncio.sleep(5)

    def _format_ws_event(
        self, msg_type: str, content: Any,
    ) -> tuple[str, str, str]:
        """Convert a raw WebSocket event into a display-ready log entry.

        Args:
            msg_type: The event type string from the WebSocket message.
            content: The ``data`` payload from the WebSocket message.

        Returns:
            A ``(character_name, message, log_level)`` tuple ready for
            ``_emit_log``.
        """
        if not isinstance(content, dict):
            return ("System", f"[{msg_type}] {str(content)[:120]}", "info")

        char = content.get("character") or content.get("name") or "System"

        if msg_type == "grandexchange_neworder":
            code = content.get("code", "?")
            qty = content.get("quantity", 1)
            price = content.get("price", 0)
            seller = content.get("seller", "?")
            return ("System", f"📊 GE: {seller} listed {code} ×{qty} @ {price}g", "info")

        if msg_type == "grandexchange_sell":
            code = content.get("code", "?")
            qty = content.get("quantity", 1)
            price = content.get("price", 0)
            return (char, f"💰 GE: Sold {code} ×{qty} @ {price}g", "success")

        if msg_type == "my_grandexchange_sell":
            code = content.get("code", "?")
            qty = content.get("quantity", 1)
            price = content.get("price", 0)
            return (char, f"💰 YOUR GE: Sold {code} ×{qty} @ {price}g", "success")

        if msg_type == "achievement_unlocked":
            achievement = content.get("name", content.get("code", "?"))
            return (char, f"🏆 Achievement unlocked: {achievement}", "success")

        if msg_type == "event_spawn":
            code = content.get("code", content.get("name", "?"))
            pos = ""
            if content.get("x") is not None:
                pos = f" at ({content['x']},{content['y']})"
            return ("System", f"⚡ Event spawned: {code}{pos}", "warning")

        if msg_type == "event_removed":
            code = content.get("code", content.get("name", "?"))
            return ("System", f"🔚 Event ended: {code}", "info")

        desc = content.get("description", str(content)[:120])
        return (char, f"[{msg_type}] {desc}", "info")

    def _notify_state_listeners(self, character_name: str) -> None:
        """Push a cached summary to all registered state listeners.

        Args:
            character_name: Name of the character whose state changed.
        """
        summary = self._bot_cache.get(character_name)
        if not summary:
            return
        proxy = BotProxy(summary)
        for listener in self._state_listeners:
            try:
                listener(proxy)
            except Exception:
                pass

    def _emit_log(self, character_name: str, message: str, level: str) -> None:
        """Dispatch a log entry to all registered log listeners.

        Args:
            character_name: Originating character or ``'System'``.
            message: Human-readable log text.
            level: One of ``'info'``, ``'success'``, ``'warning'``, ``'error'``.
        """
        for listener in self._log_listeners:
            try:
                listener(character_name, message, level)
            except Exception:
                pass

    def start_background_tasks(self) -> None:
        """Start the WebSocket listener if an event loop is running."""
        if not self._ws_task:
            try:
                loop = asyncio.get_running_loop()
                self._ws_task = loop.create_task(self._ws_listener_loop())
            except RuntimeError:
                pass

    def get_shared_state(self) -> dict[str, Any]:
        """Return aggregated swarm state for the TUI global stats widget."""
        return {
            "status": "Official API Mode",
            "aggregate": {},
            "bots": list(self._bot_cache.values())
        }

    def execute_command(self, command: str, target_bot: str = "all") -> str:
        """Return an error string; commands are unavailable in view-only mode."""
        return "Error: Read-only mode. TUI commands are disabled when using the official API directly."

    def rest_all(self) -> None:
        """No-op; rest commands are unavailable in view-only mode."""

    def add_state_listener(self, callback: Any) -> None:
        """Register a callback invoked on character state changes."""
        self._state_listeners.append(callback)

    def remove_state_listener(self, callback: Any) -> None:
        """Unregister a previously added state listener."""
        if callback in self._state_listeners:
            self._state_listeners.remove(callback)

    def add_log_listener(self, callback: Any) -> None:
        """Register a callback invoked on each log event.

        Also starts the WebSocket listener if not already running, since
        the TUI registers log listeners during mount.
        """
        self._log_listeners.append(callback)
        if not self._ws_task:
            self.start_background_tasks()

    def remove_log_listener(self, callback: Any) -> None:
        """Unregister a previously added log listener."""
        if callback in self._log_listeners:
            self._log_listeners.remove(callback)
            
    def poll_logs(self) -> None:
        """No-op; logs arrive asynchronously via the WebSocket listener."""
        
    @staticmethod
    def _derive_goal_task(char: dict[str, Any]) -> str:
        """Derive a human-readable goal string from character task fields.

        Combines ``task``, ``task_type``, and progress counters into a label
        such as ``"Monsters: Kill Chickens (3/10)"``.

        Args:
            char: A character dict from the official ``/my/characters`` API.

        Returns:
            A formatted goal string, or ``'Idle'`` / ``'On cooldown'`` when
            no active task is present.
        """
        task = char.get("task", "") or ""
        task_type = char.get("task_type", "") or ""
        task_progress = char.get("task_progress", 0) or 0
        task_total = char.get("task_total", 0) or 0

        if not task:
            # Infer from position or cooldown
            cd = char.get("cooldown", 0) or 0
            if cd > 0:
                return "On cooldown"
            return "Idle"

        label = task.replace("_", " ").title()
        if task_type:
            label = f"{task_type.title()}: {label}"
        if task_total > 0:
            label += f" ({task_progress}/{task_total})"
        return label

    @staticmethod
    def _compute_cooldown(char: dict[str, Any]) -> int:
        """Compute remaining cooldown seconds from the expiration timestamp.

        Parses ``cooldown_expiration`` (ISO 8601) and calculates the delta
        against the current UTC time.  Falls back to the raw ``cooldown``
        integer field if the timestamp is absent or unparseable.

        Args:
            char: A character dict from the official ``/my/characters`` API.

        Returns:
            Non-negative integer of remaining cooldown seconds.
        """
        expiration = char.get("cooldown_expiration")
        if expiration:
            try:
                exp_str = str(expiration)
                if exp_str.endswith("Z"):
                    exp_str = exp_str[:-1] + "+00:00"
                exp_dt = datetime.fromisoformat(exp_str)
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                remaining = (exp_dt - datetime.now(timezone.utc)).total_seconds()
                return max(0, int(remaining))
            except (ValueError, TypeError):
                pass
        return int(char.get("cooldown", 0) or 0)

    def get_all_summaries(self) -> list[dict[str, Any]]:
        """Fetch all characters and map them to TUI-compatible summaries.

        Queries ``/my/characters`` and transforms each ``CharacterSchema``
        into the summary dict format expected by ``CharacterCard.update_from_state``.
        Preserves WebSocket-derived signal text across polls when available.

        Returns:
            A list of summary dicts, one per character.  Falls back to the
            cached values on API errors.
        """
        try:
            response = self.client.get("/my/characters")
            response.raise_for_status()
            characters = response.json().get("data", [])
            
            mapped_summaries = []
            for char in characters:
                name = char.get("name", "Unknown")
                hp = char.get("hp", 0)
                max_hp = char.get("max_hp", 0)
                xp = char.get("xp", 0)
                max_xp = char.get("max_xp", 0)
                level = char.get("level", 1)
                gold = char.get("gold", 0)
                x = char.get("x", 0)
                y = char.get("y", 0)
                
                existing_cache = self._bot_cache.get(name, {})
                
                goal_task = self._derive_goal_task(char)
                current_task = char.get("task", "") or "Idle"
                
                ws_signal = existing_cache.get("last_decision")
                if isinstance(ws_signal, str) and ws_signal.strip():
                    signal = ws_signal
                else:
                    signal = f"Lv.{level} · 💰{gold}g · 📍({x},{y}) · ❤️{hp}/{max_hp}"
                
                summary = {
                    "name": name,
                    "skin": char.get("skin", "men1"),
                    "hp": f"{hp}/{max_hp}",
                    "xp": f"{xp}/{max_xp}",
                    "level": level,
                    "gold": gold,
                    "position": f"({x},{y})",
                    "goal_task": goal_task,
                    "current_task": current_task,
                    "cooldown": self._compute_cooldown(char),
                    "last_decision": signal,
                    "task_queue": [],
                    "mission_queue": [],
                    "queue_eta_seconds": None,
                    "queue_eta_known_actions": 0,
                    "queue_eta_total_actions": 0,
                }
                self._bot_cache[name] = summary
                mapped_summaries.append(summary)
                
            return mapped_summaries
        except Exception as e:
            self._emit_log("System", f"API Error: {e}", "error")
            return list(self._bot_cache.values())

    def get_swarm_demand_snapshot(self) -> dict[str, Any]:
        """Return an empty demand snapshot; unavailable in view-only mode."""
        return self._swarm_demand_cache

    def get_bot(self, name: str) -> BotProxy | None:
        """Return a ``BotProxy`` for the named character, or ``None``.

        Triggers a summary refresh if the character is not yet cached.
        """
        summary = self._bot_cache.get(name)
        if not summary:
            try:
                self.get_all_summaries()
                summary = self._bot_cache.get(name)
            except Exception:
                pass
        
        if summary:
            return BotProxy(summary)
        return None

    @property
    def roster(self) -> None:
        """Return ``None``; roster introspection is unavailable in view-only mode."""
        return None
