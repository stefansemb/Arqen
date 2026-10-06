"""The project board: milestones, progress and parked ideas."""

import json

from arqen.core.projects import ProjectBoard


def board(tmp_path):
    return ProjectBoard(tmp_path / "projects.json")


def test_progress_is_the_share_of_milestones_done(tmp_path):
    b = board(tmp_path)
    p = b.add_project("Arqen Motion")
    assert p.id == "arqen-motion" and p.percent == 0
    for text in ("MVP", "Release 1.0", "Docs"):
        b.add_milestone(p.id, text)
    b.set_done(p.id, 0, True)
    assert p.percent == 33
    assert p.next_milestone == "Release 1.0"
    assert p.milestones[0].done_at


def test_manual_percent_wins_until_cleared(tmp_path):
    b = board(tmp_path)
    p = b.add_project("Site")
    b.add_milestone(p.id, "Launch")
    b.set_manual_percent(p.id, 140)
    assert p.percent == 100
    b.set_manual_percent(p.id, None)
    assert p.percent == 0


def test_parked_ideas_dont_count_until_promoted(tmp_path):
    b = board(tmp_path)
    p = b.add_project("Studio")
    b.add_milestone(p.id, "First upload")
    b.set_done(p.id, 0, True)
    b.add_later(p.id, "Background music")
    assert p.percent == 100
    b.promote_later(p.id, 0)
    assert p.later == [] and p.percent == 50


def test_survives_a_reload_and_a_hand_edit(tmp_path):
    b = board(tmp_path)
    p = b.add_project("Studio")
    b.add_milestone(p.id, "First upload")
    again = ProjectBoard(b.path)
    assert again.get("studio").milestones[0].text == "First upload"
    data = json.loads(b.path.read_text(encoding="utf-8"))
    data["projects"][0]["name"] = "Arqen AI Studio"
    b.path.write_text(json.dumps(data), encoding="utf-8")
    import os
    os.utime(b.path, (1, 1))
    assert b.reload() and b.get("studio").name == "Arqen AI Studio"


def test_same_name_twice_gets_its_own_id(tmp_path):
    b = board(tmp_path)
    assert b.add_project("X").id == "x"
    assert b.add_project("X").id == "x-2"
