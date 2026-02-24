"""Icon selection helpers for character card tasks."""

from __future__ import annotations

from typing import Any

from sentient_artifacts.tui.widgets.character_card.formatting.normalization import (
    TextNormalizer,
)


class TaskIconResolver:
    """Resolve ASCII icon tags for mission and task actions."""

    def __init__(self, normalizer: TextNormalizer) -> None:
        """Store the normalizer used for compact token extraction."""
        self._normalizer = normalizer

    def gather_icon_tag(self, skill: Any = None, target: Any = None) -> str:
        """Return an ASCII icon tag for gather tasks."""
        skill_token = self._normalizer.compact_token(skill)
        target_token = self._normalizer.compact_token(target)

        if "mining" in skill_token:
            return "⛏️"
        if "woodcutting" in skill_token:
            return "🪓"
        if "fishing" in skill_token:
            return "🎣"
        if any(
            tag in skill_token
            for tag in ("alchemy", "foraging", "farming", "herbal")
        ):
            return "🌸"

        if any(
            tag in target_token
            for tag in ("ore", "rock", "mine", "copper", "iron", "coal", "gold")
        ):
            return "⛏️"
        if any(
            tag in target_token
            for tag in ("tree", "wood", "log", "spruce", "ash", "oak", "maple")
        ):
            return "🪓"
        if any(
            tag in target_token
            for tag in ("fish", "spot", "gudgeon", "trout", "salmon", "shrimp")
        ):
            return "🎣"
        if any(
            tag in target_token
            for tag in ("mushroom", "herb", "flower", "berry", "root", "slime")
        ):
            return "🌸"
        return "🧺"

    def craft_icon_tag(self, target: Any = None) -> str:
        """Return an ASCII icon tag for crafting tasks."""
        token = self._normalizer.compact_token(target)
        if any(tag in token for tag in ("potion", "elixir", "flask", "brew")):
            return "⚗️"
        if any(tag in token for tag in ("cooked", "meal", "stew", "soup", "food")):
            return "🍳"
        if any(tag in token for tag in ("ring", "amulet", "jewel", "gem", "necklace")):
            return "💎"
        if any(
            tag in token
            for tag in ("shield", "armor", "helm", "helmet", "boots", "gloves", "legs")
        ):
            return "🛡️"
        if any(
            tag in token
            for tag in ("sword", "staff", "bow", "dagger", "mace", "axe", "weapon")
        ):
            return "⚒️"
        return "🔨"

    def task_icon_tag(
        self,
        action: str,
        *,
        skill: Any = None,
        target: Any = None,
    ) -> str:
        """Return an ASCII icon tag for a mission/task action."""
        token = self._normalizer.compact_token(action)
        if token == "gather":
            return self.gather_icon_tag(skill=skill, target=target)
        if token == "craft":
            return self.craft_icon_tag(target=target)
        if token in {"combat", "fight"}:
            return "⚔️"
        if token in {"bankroutine", "deposit", "withdraw", "bank"}:
            return "🏦"
        if token in {"equip", "unequip"}:
            return "🛡️"
        if token == "move":
            return "🚶"
        if token == "rest":
            return "💤"
        if token == "use":
            return "✨"
        if token in {"tasknew", "taskcomplete", "taskexchange"}:
            return "📜"
        if token in {"wait", "idle"}:
            return "⏳"
        return "📌"
