"""Rendering helpers for the crafting demand panel."""

from __future__ import annotations

from rich.console import Group
from rich.text import Text

from sentient_artifacts.tui.widgets.crafting_demand_panel.models import (
    CraftingDemandSnapshot,
)
from sentient_artifacts.tui.widgets.crafting_demand_panel.tables import (
    DemandTableBuilder,
)


class CraftingDemandRenderer:
    """Render crafting demand snapshots into Rich groups."""

    def __init__(self, table_builder: DemandTableBuilder) -> None:
        """Initialize the renderer with a table builder."""
        self._table_builder = table_builder

    def render(self, snapshot: CraftingDemandSnapshot) -> Group:
        """Render the demand snapshot into a Rich group."""
        header = Text("CRAFTING DEMAND", style="bold #9feec0")
        return Group(
            header,
            self._table_builder.build_craft_queue_table(
                snapshot.bounties,
                snapshot.bounty_details,
            ),
            self._table_builder.build_craft_req_queue_table(
                snapshot.targets_sorted(),
                snapshot.bounties,
                snapshot.crafting_target_details,
            ),
        )
