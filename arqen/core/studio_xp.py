"""XP across the Arqen apps, as worked out by Arqen AI Studio.

Studio counts uploads, renders, tasks and git history for every Arqen app and
saves the result to ``data/xp.json``.  Mission Control only reads that file, so
the numbers are the same in both places; without Studio the panel stays hidden.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from arqen.config.paths import APP_ROOT


def snapshot_path() -> Path:
    """Studio's XP file: ``ARQEN_STUDIO_DIR`` or the sibling folder "Arqen AI Studio"."""
    root = os.environ.get("ARQEN_STUDIO_DIR") or str(APP_ROOT.parent / "Arqen AI Studio")
    return Path(root) / "data" / "xp.json"


class StudioXp:
    """Reads the snapshot again only when Studio has rewritten it (the dashboard refreshes every 2 s)."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or snapshot_path()
        self._mtime: float | None = None
        self._data: dict | None = None

    def load(self) -> dict | None:
        try:
            mtime = self.path.stat().st_mtime
        except OSError:
            self._mtime, self._data = None, None
            return None
        if mtime != self._mtime:
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
                self._mtime = mtime
            except (OSError, ValueError):
                # Caught mid-write: keep what we had and try again next refresh.
                pass
        return self._data


def progress(data: dict) -> float:
    """How far into the current level, 0..1."""
    span = data["nextLevelAt"] - data["levelStart"]
    return max(0.0, min(1.0, (data["total"] - data["levelStart"]) / span)) if span else 1.0


def latest_achievement(data: dict) -> dict | None:
    unlocked = [a for a in data.get("achievements", []) if a.get("unlockedAt")]
    return max(unlocked, key=lambda a: a["unlockedAt"]) if unlocked else None
