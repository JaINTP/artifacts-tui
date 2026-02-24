"""Data models for crafting demand snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CraftingBounty:
    """Normalized crafting bounty payload."""

    item_code: str | None = None
    quantity_needed: int = 0
    priority_score: int = 0
    requester: str | None = None
    provider: str | None = None
    accepted: str | None = None
    accepted_by: dict[str, Any] = field(default_factory=dict)
    requesters: dict[str, Any] = field(default_factory=dict)
    providers: dict[str, Any] = field(default_factory=dict)

    def signature_payload(self) -> dict[str, Any]:
        """Return a stable payload for snapshot signatures."""
        return {
            "item_code": self.item_code,
            "quantity_needed": self.quantity_needed,
            "priority_score": self.priority_score,
            "requester": self.requester,
            "provider": self.provider,
            "accepted": self.accepted,
            "accepted_by": self.accepted_by,
            "requesters": self.requesters,
            "providers": self.providers,
        }


@dataclass(frozen=True)
class CraftingDemandSnapshot:
    """Normalized view of crafting demand data."""

    crafting_targets: dict[str, int] = field(default_factory=dict)
    crafting_target_details: dict[str, dict[str, Any]] = field(default_factory=dict)
    bounties: list[CraftingBounty] = field(default_factory=list)
    bounty_details: dict[str, dict[str, Any]] = field(default_factory=dict)

    def signature(self) -> str:
        """Compute a signature for change detection."""
        payload = {
            "crafting_targets": self.crafting_targets,
            "crafting_target_details": self.crafting_target_details,
            "bounties": [bounty.signature_payload() for bounty in self.bounties],
            "bounty_details": self.bounty_details,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)

    def targets_sorted(self) -> list[tuple[str, int]]:
        """Return sorted crafting targets by quantity then code."""
        return sorted(
            (
                (code, int(qty))
                for code, qty in (self.crafting_targets or {}).items()
                if int(qty) > 0
            ),
            key=lambda item: (-item[1], item[0]),
        )
