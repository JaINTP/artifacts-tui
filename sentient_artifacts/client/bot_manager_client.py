"""Client and protocol helpers for the bot manager API."""

from __future__ import annotations

from typing import Any, Protocol

import httpx


class BotManagerProtocol(Protocol):
    """Protocol defining the interface required by the TUI."""
    
    def get_shared_state(self) -> dict[str, Any]:
        """Return the shared state payload."""
        ...

    def execute_command(self, command: str, target_bot: str = "all") -> str:
        """Send a command to the bot manager."""
        ...

    def rest_all(self) -> None:
        """Request a rest-all action for bots."""
        ...

    def add_state_listener(self, callback: Any) -> None:
        """Register a state update listener."""
        ...

    def remove_state_listener(self, callback: Any) -> None:
        """Remove a state update listener."""
        ...

    def add_log_listener(self, callback: Any) -> None:
        """Register a log listener."""
        ...

    def remove_log_listener(self, callback: Any) -> None:
        """Remove a log listener."""
        ...

    def get_swarm_demand_snapshot(self) -> dict[str, Any]:
        """Return the current swarm demand snapshot."""
        ...


class BotManagerClient:
    """Client for interacting with the remote BotManager API.
    
    Implements the BotManagerProtocol so it can be used interchangeably 
    with BotManager in the TUI.
    """
    
    def __init__(self, base_url: str = "http://localhost:8765") -> None:
        """Initialize the API client with a base URL."""
        self.base_url = base_url.rstrip("/")
        # The TUI expects these list methods to exist, even if we don't use them for pushes
        self._state_listeners: list[Any] = []
        self._log_listeners: list[Any] = []
        
        # We'll use a sync client for now as TUI methods are often synchronous
        self.client = httpx.Client(base_url=self.base_url, timeout=5.0)
        self._bot_cache: dict[str, dict[str, Any]] = {}
        self._last_log_timestamp = 0.0
        self._swarm_demand_cache: dict[str, Any] = {
            "crafting_targets": {},
            "character_demands": {},
            "character_requests": {},
            "bounties": [],
        }

    def get_shared_state(self) -> dict[str, Any]:
        """Fetch aggregated state from API."""
        try:
            response = self.client.get("/status")
            response.raise_for_status()
            data = response.json()
            
            # Cache the bot summaries for get_bot calls
            if "bots" in data:
                self._update_cache(data["bots"])
                
            return data
        except Exception as e:
            return {
                "status": "API Error",
                "aggregate": {},
                "bots": [],
                "error": str(e)
            }

    def execute_command(self, command: str, target_bot: str = "all") -> str:
        """Send command to API."""
        try:
            # Parse command to match API expected format
            parts = command.strip().split()
            if not parts:
                return "Error: Empty command"
                
            action = parts[0].lower()
            params = parts[1:]
            
            task: dict[str, Any] = {"action": action}
            
            # Simple parsing logic replicated from manager for the API payload
            # The API expects: { "bot_name": "...", "task": { ... } }
            
            # Client-side validation helps avoid bad requests
            if action == "move":
                if len(params) >= 2:
                    task["x"] = int(params[0])
                    task["y"] = int(params[1])
            elif action in ["craft", "deposit", "withdraw"]:
                if len(params) >= 1:
                    task["code"] = params[0]
                if len(params) >= 2:
                    task["quantity"] = int(params[1])
            elif action == "equip":
                if len(params) >= 2:
                    task["code"] = params[0]
                    task["slot"] = params[1]
            elif action == "unequip":
                if len(params) >= 1:
                    task["slot"] = params[0]
            
            payload = {
                "bot_name": target_bot if target_bot.lower() != "all" else None,
                "task": task
            }
            
            response = self.client.post("/command", json=payload)
            response.raise_for_status()
            data = response.json()
            return f"Command queued via API: {data.get('status')}"
            
        except Exception as e:
            return f"Error sending command: {e}"

    def rest_all(self) -> None:
        """Trigger rest-all endpoint."""
        try:
            self.client.post("/bots/rest-all")
        except Exception:
            pass

    # Stub listener methods to satisfy Protocol
    # In a real decoupled app, we'd use WebSocket here
    def add_state_listener(self, callback: Any) -> None:
        """Register a local state listener."""
        self._state_listeners.append(callback)

    def remove_state_listener(self, callback: Any) -> None:
        """Remove a local state listener."""
        if callback in self._state_listeners:
            self._state_listeners.remove(callback)
        
    def add_log_listener(self, callback: Any) -> None:
        """Register a local log listener."""
        self._log_listeners.append(callback)
        
    def remove_log_listener(self, callback: Any) -> None:
        """Remove a local log listener."""
        if callback in self._log_listeners:
            self._log_listeners.remove(callback)
            
    def poll_logs(self) -> None:
        """Fetch and emit new logs from the server."""
        try:
            response = self.client.get("/logs")
            if response.status_code == 200:
                logs = response.json().get("logs", [])
                # Process logs
                for log in logs:
                    ts = log.get("timestamp", 0)
                    if ts > self._last_log_timestamp:
                        self._last_log_timestamp = ts
                        # Emit
                        char = log.get("character_name")
                        msg = log.get("message")
                        level = log.get("level")
                        for listener in self._log_listeners:
                            listener(char, msg, level)
        except Exception:
            pass
        
    def get_all_summaries(self) -> list[dict[str, Any]]:
        """Get list of bot summaries."""
        try:
            response = self.client.get("/bots")
            response.raise_for_status()
            data = response.json().get("bots", [])
            # Update cache
            self._update_cache(data)
            return data
        except Exception:
            return []

    def get_swarm_demand_snapshot(self) -> dict[str, Any]:
        """Fetch swarm demand board snapshot from API with local cache fallback."""
        try:
            response = self.client.get("/swarm/demand")
            response.raise_for_status()
            data = response.json() or {}
            if isinstance(data, dict):
                self._swarm_demand_cache = data
            return self._swarm_demand_cache
        except Exception:
            return self._swarm_demand_cache

    def get_bot(self, name: str) -> BotProxy | None:
        """Get a proxy bot object for TUI compatibility."""
        summary = self._bot_cache.get(name)
        if not summary:
            # Try to fetch fresh if not in cache (fallback)
            try:
                self.get_all_summaries()
                summary = self._bot_cache.get(name)
            except Exception:
                pass
        
        if summary:
            return BotProxy(summary)
        return None

    def _update_cache(self, summaries: list[dict[str, Any]]) -> None:
        """Update the internal cache of bot summaries."""
        for summary in summaries:
            name = summary.get("name")
            if name:
                self._bot_cache[name] = summary

    # Stub specifically for TUI access to 'roster' if it tries to access it directly
    # The TUI currently checks hasattr(manager, 'roster')
    @property
    def roster(self) -> None:
        """Return None to satisfy UI roster access checks."""
        return None


class BotProxy:
    """A proxy class that mimics BotInstance for the TUI."""
    
    def __init__(self, summary: dict[str, Any]) -> None:
        """Initialize a proxy with a bot summary payload."""
        self.summary = summary
        self.character_name = summary.get("name", "Unknown")
        
    def get_summary(self) -> dict[str, Any]:
        """Return the cached summary payload."""
        return self.summary
