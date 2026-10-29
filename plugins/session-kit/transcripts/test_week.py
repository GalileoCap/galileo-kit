"""Cases for ``session-transcripts week``. Run it: python3 transcripts/test_week.py

The review decides whether 2b rolls out, and no session may read its
figures (C5): a wrong verdict, or a figure on stdout, would go unseen. Each
case builds made-up transcripts and a load folder in a temporary directory.
No real transcript is read.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOOL = str(Path(__file__).with_name("session_transcripts.py"))
HOME = str(Path.home())
LANE = f"{HOME}/devel/iquall/tagents/lane5"
KIT = f"{HOME}/devel/galileo/misc/galileo-kit"
BRAIN = f"{HOME}/devel/galileo/brain-dumping"
# Buenos Aires is UTC-3 all year.
LOCAL = timezone(timedelta(hours=-3))

SETTINGS = {
    "timeZone": "America/Argentina/Buenos_Aires",
    "work": {"days": ["mon", "tue", "wed", "thu", "fri"], "hours": ["06:00-11:00", "15:00-17:00"]},
    "personal": {"days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"], "hours": ["05:30-22:00"], "folders": ["~/devel/galileo"]},
    "passMinutes": 30,
    "watch": ["~/devel/galileo/misc/galileo-kit"],
    "bar": {"live": "2026-10-29", "weeks": 4, "offWindowBelow": 0.40, "lastMessageBy": "22:00"},
}


def at(day: int, hhmm: str) -> datetime:
    h, m = hhmm.split(":")
    return datetime(2026, 11, day, int(h), int(m), tzinfo=LOCAL)


def prompt(when: datetime, cwd: str, text: str, n: int) -> dict:
    return {"type": "user", "isSidechain": False, "origin": {"kind": "human"}, "cwd": cwd, "sessionId": "s1", "uuid": f"u{n}",
            "timestamp": when.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"), "message": {"role": "user", "content": text}}


def run(prompts: list[tuple[datetime, str, str]], holds: list[dict], as_of: str, focus: dict[str, str] | None = None) -> tuple[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "projects" / "-p"
        root.mkdir(parents=True)
        (root / "s1.jsonl").write_text("\n".join(json.dumps(prompt(w, c, t, i)) for i, (w, c, t) in enumerate(prompts)) + "\n")
        load = Path(tmp) / "load"
        load.mkdir()
        (load / "settings.json").write_text(json.dumps(SETTINGS))
        (load / "holds.jsonl").write_text("".join(json.dumps(h) + "\n" for h in holds))
        for name, text in (focus or {}).items():
            (Path(tmp) / name).write_text(text)
        out = subprocess.run([sys.executable, TOOL, "week", "--root", str(Path(tmp) / "projects"), "--load-dir", str(load),
                              "--measure-dir", str(Path(tmp) / "none"), "--week", as_of], capture_output=True, text=True, timeout=10)
        assert out.returncode == 0, out.stderr
        day = datetime.fromisoformat(as_of).date()
        return out.stdout, (load / f"week-{day - timedelta(days=day.weekday())}.md").read_text()


def test_week_four_gives_the_verdict_from_the_weeks_figures_and_prints_only_the_path() -> None:
    prompts = [
        (at(22, "10:00"), LANE, "sunday work"),
        (at(23, "09:00"), LANE, "merge lane5"),
        (at(23, "19:00"), LANE, "and push"),
        (at(23, "21:00"), BRAIN, "a note"),
        (at(23, "23:30"), KIT, "kit at night"),
        (at(23, "23:31"), KIT, "kit at night"),
        (at(24, "10:00"), LANE, "tuesday work"),
    ]
    holds = [
        {"at": int(at(23, "19:00").timestamp() * 1000), "session": "s1", "cwd": LANE, "kind": "work", "reason": "the demo | tomorrow", "via": "band", "outcome": "sent"},
        {"at": int(at(20, "19:00").timestamp() * 1000), "session": "s1", "cwd": LANE, "kind": "work", "reason": "last week", "via": "band", "outcome": "sent"},
    ]
    # Value metrics was lane5's must-have until Tuesday morning, when the owner dropped it from the list.
    tagged = [(at(23, "08:59"), "value metrics (O18)"), (at(24, "09:59"), None)]
    focus = {
        "load/focus-2026-11-23.md": "# Week of 2026-11-23\n\n- the MAT demo ~/devel/iquall/demo-mat-porting\n",
        "load/prompts-2026-11-23.jsonl": "".join(json.dumps({"at": int(w.timestamp() * 1000), "session": "s1", "cwd": LANE, "focus": f}) + "\n" for w, f in tagged),
    }
    stdout, review = run(prompts, holds, "2026-11-27", focus)

    assert stdout.strip().endswith("load/week-2026-11-23.md") and "\n" not in stdout.strip(), stdout
    # The same text again within two minutes is one message: five in the week, three off the window.
    assert "5 messages, 3 of them off-window (60%)" in review, review
    assert "Streak: 0 days" in review, review
    assert "Week 4 of 4" in review, review
    assert "Off-window share: 60% of 5 messages, against below 40%: not met" in review, review
    assert "Without the watched folders: 50% of 4" in review, review
    assert "after 22:00: 1 of 2: met" in review, review
    assert "the bar is not met: 2b rolls out" in review, review
    assert "| `~/devel/galileo/misc/galileo-kit` (watched) | personal | - | 1 | 1 | 100% |" in review, review
    # Each message keeps the tag it went on with: lane5's Monday two on focus, its Tuesday one off.
    assert "2 of 5 messages on focus (40%)" in review, review
    assert "| value metrics (O18) | - | 2 | 1 | 40% |" in review, review
    assert "| `~/devel/iquall/tagents/lane5` | work | value metrics (O18) | 3 | 1 | 33% |" in review, review
    assert "| Mon 23 | 4 | 3 |" in review and "| 09:00 | 23:30 |" in review, review
    assert "the demo \\| tomorrow" in review and "last week" not in review, review


def test_before_its_weeks_are_up_the_bar_gives_no_verdict_and_a_list_of_another_week_is_no_focus_list() -> None:
    _, review = run([(at(3, "09:00"), LANE, "work")], [], "2026-11-06", {"focus.md": "# Week of 2026-10-26\n\n- lane5 ~/devel/iquall/tagents/lane5\n"})
    assert "Week 1 of 4" in review and "Verdict" not in review, review
    assert "No focus list for this week." in review, review


if __name__ == "__main__":
    for name, case in list(globals().items()):
        if name.startswith("test_"):
            case()
            print(f"ok {name}")
