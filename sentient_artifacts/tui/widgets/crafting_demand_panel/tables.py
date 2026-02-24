"""Table builders for crafting demand views."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from rich import box
from rich.table import Table

from sentient_artifacts.tui.widgets.crafting_demand_panel.formatting import (
    ActorAnalytics,
    CodeFormatter,
)
from sentient_artifacts.tui.widgets.crafting_demand_panel.models import CraftingBounty


class DemandTableBuilder:
    """Build Rich tables for crafting demand data."""

    def __init__(
        self,
        formatter: CodeFormatter,
        actor_analytics: ActorAnalytics,
        *,
        max_queue_rows: int = 10,
        max_req_rows: int = 10,
    ) -> None:
        """Initialize table builder settings."""
        self._formatter = formatter
        self._actor_analytics = actor_analytics
        self._max_queue_rows = max_queue_rows
        self._max_req_rows = max_req_rows

    @staticmethod
    def _format_duration(seconds: float | None) -> str:
        """Format seconds into a short duration label."""
        if seconds is None:
            return "-"
        total = int(round(float(seconds)))
        if total <= 0:
            return "Ready"
        mins, secs = divmod(total, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours}h {mins}m"
        if mins > 0:
            return f"{mins}m {secs}s"
        return f"{secs}s"

    def build_craft_queue_table(
        self,
        bounties: Iterable[CraftingBounty],
        bounty_details: dict[str, dict[str, Any]] | None = None,
    ) -> Table:
        """Build the craft queue table."""
        bounty_details = bounty_details or {}
        table = Table(
            title="Craft Queue",
            box=box.SIMPLE,
            expand=True,
            show_lines=False,
            pad_edge=False,
        )
        table.add_column("Item", min_width=16)
        table.add_column("Qty", no_wrap=True, justify="right", width=4)
        table.add_column("No.", no_wrap=True, justify="right", width=4)
        table.add_column("Prio", no_wrap=True, justify="right", width=4)
        table.add_column("Requester", no_wrap=True, width=12)
        table.add_column("Provider", no_wrap=True, width=12)
        table.add_column("ETA", no_wrap=True, width=10)
        table.add_column("Active", no_wrap=True, width=14)

        bounty_list = list(bounties)
        if not bounty_list:
            table.add_row("none", "-", "-", "-", "-", "-", "-", "-")
            return table

        for idx, bounty in enumerate(bounty_list[: self._max_queue_rows], start=1):
            item = self._formatter.humanize(bounty.item_code)
            qty = int(bounty.quantity_needed or 0)
            prio = int(bounty.priority_score or 0)
            requester = bounty.requester or self._actor_analytics.primary_actor(
                bounty.requesters,
                "Unknown",
            )
            provider = bounty.provider or self._actor_analytics.primary_actor(
                bounty.providers,
                "Unassigned",
            )
            active = bounty.accepted or self._actor_analytics.actor_preview(
                bounty.accepted_by,
                fallback="-",
                max_names=2,
            )
            detail = bounty_details.get(str(bounty.item_code or ""), {})
            eta_seconds = detail.get("eta_seconds")
            eta_label = self._format_duration(
                float(eta_seconds) if eta_seconds is not None else None
            )

            table.add_row(
                item,
                str(qty),
                str(idx),
                str(prio),
                requester,
                provider,
                eta_label,
                active,
            )
        return table

    def build_craft_req_queue_table(
        self,
        targets: list[tuple[str, int]],
        bounties: Iterable[CraftingBounty],
        target_details: dict[str, dict[str, Any]] | None = None,
    ) -> Table:
        """Build the crafting requirements table."""
        target_details = target_details or {}
        shortfall_by_code: dict[str, int] = {}
        provider_by_code: dict[str, str] = {}
        for bounty in bounties:
            code = str(bounty.item_code or "")
            if not code:
                continue
            shortfall_by_code[code] = int(bounty.quantity_needed or 0)
            provider = bounty.provider or self._actor_analytics.primary_actor(
                bounty.providers,
                "Unassigned",
            )
            provider_by_code[code] = provider

        table = Table(
            title="Craft Req Queue",
            box=box.SIMPLE,
            expand=True,
            show_lines=False,
            pad_edge=False,
        )
        table.add_column("Item", min_width=16)
        table.add_column("QtyInv", no_wrap=True, justify="right", width=7)
        table.add_column("QtyNeeded", no_wrap=True, justify="right", width=9)
        table.add_column("Provider", no_wrap=True, width=12)
        table.add_column("ETA", no_wrap=True, width=10)

        if not targets:
            table.add_row("none", "-", "-", "-", "-")
            return table

        for code, target_qty in targets[: self._max_req_rows]:
            outstanding_qty = max(0, shortfall_by_code.get(code, 0))
            inv_qty = max(0, int(target_qty) - outstanding_qty)
            detail = target_details.get(code, {})
            eta_seconds = detail.get("eta_seconds")
            table.add_row(
                self._formatter.humanize(code),
                str(inv_qty),
                str(outstanding_qty),
                provider_by_code.get(code, "Unassigned"),
                self._format_duration(eta_seconds),
            )

        return table
