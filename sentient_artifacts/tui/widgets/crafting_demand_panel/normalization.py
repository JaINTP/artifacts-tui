"""Normalization helpers for crafting demand payloads."""

from __future__ import annotations

from typing import Any

from sentient_artifacts.tui.widgets.crafting_demand_panel.models import CraftingBounty


class BountyNormalizer:
    """Normalize raw bounty payloads into structured models."""

    def normalize(self, raw_bounties: Any) -> list[CraftingBounty]:
        """Normalize bounties into structured entries."""
        rows: list[CraftingBounty] = []

        if isinstance(raw_bounties, dict):
            iterable = list(raw_bounties.values())
        elif isinstance(raw_bounties, list):
            iterable = raw_bounties
        else:
            iterable = []

        for bounty in iterable:
            if isinstance(bounty, dict):
                rows.append(
                    CraftingBounty(
                        item_code=bounty.get("item_code"),
                        quantity_needed=int(bounty.get("quantity_needed", 0) or 0),
                        priority_score=int(bounty.get("priority_score", 0) or 0),
                        requester=bounty.get("requester"),
                        provider=bounty.get("provider"),
                        accepted=bounty.get("accepted"),
                        accepted_by=bounty.get("accepted_by") or {},
                        requesters=bounty.get("requesters") or {},
                        providers=bounty.get("providers") or {},
                    )
                )
                continue

            rows.append(
                CraftingBounty(
                    item_code=getattr(bounty, "item_code", None),
                    quantity_needed=int(getattr(bounty, "quantity_needed", 0) or 0),
                    priority_score=int(getattr(bounty, "priority_score", 0) or 0),
                    requester=getattr(
                        bounty,
                        "primary_requester",
                        getattr(bounty, "requester", None),
                    ),
                    provider=getattr(bounty, "primary_provider", None),
                    accepted=getattr(bounty, "accepted", None),
                    accepted_by=getattr(bounty, "accepted_by", {}) or {},
                    requesters=getattr(bounty, "requesters", {}) or {},
                    providers=getattr(bounty, "providers", {}) or {},
                )
            )

        rows.sort(
            key=lambda row: (
                -int(row.priority_score),
                -int(row.quantity_needed),
                str(row.item_code or ""),
            )
        )
        return rows
