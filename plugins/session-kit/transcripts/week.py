"""The owner's week against their working window, for the owner alone (A93).

``session-transcripts week`` writes the Friday review of the rules-and-load
audit's part 2a to ``week-<monday>.md`` beside the hold's settings, under
``~/.claude/session-kit/load/``, and prints its path and nothing else: no
figure of it reaches a session that runs it (C5). It reads the owner's own
prompts from the transcripts, the settings the hold reads (``settings.json``)
and the hold's log (``holds.jsonl``). It gives, from Monday to the day asked
for: the hours and the messages in and out of the work window by day, the
day's first and last message, the streak, the sittings reopened within an
hour of the window closing, the messages by folder, with the settings'
``watch`` folders on lines of their own, the share on the week's focus list
(A94), the reasons log, and the 2b bar with its verdict once its weeks are up. A message in the personal slot counts as
off-window for the bar, as it did in the October baseline.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from records import Session

LOAD_DIR = Path.home() / ".claude" / "session-kit" / "load"
SITTING_GAP = timedelta(minutes=20)
DEDUPE_GAP = timedelta(minutes=2)
REOPEN_WITHIN = timedelta(minutes=60)
# A message before 04:00 belongs to the day before, so a night's last message is that day's.
DAY_CUTOFF = timedelta(hours=4)
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
# The audit's October, which the bar is measured against.
BASELINE = "October: 65% of messages off-window, the last around 00:05, 125 sittings reopened within an hour of the window closing, a 32-day streak."
# Prompts the person did not type, which the transcripts store as theirs.
NOT_TYPED = re.compile(
    r"^(This session is being continued from a previous conversation|Base directory for this skill:|Another Claude session sent|"
    r"The session-kit plugin sent a message|Continue\. Read again in full the documents CLAUDE\.local\.md lists|"
    r"\[Request interrupted by user|The app was quit while you were working)"
)


# A focus list's heading, and a word of a must-have's line that names a folder.
FOCUS_HEADING = re.compile(r"^#\s*Week of (\d{4}-\d{2}-\d{2})\s*$", re.M)
FOCUS_ITEM = re.compile(r"^\s*[-*]\s+")
FOCUS_PATH = re.compile(r"^(~|~?/)")


@dataclass
class Message:
    at: datetime
    folder: str
    kind: str
    inside: bool


def minute_of(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def within(span: dict, at: datetime) -> bool:
    minute = at.hour * 60 + at.minute
    return DAYS[at.weekday()] in span["days"] and any(
        minute_of(r.split("-")[0]) <= minute < minute_of(r.split("-")[1]) for r in span["hours"]
    )


def folder_of(cwd: str | None, home: str) -> str:
    """The folder a prompt was typed in, a worktree under its checkout's, the home written as ``~``."""
    path = re.sub(r"/\.claude/worktrees/.*$", "", cwd or "?")
    return "~" + path[len(home):] if path == home or path.startswith(home + "/") else path


def under(folder: str, roots: list[str]) -> bool:
    return any(folder == r.rstrip("/") or folder.startswith(r.rstrip("/") + "/") for r in roots)


def parse_focus(text: str, home: str) -> tuple[str | None, list[tuple[str, list[str]]]]:
    """The Monday a focus list's heading names, and each must-have's name and folders, the home written as ``~``, as the hold reads it."""
    heading = FOCUS_HEADING.search(text)
    items: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if not FOCUS_ITEM.match(line):
            continue
        words = [re.sub(r"[,;]$", "", w.replace("`", "")) for w in FOCUS_ITEM.sub("", line).split()]
        name = re.sub(r"[\s:,\-–—]+$", "", " ".join(w for w in words if not FOCUS_PATH.match(w)))
        items.append((name, [folder_of(w, home).rstrip("/") for w in words if FOCUS_PATH.match(w)]))
    return (heading.group(1) if heading else None), items


def focus_list(load_dir: Path, monday: date, home: str) -> list[tuple[str, list[str]]] | None:
    """The week's focus list: the copy the hold kept beside its log, else the owner's list when its heading is that week."""
    for path in (load_dir / f"focus-{monday.isoformat()}.md", load_dir.parent / "focus.md"):
        if path.is_file():
            week, items = parse_focus(path.read_text(encoding="utf-8"), home)
            if week == monday.isoformat():
                return items
    return None


def focus_name(folder: str, items: list[tuple[str, list[str]]] | None) -> str | None:
    return next((name for name, folders in items or [] if under(folder, folders)), None)


def messages_of(sessions: list[Session], settings: dict, home: str) -> list[Message]:
    """The owner's typed prompts, the same text sent again within two minutes in the same folder counted once."""
    tz = ZoneInfo(settings["timeZone"])
    typed = sorted(
        ((a.at.astimezone(tz), folder_of(a.cwd, home), a.text) for s in sessions for a in s.asks if a.at is not None and not NOT_TYPED.match(a.text)),
        key=lambda t: t[0],
    )
    kept: list[Message] = []
    last: dict[tuple[str, str], datetime] = {}
    for at, folder, text in typed:
        before = last.get((folder, text))
        last[(folder, text)] = at
        if before is not None and at - before <= DEDUPE_GAP:
            continue
        kind = "personal" if under(folder, settings["personal"]["folders"]) else "work"
        kept.append(Message(at, folder, kind, within(settings["work"], at)))
    return kept


def share(part: int, whole: int) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "-"


def clock(at: datetime, day: date) -> str:
    """The time of day, past midnight written as 24:xx and on, against the day it belongs to."""
    minutes = int((at.replace(tzinfo=None) - datetime(day.year, day.month, day.day)).total_seconds() // 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    return "\n".join(out + ["| " + " | ".join(row) + " |" for row in rows])


def sittings(ms: list[Message]) -> list[list[Message]]:
    out: list[list[Message]] = []
    for m in ms:
        if out and m.at - out[-1][-1].at <= SITTING_GAP:
            out[-1].append(m)
        else:
            out.append([m])
    return out


def active_minutes(ms: list[Message]) -> list[datetime]:
    """The minutes of the owner's sittings: each message's own minute, and the time between two messages twenty minutes or less apart."""
    seen: set[datetime] = set()
    for a, b in zip(ms, ms[1:] + [None]):
        start = a.at.replace(second=0, microsecond=0)
        end = b.at if b is not None and b.at - a.at <= SITTING_GAP else start + timedelta(minutes=1)
        t = start
        while t < end:
            seen.add(t)
            t += timedelta(minutes=1)
    return sorted(seen)


def window_ends(settings: dict) -> list[int]:
    return sorted({minute_of(r.split("-")[1]) for r in settings["work"]["hours"]})


def reopened(ms: list[Message], settings: dict) -> int:
    """Weekday sittings off the window that began within an hour after it closed, the overrun of an in-window sitting aside."""
    n = 0
    for sitting in sittings(ms):
        first = sitting[0]
        if first.inside or first.at.weekday() >= 5:
            continue
        minute = first.at.hour * 60 + first.at.minute
        if any(0 <= minute - end < REOPEN_WITHIN.total_seconds() // 60 for end in window_ends(settings)):
            n += 1
    return n


def streak(ms: list[Message], until: date) -> int:
    active = {m.at.date() for m in ms}
    n, d = 0, until
    while d in active:
        n += 1
        d -= timedelta(days=1)
    return n


def day_of(m: Message) -> date:
    return (m.at - DAY_CUTOFF).date()


def days_table(week: list[Message], work: dict, monday: date, until: date) -> tuple[str, list[tuple[date, datetime]]]:
    """A row per day: its messages, its hours in and out of the window, its first and last message; and each active day's last."""
    rows: list[list[str]] = []
    lasts: list[tuple[date, datetime]] = []
    minutes = active_minutes(week)
    d = monday
    while d <= until:
        ms = [m for m in week if day_of(m) == d]
        mins = [t for t in minutes if (t - DAY_CUTOFF).date() == d]
        inside = sum(1 for t in mins if within(work, t))
        if ms:
            lasts.append((d, ms[-1].at))
        rows.append([
            d.strftime("%a %d"), str(len(ms)), str(sum(1 for m in ms if not m.inside)), f"{inside / 60:.1f}", f"{(len(mins) - inside) / 60:.1f}",
            clock(ms[0].at, d) if ms else "-", clock(ms[-1].at, d) if ms else "-",
        ])
        d += timedelta(days=1)
    return table(["Day", "Messages", "Off-window", "Hours in", "Hours out", "First", "Last"], rows), lasts


def folders_table(week: list[Message], watch: list[str], items: list[tuple[str, list[str]]] | None) -> str:
    by: dict[str, list[Message]] = {}
    for m in week:
        by.setdefault(m.folder, []).append(m)
    rows: list[list[str]] = []
    for folder, ms in sorted(by.items(), key=lambda kv: -len(kv[1])):
        off = sum(1 for m in ms if not m.inside)
        mark = " (watched)" if under(folder, watch) else ""
        rows.append([f"`{folder}`{mark}", ms[0].kind, focus_name(folder, items) or "-", str(len(ms)), str(off), share(off, len(ms))])
    for kind in ("work", "personal"):
        ms = [m for m in week if m.kind == kind]
        off = sum(1 for m in ms if not m.inside)
        rows.append([f"**{kind}**", kind, "", str(len(ms)), str(off), share(off, len(ms))])
    return table(["Folder", "Kind", "Focus", "Messages", "Off-window", "Share off"], rows)


def focus_section(week: list[Message], items: list[tuple[str, list[str]]] | None) -> str:
    if items is None:
        return "No focus list for this week."
    rows: list[list[str]] = []
    for name, folders in items:
        ms = [m for m in week if focus_name(m.folder, items) == name]
        off = sum(1 for m in ms if not m.inside)
        rows.append([name, ", ".join(f"`{f}`" for f in folders) or "-", str(len(ms)), str(off), share(len(ms), len(week))])
    rest = [m for m in week if focus_name(m.folder, items) is None]
    rows.append(["**off focus**", "", str(len(rest)), str(sum(1 for m in rest if not m.inside)), share(len(rest), len(week))])
    on = len(week) - len(rest)
    return f"{on} of {len(week)} messages on focus ({share(on, len(week))}).\n\n" + table(["Must-have", "Folders", "Messages", "Off-window", "Share of the week"], rows)


def holds_of(path: Path, start: datetime, end: datetime) -> list[dict]:
    if not path.is_file():
        return []
    found: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict) and isinstance(record.get("at"), (int, float)):
            at = datetime.fromtimestamp(record["at"] / 1000, timezone.utc)
            if start <= at < end:
                found.append(record | {"_at": at})
    return found


def holds_table(holds: list[dict], tz: ZoneInfo, home: str) -> str:
    if not holds:
        return "No prompt was held."
    rows = [[
        h["_at"].astimezone(tz).strftime("%a %H:%M"), f"`{folder_of(h.get('cwd'), home)}`", str(h.get("kind")), str(h.get("via")),
        str(h.get("outcome")), "-" if h.get("reason") is None else " ".join(str(h["reason"]).split()).replace("|", "\\|"),
    ] for h in holds]
    sent = sum(1 for h in holds if h.get("outcome") == "sent" and h.get("via") == "band")
    back = sum(1 for h in holds if h.get("outcome") == "returned")
    phone = sum(1 for h in holds if h.get("via") == "phone")
    return f"{table(['When', 'Folder', 'Kind', 'Via', 'Outcome', 'Reason'], rows)}\n\n{sent} sent with a reason, {back} put back in the box, {phone} from the phone with none."


def bar_section(bar: dict | None, week: list[Message], lasts: list[tuple[date, datetime]], monday: date, watch: list[str]) -> str:
    if not bar:
        return "No bar in the settings."
    live = date.fromisoformat(bar["live"])
    weeks = int(bar["weeks"])
    below = float(bar["offWindowBelow"])
    by = minute_of(bar["lastMessageBy"])
    # The week 2a went live in is week 0, and week 1 the first whole week after it.
    first_week = live + timedelta(days=7 - live.weekday())
    n = 0 if monday < first_week else (monday - first_week).days // 7 + 1
    off = sum(1 for m in week if not m.inside)
    off_share = off / len(week) if week else 0.0
    rest = [m for m in week if not under(m.folder, watch)]
    weekdays = [(d, at) for d, at in lasts if d.weekday() < 5]
    late = [d for d, at in weekdays if minute_of(clock(at, d)) > by]
    met_share = off_share < below
    met_late = len(late) * 2 <= len(weekdays)
    lines = [
        f"Agreed 2026-10-29, live since {live.isoformat()}: after {weeks} weeks, 2b rolls out if the off-window share is not below "
        f"{below:.0%}, or the last message is after {bar['lastMessageBy']} on most weekdays.",
        "",
        f"- Week {n} of {weeks}" + (" (the week 2a went live, not counted)" if n == 0 else "") + ".",
        f"- Off-window share: {share(off, len(week))} of {len(week)} messages, against below {below:.0%}: {'met' if met_share else 'not met'}."
        + (f" Without the watched folders: {share(sum(1 for m in rest if not m.inside), len(rest))} of {len(rest)}." if watch else ""),
        f"- Weekdays whose last message came after {bar['lastMessageBy']}: {len(late)} of {len(weekdays)}: {'met' if met_late else 'not met'}.",
        f"- Baseline, {BASELINE}",
    ]
    if n >= weeks:
        verdict = "met: 2b stays parked." if met_share and met_late else "not met: 2b rolls out, and its objectives go to the kit session with no new vote."
        lines += ["", f"**Verdict, week {n}: the bar is {verdict}**"]
    return "\n".join(lines)


def report(sessions: list[Session], settings: dict, load_dir: Path, as_of: date, home: str) -> str:
    tz = ZoneInfo(settings["timeZone"])
    watch = [w.rstrip("/") for w in settings.get("watch", [])]
    everything = messages_of(sessions, settings, home)
    monday = as_of - timedelta(days=as_of.weekday())
    start = datetime(monday.year, monday.month, monday.day, tzinfo=tz) + DAY_CUTOFF
    end = datetime(as_of.year, as_of.month, as_of.day, tzinfo=tz) + timedelta(days=1) + DAY_CUTOFF
    week = [m for m in everything if start <= m.at < end]
    days, lasts = days_table(week, settings["work"], monday, as_of)
    off = sum(1 for m in week if not m.inside)
    items = focus_list(load_dir, monday, home)
    return "\n".join([
        f"# The week of {monday.isoformat()}, to {as_of.isoformat()}",
        "",
        f"Written by `session-transcripts week` for the owner alone. Times in {settings['timeZone']}. A day runs from 04:00 to 04:00. "
        "Hours are the time between messages twenty minutes or less apart, and a minute for each message. "
        "The window is the work hours, so a message in the personal slot counts as off-window.",
        "",
        f"{len(week)} messages, {off} of them off-window ({share(off, len(week))}). Streak: {streak(everything, as_of)} days. "
        f"Sittings reopened within an hour of the window closing: {reopened(week, settings)}.",
        "",
        "## Days",
        "",
        days,
        "",
        "## Folders",
        "",
        folders_table(week, watch, items),
        "",
        "## Focus",
        "",
        focus_section(week, items),
        "",
        "## Reasons",
        "",
        holds_table(holds_of(load_dir / "holds.jsonl", start, end), tz, home),
        "",
        "## The 2b bar",
        "",
        bar_section(settings.get("bar"), week, lasts, monday, watch),
        "",
    ])


def write(sessions: list[Session], load_dir: Path, as_of: date, home: str) -> int:
    """Writes the review beside the settings and prints its path alone."""
    settings_path = load_dir / "settings.json"
    if not settings_path.is_file():
        print(f"{settings_path}: no settings, so there is no window to read the week against")
        return 2
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    monday = as_of - timedelta(days=as_of.weekday())
    out = load_dir / f"week-{monday.isoformat()}.md"
    out.write_text(report(sessions, settings, load_dir, as_of, home), encoding="utf-8")
    print(out)
    return 0
