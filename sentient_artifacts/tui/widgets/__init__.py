"""TUI Widgets for Sentient Artifacts."""

from sentient_artifacts.tui.widgets.character_card import CharacterCard
from sentient_artifacts.tui.widgets.crafting_demand_panel import CraftingDemandPanel
from sentient_artifacts.tui.widgets.global_stats import GlobalStats
from sentient_artifacts.tui.widgets.log_console import LogConsole
from sentient_artifacts.tui.widgets.matrix_view import MatrixView

__all__ = [
    "CharacterCard",
    "LogConsole",
    "CraftingDemandPanel",
    "GlobalStats",
    "MatrixView",
]
