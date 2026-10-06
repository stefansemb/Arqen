"""The project board: every project with its milestones and how far it has come.

Each project has a short list of milestones; the progress is the share that is
ticked off, unless it has been set by hand.  Ideas that aren't part of the plan
yet are parked under "later" and don't count.  Stored as ``data/projects.json``,
so it is easy to edit by hand and stays out of the repository.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Milestone:
    text: str
    done: bool = False
    done_at: str | None = None


@dataclass
class Project:
    id: str
    name: str
    milestones: list[Milestone] = field(default_factory=list)
    later: list[str] = field(default_factory=list)
    # Set by hand (0-100); None means worked out from the milestones.
    manual_percent: int | None = None

    @property
    def percent(self) -> int:
        if self.manual_percent is not None:
            return self.manual_percent
        if not self.milestones:
            return 0
        return round(100 * sum(m.done for m in self.milestones) / len(self.milestones))

    @property
    def next_milestone(self) -> str | None:
        return next((m.text for m in self.milestones if not m.done), None)


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "project"


class ProjectBoard:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.projects: list[Project] = []
        self._mtime: float | None = None
        self.reload()

    def reload(self) -> bool:
        """Reads the file again if it changed on disk (edited by hand); True when it did."""
        try:
            mtime = self.path.stat().st_mtime
        except OSError:
            changed = bool(self.projects)
            self.projects, self._mtime = [], None
            return changed
        if mtime == self._mtime:
            return False
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            # Half written or a typo while editing by hand: keep what we had.
            return False
        self.projects = [
            Project(
                id=p["id"],
                name=p.get("name", p["id"]),
                milestones=[Milestone(**m) for m in p.get("milestones", [])],
                later=list(p.get("later", [])),
                manual_percent=p.get("manual_percent"),
            )
            for p in raw.get("projects", [])
        ]
        self._mtime = mtime
        return True

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"projects": [asdict(p) for p in self.projects]}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
        self._mtime = self.path.stat().st_mtime

    def get(self, project_id: str) -> Project | None:
        return next((p for p in self.projects if p.id == project_id), None)

    def add_project(self, name: str) -> Project:
        base = slug(name)
        project_id, n = base, 2
        while self.get(project_id):
            project_id, n = f"{base}-{n}", n + 1
        project = Project(id=project_id, name=name.strip())
        self.projects.append(project)
        self.save()
        return project

    def remove_project(self, project_id: str) -> None:
        self.projects = [p for p in self.projects if p.id != project_id]
        self.save()

    def add_milestone(self, project_id: str, text: str) -> None:
        self.get(project_id).milestones.append(Milestone(text.strip()))
        self.save()

    def set_done(self, project_id: str, index: int, done: bool) -> None:
        milestone = self.get(project_id).milestones[index]
        if milestone.done == done:
            return
        milestone.done = done
        milestone.done_at = _now() if done else None
        self.save()

    def remove_milestone(self, project_id: str, index: int) -> None:
        del self.get(project_id).milestones[index]
        self.save()

    def add_later(self, project_id: str, text: str) -> None:
        self.get(project_id).later.append(text.strip())
        self.save()

    def remove_later(self, project_id: str, index: int) -> None:
        del self.get(project_id).later[index]
        self.save()

    def promote_later(self, project_id: str, index: int) -> None:
        """Turns a parked idea into a milestone, now that it is part of the plan."""
        project = self.get(project_id)
        project.milestones.append(Milestone(project.later.pop(index)))
        self.save()

    def set_manual_percent(self, project_id: str, percent: int | None) -> None:
        self.get(project_id).manual_percent = None if percent is None else max(0, min(100, int(percent)))
        self.save()
