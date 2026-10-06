"""Match reminders: reading a club calendar and messaging in the hours before kick-off."""

from datetime import datetime, timedelta, timezone

from arqen.mission.match_reminders import MatchReminders, due_reminders, parse_ics

ICS = """BEGIN:VCALENDAR\r
BEGIN:VEVENT\r
DTSTART:20261011T143000Z\r
UID:men-1\r
SUMMARY:BK Häcken – Öis (h)\r
LOCATION:Nordic Wellness Arena\\, Idrottsvägen 1\\, Göteborg\r
END:VEVENT\r
BEGIN:VEVENT\r
DTSTART:20261011T110000Z\r
UID:women-1\r
SUMMARY:BK Häcken - Hammarby (d)\r
END:VEVENT\r
BEGIN:VEVENT\r
DTSTART;VALUE=DATE:20261012\r
UID:allday\r
SUMMARY:Supporter day (h)\r
END:VEVENT\r
END:VCALENDAR\r
"""
KICKOFF = datetime(2026, 10, 11, 14, 30, tzinfo=timezone.utc)


def test_parses_events_with_a_kickoff_and_skips_all_day_ones():
    matches = parse_ics(ICS)
    assert [m.uid for m in matches] == ["women-1", "men-1"]
    assert matches[1].start == KICKOFF
    assert matches[1].location == "Nordic Wellness Arena"


def test_one_reminder_per_hour_for_the_filtered_team_only():
    matches = parse_ics(ICS)
    assert due_reminders(matches, set(), KICKOFF - timedelta(hours=7), flt="(h)", hours_before=6) == []
    due = due_reminders(matches, set(), KICKOFF - timedelta(hours=5, minutes=59), flt="(h)", hours_before=6)
    assert len(due) == 1
    key, text = due[0]
    assert key == "men-1|6"
    assert text.startswith("⚽ BK Häcken – Öis kicks off in 6 hours (")
    assert "(h)" not in text and "Nordic Wellness Arena" in text
    assert due_reminders(matches, {key}, KICKOFF - timedelta(hours=5, minutes=30), flt="(h)", hours_before=6) == []
    assert due_reminders(matches, {key}, KICKOFF - timedelta(minutes=50), flt="(h)", hours_before=6)[0][0] == "men-1|1"
    assert due_reminders(matches, set(), KICKOFF + timedelta(minutes=1), flt="(h)", hours_before=6) == []


def test_check_sends_once_and_remembers_it(tmp_path):
    sent = []
    reminders = MatchReminders(sent.append, data_dir=tmp_path, fetch=lambda url: ICS)
    now = KICKOFF - timedelta(hours=2, minutes=10)
    assert reminders.check(now) == sent and len(sent) == 1
    assert reminders.check(now + timedelta(minutes=1)) == []
    assert len(reminders.check(now + timedelta(minutes=15))) == 1  # the 2-hour mark
    assert (tmp_path / "match_reminders.json").exists()


def test_turned_off_sends_nothing(tmp_path):
    (tmp_path / "match_reminders.json").write_text('{"enabled": false}', encoding="utf-8")
    sent = []
    MatchReminders(sent.append, data_dir=tmp_path, fetch=lambda url: ICS).check(KICKOFF - timedelta(hours=1))
    assert sent == []
