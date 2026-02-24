"""Crafting demand panel showing live swarm supply-chain needs."""

from __future__ import annotations

from typing import Any

from textual.widgets import Static

from sentient_artifacts.tui.widgets.crafting_demand_panel.formatting import (
    ActorAnalytics,
    CodeFormatter,
)
from sentient_artifacts.tui.widgets.crafting_demand_panel.models import (
    CraftingDemandSnapshot,
)
from sentient_artifacts.tui.widgets.crafting_demand_panel.normalization import (
    BountyNormalizer,
)
from sentient_artifacts.tui.widgets.crafting_demand_panel.rendering import (
    CraftingDemandRenderer,
)
from sentient_artifacts.tui.widgets.crafting_demand_panel.tables import (
    DemandTableBuilder,
)


class CraftingDemandPanel(Static):
    """Right-side panel with compact crafting queue views."""

    MAX_QUEUE_ROWS = 10
    MAX_REQ_ROWS = 10

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the crafting demand panel widget."""
        super().__init__(**kwargs)
        self._last_snapshot_signature: str | None = None
        formatter = CodeFormatter()
        actor_analytics = ActorAnalytics()
        self._normalizer = BountyNormalizer()
        self._table_builder = DemandTableBuilder(
            formatter,
            actor_analytics,
            max_queue_rows=self.MAX_QUEUE_ROWS,
            max_req_rows=self.MAX_REQ_ROWS,
        )
        self._renderer = CraftingDemandRenderer(self._table_builder)

    def on_mount(self) -> None:
        """Render an empty snapshot on mount."""
        self.update_from_snapshot({})

    def update_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Render from serialized swarm demand snapshot (client mode)."""
        snapshot_model = self._snapshot_from_payload(snapshot or {})
        signature = snapshot_model.signature()
        if signature == self._last_snapshot_signature:
            return
        self._last_snapshot_signature = signature
        self.update(self._renderer.render(snapshot_model))

    def _snapshot_from_payload(
        self,
        payload: dict[str, Any],
    ) -> CraftingDemandSnapshot:
        """Normalize snapshot payload into a structured model."""
        targets = {
            str(code): int(qty)
            for code, qty in (payload.get("crafting_targets") or {}).items()
        }
        bounties = self._normalizer.normalize(payload.get("bounties"))
        target_details = {
            str(code): dict(detail or {})
            for code, detail in (payload.get("crafting_target_details") or {}).items()
        }
        bounty_details = {
            str(code): dict(detail or {})
            for code, detail in (payload.get("bounty_details") or {}).items()
        }
        return CraftingDemandSnapshot(
            crafting_targets=targets,
            crafting_target_details=target_details,
            bounties=bounties,
            bounty_details=bounty_details,
        )
