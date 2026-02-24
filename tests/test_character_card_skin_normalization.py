"""Tests for character card formatting helpers."""

from __future__ import annotations

import pytest

pytest.importorskip("textual")

from sentient_artifacts.tui.widgets.character_card import CharacterCard


def test_normalize_skin_accepts_known_ids() -> None:
    """Normalize valid skin IDs without modification."""
    assert CharacterCard._normalize_skin_id("men3") == "men3"
    assert CharacterCard._normalize_skin_id("women2") == "women2"


def test_normalize_skin_supports_common_aliases_and_formats() -> None:
    """Normalize common alias tokens and URL formats."""
    assert CharacterCard._normalize_skin_id("women_2") == "women2"
    assert CharacterCard._normalize_skin_id("male3") == "men3"
    assert CharacterCard._normalize_skin_id("female2") == "women2"
    assert (
        CharacterCard._normalize_skin_id(
            "https://artifactsmmo.com/images/characters/women2.png"
        )
        == "women2"
    )


def test_normalize_skin_rejects_empty_or_invalid_tokens() -> None:
    """Reject empty and invalid skin identifiers."""
    assert CharacterCard._normalize_skin_id(None) is None
    assert CharacterCard._normalize_skin_id("") is None
    assert CharacterCard._normalize_skin_id("  ") is None
    assert CharacterCard._normalize_skin_id("None") is None
    assert CharacterCard._normalize_skin_id("null") is None
    assert CharacterCard._normalize_skin_id("totally_fake_skin") is None


def test_normalize_goal_text_humanizes_code_like_values() -> None:
    """Humanize goal text values for display."""
    assert CharacterCard._normalize_goal_text("best_health_potions", "") == "Best Health Potions"
    assert CharacterCard._normalize_goal_text("Mission: craft_gear", "") == "Mission: Craft Gear"
    assert CharacterCard._normalize_goal_text("Crafting 2x iron_bar", "") == "Crafting 2x iron_bar"


def test_gather_icon_tag_classifies_skills_and_resources() -> None:
    """Ensure gather icon tags match skills and resources."""
    assert CharacterCard._gather_icon_tag(skill="mining", target="copper_rocks") == "⛏️"
    assert CharacterCard._gather_icon_tag(skill="woodcutting", target="ash_tree") == "🪓"
    assert CharacterCard._gather_icon_tag(skill="fishing", target="gudgeon_spot") == "🎣"
    assert CharacterCard._gather_icon_tag(skill="alchemy", target="mushroom") == "🌸"
    assert CharacterCard._gather_icon_tag(skill=None, target="gudgeon_spot") == "🎣"


def test_task_icon_tag_covers_core_actions() -> None:
    """Ensure task icon tags cover core actions."""
    assert CharacterCard._task_icon_tag("craft", target="iron_bar") == "🔨"
    assert CharacterCard._task_icon_tag("fight", target="yellow_slime") == "⚔️"
    assert CharacterCard._task_icon_tag("deposit", target="wood") == "🏦"
    assert CharacterCard._task_icon_tag("equip", target="wooden_staff") == "🛡️"
    assert CharacterCard._task_icon_tag("move", target=None) == "🚶"
