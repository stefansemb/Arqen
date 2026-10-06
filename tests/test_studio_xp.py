"""Studio's XP snapshot, as Mission Control reads it."""

import json

from arqen.core import studio_xp

SNAPSHOT = {
    "total": 750,
    "level": 3,
    "title": "Builder",
    "levelStart": 400,
    "nextLevelAt": 900,
    "streakWeeks": 2,
    "perApp": {"studio": 500, "mission": 250},
    "achievements": [
        {"id": "a", "name": "First Upload", "description": "", "unlockedAt": "2026-09-27T10:00:00Z"},
        {"id": "b", "name": "Shipper", "description": "", "unlockedAt": "2026-09-28T10:00:00Z"},
        {"id": "c", "name": "Centurion", "description": ""},
    ],
}


def test_missing_snapshot_means_no_panel(tmp_path):
    assert studio_xp.StudioXp(tmp_path / "xp.json").load() is None


def test_reads_the_snapshot_and_keeps_it_through_a_half_written_file(tmp_path):
    path = tmp_path / "xp.json"
    path.write_text(json.dumps(SNAPSHOT), encoding="utf-8")
    reader = studio_xp.StudioXp(path)
    assert reader.load()["level"] == 3
    path.write_text('{"total": 7', encoding="utf-8")
    import os
    os.utime(path, (1, 1))
    assert reader.load()["level"] == 3


def test_progress_and_latest_achievement():
    assert studio_xp.progress(SNAPSHOT) == 0.7
    assert studio_xp.latest_achievement(SNAPSHOT)["name"] == "Shipper"
