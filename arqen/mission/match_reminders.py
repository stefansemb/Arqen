"""Match reminders: Telegram messages in the hours before a team's kick-off.

Reads the team's public calendar (an .ics feed), keeps the matches whose title
contains the filter (BK Häcken marks men's games "(h)"), and sends one message
per hour from ``hours_before`` hours until kick-off. No AI is involved.

It runs on its own, so reminders arrive while the app is closed:
``pythonw -m arqen.mission.match_reminders`` from a Windows scheduled task
every 5 minutes ("Arqen match reminders"). The calendar is fetched at most every
few hours. Settings live in ``data/match_reminders.json``, what has been sent in
``data/match_reminders_state.json`` and errors in ``data/match_reminders.log``.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

from arqen.config import paths

DEFAULTS = {
    "enabled": True,
    "label": "BK Häcken",
    "calendar_url": "https://calendar.google.com/calendar/ical/8516c9f341e6ae8dd8e54c0f872f8a42907911cecb863410423fb07c6e171fd0%40group.calendar.google.com/public/basic.ics",
    "filter": "(h)",
    "hours_before": 6,
}
REFRESH = timedelta(hours=3)


@dataclass
class Match:
    uid: str
    start: datetime
    title: str
    location: str


def _unescape(value: str) -> str:
    return value.replace("\\,", ",").replace("\\;", ";").replace("\\n", " ").replace("\\N", " ").replace("\\\\", "\\").strip()


def _parse_start(params: str, value: str) -> datetime | None:
    value = value.strip()
    try:
        if "VALUE=DATE" in params and len(value) == 8:
            # All-day entries have no kick-off time, so they get no countdown.
            return None
        if value.endswith("Z"):
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        # Floating or TZID times: the feeds this is used with are Swedish and so is this PC.
        return datetime.strptime(value[:15], "%Y%m%dT%H%M%S").astimezone()
    except ValueError:
        return None


def parse_ics(text: str) -> list[Match]:
    text = re.sub(r"\r?\n[ \t]", "", text)
    matches = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        fields: dict[str, tuple[str, str]] = {}
        for line in block.splitlines():
            key, sep, value = line.partition(":")
            if not sep:
                continue
            name, _, params = key.partition(";")
            fields.setdefault(name.upper(), (params, value))
        if "DTSTART" not in fields:
            continue
        start = _parse_start(*fields["DTSTART"])
        if start is None:
            continue
        matches.append(Match(
            uid=fields.get("UID", ("", ""))[1].strip() or fields["DTSTART"][1],
            start=start,
            title=_unescape(fields.get("SUMMARY", ("", ""))[1]),
            location=_unescape(fields.get("LOCATION", ("", ""))[1]).split(",")[0],
        ))
    return sorted(matches, key=lambda m: m.start)


def _fmt_left(delta: timedelta) -> str:
    minutes = max(1, round(delta.total_seconds() / 60))
    hours, mins = divmod(minutes, 60)
    if mins >= 55:
        # The check runs just after each hour mark, so "5 h 59 min" reads better as "6 hours".
        hours, mins = hours + 1, 0
    if hours and mins >= 5:
        return f"{hours} h {mins} min"
    if hours:
        return f"{hours} hour" + ("s" if hours > 1 else "")
    return f"{mins} min"


def due_reminders(matches: list[Match], sent: set[str], now: datetime, *, flt: str, hours_before: int) -> list[tuple[str, str]]:
    """The (key, message) pairs to send now: one per match per hour bucket before kick-off."""
    out = []
    for match in matches:
        if flt and flt.lower() not in match.title.lower():
            continue
        left = match.start - now
        if left <= timedelta(0) or left > timedelta(hours=hours_before):
            continue
        bucket = math.ceil(left.total_seconds() / 3600)
        key = f"{match.uid}|{bucket}"
        if key in sent:
            continue
        title = match.title.replace(flt, "").strip() if flt else match.title
        kickoff = match.start.astimezone().strftime("%H:%M")
        where = f", {match.location}" if match.location else ""
        out.append((key, f"⚽ {title} kicks off in {_fmt_left(left)} ({kickoff}{where})."))
    return out


class MatchReminders:
    def __init__(self, send: Callable[[str], None], data_dir: Path | None = None,
                 fetch: Callable[[str], str] | None = None) -> None:
        root = data_dir or paths.data_dir()
        self.settings_path = root / "match_reminders.json"
        self.state_path = root / "match_reminders_state.json"
        self.cache_path = root / "match_reminders.ics"
        self.send = send
        self.fetch = fetch or self._fetch

    def settings(self) -> dict:
        if not self.settings_path.exists():
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            self.settings_path.write_text(json.dumps(DEFAULTS, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            return {**DEFAULTS, **json.loads(self.settings_path.read_text(encoding="utf-8"))}
        except (OSError, ValueError):
            return dict(DEFAULTS)

    @staticmethod
    def _fetch(url: str) -> str:
        request = Request(url, headers={"User-Agent": "Arqen Mission Control"})
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")

    def _calendar(self, url: str, now: datetime) -> str:
        # Each run is a new process, so the cached copy's age decides when to fetch again.
        try:
            age = now - datetime.fromtimestamp(self.cache_path.stat().st_mtime, timezone.utc)
        except OSError:
            age = REFRESH
        if age >= REFRESH or age < timedelta(0):
            try:
                self.cache_path.write_text(self.fetch(url), encoding="utf-8")
            except Exception:
                # Offline: keep using the last copy; the next run tries again.
                if not self.cache_path.exists():
                    raise
        return self.cache_path.read_text(encoding="utf-8")

    def check(self, now: datetime | None = None) -> list[str]:
        now = now or datetime.now(timezone.utc)
        cfg = self.settings()
        if not cfg.get("enabled") or not cfg.get("calendar_url"):
            return []
        matches = parse_ics(self._calendar(cfg["calendar_url"], now))
        try:
            sent = set(json.loads(self.state_path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            sent = set()
        messages = []
        for key, text in due_reminders(matches, sent, now, flt=cfg.get("filter", ""), hours_before=int(cfg.get("hours_before", 6))):
            self.send(text)
            sent.add(key)
            messages.append(text)
        if messages:
            # Keep only keys for matches that haven't kicked off, so the file stays small.
            live = {m.uid for m in matches if m.start > now}
            self.state_path.write_text(json.dumps(sorted(k for k in sent if k.split("|")[0] in live)), encoding="utf-8")
        return messages


def main() -> int:
    """One check, for the scheduled task. Errors go to data/match_reminders.log (pythonw has no console)."""
    from arqen.connectors import store as connector_store
    from arqen.connectors.messaging import telegram_send

    reminders = MatchReminders(lambda text: telegram_send(connector_store.load_credentials("telegram"), text))
    try:
        reminders.check()
    except Exception as error:
        log = reminders.settings_path.parent / "match_reminders.log"
        with log.open("a", encoding="utf-8") as handle:
            handle.write(f"{datetime.now().isoformat(timespec='seconds')} {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
