"""Official API Client for Artifacts MMO."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx
import websockets

logger = logging.getLogger(__name__)


class BotProxy:
    """A proxy class that mimics BotInstance for the TUI."""
    
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
        self.base_url = "https://api.artifactsmmo.com"
        
        self._state_listeners: list[Any] = []
        self._log_listeners: list[Any] = []
        
        # HTTP Client configuration
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

        # Background tasks
        self._ws_task: asyncio.Task[None] | None = None
        
    async def _ws_listener_loop(self) -> None:
        """Background loop to listen for websocket events."""
        url = "wss://realtime.artifactsmmo.com/"
        while True:
            try:
                # Need to use token as query parameter or subprotocol per some websockets, 
                # but based on search: "To connect, users must send a token in their initial message."
                async with websockets.connect(url) as ws:
                    # Authenticate
                    auth_message = f"{self.token}"
                    await ws.send(auth_message)
                    
                    self._emit_log("System", "WebSocket connected to official servers.", "success")
                    
                    async for message in ws:
                        try:
                            # Attempt to parse json
                            data = json.loads(message)
                            
                            # Extremely simple parsing, normally you'd parse types
                            msg_type = data.get("type", "unknown")
                            content = data.get("message", data)
                            
                            if msg_type == "log":
                                # Account log
                                char = content.get("character", "System")
                                text = content.get("description", str(content))
                                self._emit_log(char, text, "info")
                                
                                # Update last_decision for the TUI
                                if char in self._bot_cache:
                                    self._bot_cache[char]["last_decision"] = text
                            else:
                                # Other events (ge_order_created, achievement, etc.)
                                self._emit_log("System", f"Event [{msg_type}]: {str(content)[:100]}", "info")
                                
                        except json.JSONDecodeError:
                            self._emit_log("System", f"WS raw: {message}", "info")
                            
            except Exception as e:
                self._emit_log("System", f"WS Disconnected: {e}. Reconnecting...", "error")
                await asyncio.sleep(5)

    def _emit_log(self, character_name: str, message: str, level: str) -> None:
        """Helper to emit logs to TUI listeners."""
        for listener in self._log_listeners:
            try:
                listener(character_name, message, level)
            except Exception:
                pass

    def start_background_tasks(self) -> None:
        """Start the websocket listener."""
        if not self._ws_task:
            try:
                loop = asyncio.get_running_loop()
                self._ws_task = loop.create_task(self._ws_listener_loop())
            except RuntimeError:
                pass  # No running event loop

    # --- Protocol Methods ---

    def get_shared_state(self) -> dict[str, Any]:
        """Fetch aggregated state from API."""
        return {
            "status": "Official API Mode",
            "aggregate": {},
            "bots": list(self._bot_cache.values())
        }

    def execute_command(self, command: str, target_bot: str = "all") -> str:
        """Send command to API."""
        return "Error: Read-only mode. TUI commands are disabled when using the official API directly."

    def rest_all(self) -> None:
        """Trigger rest-all endpoint."""
        pass  # Read-only

    def add_state_listener(self, callback: Any) -> None:
        self._state_listeners.append(callback)

    def remove_state_listener(self, callback: Any) -> None:
        if callback in self._state_listeners:
            self._state_listeners.remove(callback)
        
    def add_log_listener(self, callback: Any) -> None:
        self._log_listeners.append(callback)
        
        # Start websocket if it hasn't mapped yet, since TUI is setting up
        if not self._ws_task:
            self.start_background_tasks()
        
    def remove_log_listener(self, callback: Any) -> None:
        if callback in self._log_listeners:
            self._log_listeners.remove(callback)
            
    def poll_logs(self) -> None:
        """Logs are handled asynchronously via websocket."""
        pass
        
    def get_all_summaries(self) -> list[dict[str, Any]]:
        """Get list of bot summaries by fetching /my/characters."""
        try:
            response = self.client.get("/my/characters")
            response.raise_for_status()
            characters = response.json().get("data", [])
            
            mapped_summaries = []
            for char in characters:
                # Map Official API `CharacterSchema` to TUI `BotSummary`
                name = char.get("name", "Unknown")
                hp = char.get("hp", 0)
                max_hp = char.get("max_hp", 0)
                xp = char.get("xp", 0)
                max_xp = char.get("max_xp", 0)
                
                # Fetch existing so we don't overwrite last_decision
                existing_cache = self._bot_cache.get(name, {})
                
                # If character is idle, `task` might be empty string. Fallback to `"Idle"`.
                task = char.get("task", "") or "Idle"
                
                summary = {
                    "name": name,
                    "skin": char.get("skin", "men1"),
                    "hp": f"{hp}/{max_hp}",
                    "xp": f"{xp}/{max_xp}",
                    "current_task": task,
                    "cooldown": char.get("cooldown", 0),
                    "last_decision": existing_cache.get("last_decision", {}),
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
        """No swarm demand in official API."""
        return self._swarm_demand_cache

    def get_bot(self, name: str) -> BotProxy | None:
        """Get a proxy bot object for TUI compatibility."""
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
        """Return None to satisfy UI roster access checks."""
        return None
