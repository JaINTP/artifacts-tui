"""Sprite rendering helpers for character cards."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from textual.containers import Horizontal

try:
    from textual_image.widget import Image as TextualImageWidget
    from textual_image.widget import UnicodeImage as TextualUnicodeImageWidget
except Exception:  # pragma: no cover - optional dependency
    TextualImageWidget = None
    TextualUnicodeImageWidget = None

SKINS_DIR = Path(__file__).resolve().parents[4] / "skins"


class SpriteRenderer:
    """Handle sprite rendering and skin ID normalization."""

    def __init__(self, skins_dir: Path) -> None:
        """Initialize the renderer with the skins directory path."""
        self._skins_dir = skins_dir

    def local_skin_exists(self, skin_id: str) -> bool:
        """Return True when a local sprite file exists for this skin id."""
        return (self._skins_dir / f"{skin_id}.png").exists()

    def normalize_skin_id(self, value: Any) -> str | None:
        """Normalize API skin payloads to local sprite IDs.

        The API/source can occasionally return malformed values (e.g. URLs,
        "None", or separator variants like ``women_2``). Normalize those so
        we don't replace a valid current portrait with an unresolvable skin id.
        """
        if value is None:
            return None

        raw = str(value).strip()
        if not raw:
            return None

        token = raw.replace("\\", "/").rsplit("/", 1)[-1]
        if token.lower().endswith(".png"):
            token = token[:-4]

        compact = "".join(ch for ch in token.lower() if ch.isalnum())
        if not compact or compact in {
            "none",
            "null",
            "undefined",
            "unknown",
            "na",
            "n/a",
        }:
            return None

        aliases = {
            "male1": "men1",
            "male2": "men2",
            "male3": "men3",
            "man1": "men1",
            "man2": "men2",
            "man3": "men3",
            "female1": "women1",
            "female2": "women2",
            "female3": "women3",
            "woman1": "women1",
            "woman2": "women2",
            "woman3": "women3",
        }
        if compact in aliases:
            candidate = aliases[compact]
            return candidate if self.local_skin_exists(candidate) else None

        if compact.startswith("men") and compact[3:].isdigit():
            candidate = f"men{int(compact[3:])}"
            return candidate if self.local_skin_exists(candidate) else None
        if compact.startswith("women") and compact[5:].isdigit():
            candidate = f"women{int(compact[5:])}"
            return candidate if self.local_skin_exists(candidate) else None

        return compact if self.local_skin_exists(compact) else None

    def resolve_image_widget_class(self, app: Any) -> type[object] | None:
        """Choose renderer based on runtime target (terminal vs browser)."""
        if self._is_web_mode(app) and TextualUnicodeImageWidget is not None:
            return TextualUnicodeImageWidget
        return TextualImageWidget

    def load_sprite(
        self,
        skin_id: str,
        app: Any,
        *,
        stack: Horizontal | None,
        stack_lookup: Callable[[], Horizontal | None],
        current_image: object | None,
    ) -> object | None:
        """Render a sprite and return the mounted image widget, if any."""
        image_widget_cls = self.resolve_image_widget_class(app)
        if image_widget_cls is None:
            return current_image

        skin_path = self._skins_dir / f"{skin_id}.png"
        if not skin_path.exists():
            return current_image

        target_stack = stack or stack_lookup()
        if target_stack is None:
            return current_image

        try:
            new_image = image_widget_cls(str(skin_path), classes="sprite-image")
            target_stack.mount(new_image)
            if current_image is not None and current_image is not new_image:
                try:
                    current_image.remove()
                except Exception:
                    pass
            return new_image
        except Exception:
            return current_image

    def _is_web_mode(self, app: Any) -> bool:
        """Return True when running via Textual web serving."""
        try:
            return bool(getattr(app, "is_web", False))
        except Exception:
            return False
