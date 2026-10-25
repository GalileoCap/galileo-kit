"""Cases for session_transcripts.py. Run it: python3 transcripts/test_session_transcripts.py

Each case builds a projects root of made-up transcripts in a temporary
directory, runs the command over it and reads its lines. No real transcript
is read.
"""

from __future__ import annotations

import io
import json
import subprocess
import tarfile
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOOL = str(Path(__file__).with_name("session_transcripts.py"))
T0 = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)


def stamp(minutes: float) -> str:
    return (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def prompt(text: str, minutes: float, session: str, uuid: str | None = None, origin: dict | None = None) -> dict:
    record = {"type": "user", "isSidechain": False, "message": {"role": "user", "content": [{"type": "text", "text": text}]},
              "timestamp": stamp(minutes), "sessionId": session, "uuid": uuid or f"u{minutes}"}
    return record | ({"origin": origin} if origin else {})


def summary(minutes: float, session: str) -> dict:
    """The summary a compaction leaves, which the engine writes as a user record with string content."""
    return {"type": "user", "isSidechain": False, "isCompactSummary": True, "timestamp": stamp(minutes), "sessionId": session,
            "uuid": f"s{minutes}", "message": {"role": "user", "content": "This session is being continued from a previous conversation."}}


def request(minutes: float, session: str, *, read: int, created: int, fresh: int = 100, out: int = 500, block: dict | None = None, rid: str | None = None) -> dict:
    return {"type": "assistant", "isSidechain": False, "requestId": rid or f"req{minutes}", "timestamp": stamp(minutes), "sessionId": session,
            "message": {"role": "assistant", "model": "claude-fable-5-1", "content": [block or {"type": "text", "text": "an answer"}],
                        "usage": {"input_tokens": fresh, "cache_read_input_tokens": read, "cache_creation_input_tokens": created, "output_tokens": out}}}


def tool_use(name: str, inp: dict) -> dict:
    return {"type": "tool_use", "id": "toolu_1", "name": name, "input": inp}


def warning(minutes: float, session: str, tokens: int, percent: int) -> dict:
    text = f"Context at {tokens:,} tokens ({percent}% of 1,000,000). Aim for a safe point."
    return {"type": "attachment", "isSidechain": False, "timestamp": stamp(minutes), "sessionId": session,
            "attachment": {"type": "hook_additional_context", "hookName": "PostToolUse", "content": "", "stdout": json.dumps({"hookSpecificOutput": {"additionalContext": text}})}}


def hook(minutes: float, session: str, name: str, stdout: str) -> dict:
    return {"type": "attachment", "isSidechain": False, "timestamp": stamp(minutes), "sessionId": session,
            "attachment": {"type": "hook_success", "hookName": name, "content": "", "stdout": stdout}}


def compaction(minutes: float, session: str, pre: int, trigger: str = "manual") -> dict:
    return {"type": "system", "subtype": "compact_boundary", "isSidechain": False, "timestamp": stamp(minutes), "sessionId": session,
            "uuid": f"c{minutes}", "compactMetadata": {"trigger": trigger, "preTokens": pre, "durationMs": 40000}}


def cost(session: str, usd: float, start: int | None = None) -> dict:
    """The engine's cost state: a running total, which a clear may carry on and a fork does."""
    return {"type": "cost-state", "sessionId": session, "totalCostUSD": usd, "totalLinesAdded": 10, "totalLinesRemoved": 2,
            "modelUsage": {"claude-fable-5-1": {"inputTokens": 1, "outputTokens": 2, "cacheReadInputTokens": 3, "cacheCreationInputTokens": 4, "costUSD": usd}}} | (
            {"startTime": start} if start else {})


# Session A: the context grows, a warning fires, the handoff and a commit follow a turn later, then a compaction.
A = "aaaaaaaa-0000-0000-0000-000000000001"
SESSION_A = [
    prompt("Start the task about the widget", 0, A),
    request(1, A, read=0, created=100_000),
    request(2, A, read=100_000, created=300_000),
    prompt("Keep going", 3, A),
    request(4, A, read=400_000, created=150_000, block=tool_use("Bash", {"command": "ls"})),
    warning(4.5, A, 550_000, 55),
    request(5, A, read=550_000, created=20_000),
    prompt("Ok, wrap up", 6, A),
    request(7, A, read=570_000, created=5_000, block=tool_use("Write", {"file_path": "/proj/CLAUDE.local.md", "content": "state"})),
    request(8, A, read=575_000, created=2_000, block=tool_use("Bash", {"command": "git add -A && git commit -m done"})),
    hook(8.5, A, "PostToolUse:Bash", json.dumps({"hookSpecificOutput": {"additionalContext": "Banned prose tells in what this edit wrote"}})),
    compaction(9, A, 580_000),
    prompt("Continue", 10, A),
    request(11, A, read=0, created=60_000),
    cost(A, 3.5),
]

# Session B: one warning nothing follows, and a cold send after a long gap.
B = "bbbbbbbb-0000-0000-0000-000000000002"
SESSION_B = [
    prompt("Another project's task", 0, B),
    request(1, B, read=0, created=200_000),
    request(2, B, read=200_000, created=1_000),
    warning(2.5, B, 520_000, 52),
    request(3, B, read=201_000, created=500),
    prompt("After lunch", 90, B),
    request(91, B, read=0, created=202_000),
    request(92, B, read=202_000, created=300),
    cost(B, 1.25),
]


# Sessions D, F and E share one running cost, as their cost states' start says. F is a fork of D: its file
# begins with a copy of D's first records, under D's id. E came after D ended. D's first prompt is
# written twice, as the engine does, and is one prompt.
D = "dddddddd-0000-0000-0000-000000000004"
E = "eeeeeeee-0000-0000-0000-000000000005"
F = "ffffffff-0000-0000-0000-000000000006"
S1 = 1790000000000
D_HEAD = [
    prompt("Draft the plan for the parser", 0, D, uuid="d1"),
    prompt("Draft the plan for the parser", 0, D, uuid="d1"),
    request(1, D, read=0, created=40_000, rid="rd1"),
    cost(D, 1.0, start=S1),
]
SESSION_D = D_HEAD + [
    prompt("Now the lexer", 10, D, uuid="d2"),
    request(11, D, read=40_000, created=5_000, rid="rd2"),
    request(20, D, read=45_000, created=1_000, rid="rd3"),
    cost(D, 2.0, start=S1),
]
SESSION_F = D_HEAD + [
    prompt("Try the other grammar", 5, F, uuid="f1"),
    request(6, F, read=40_000, created=2_000, rid="rf1"),
    cost(F, 1.25, start=S1),
]
SESSION_E = [
    prompt("Then the evaluator", 21, E, uuid="e1"),
    request(22, E, read=0, created=30_000, rid="re1"),
    cost(E, 3.5, start=S1),
]

# Session K: a fork of A that has no record of its own yet but its cost state, so it started at no known time.
K = "66666666-0000-0000-0000-00000000000c"
SESSION_K = [SESSION_A[0], cost(K, 3.5)]

# Sessions G and H: a clear that started a new cost, which only the kit's timeline records.
G = "11111111-0000-0000-0000-000000000007"
H = "22222222-0000-0000-0000-000000000008"
SESSION_G = [prompt("Sketch the cache layer", 30, G, uuid="g1"), request(31, G, read=0, created=20_000, rid="rg1")]
SESSION_H = [prompt("Write the cache tests", 40, H, uuid="h1"), request(41, H, read=0, created=20_000, rid="rh1")]

# Session W: its compaction's record is written twice, as the engine writes again what a compaction
# keeps, and the summary the compaction left is a user record with string content.
W = "33333333-0000-0000-0000-000000000009"
SESSION_W = [
    prompt("Look at the notes", 50, W, uuid="w1"),
    request(51, W, read=0, created=10_000, rid="rw1"),
    compaction(57, W, 200_000, trigger="auto"),
    summary(57.5, W),
    compaction(57, W, 200_000, trigger="auto"),
    request(58, W, read=0, created=8_000, rid="rw2"),
]

# Sessions X1 and X2: the person asks to commit and push three times over two sessions (a record written
# twice and a plugin's or a notification's prompt of the same words are not the person's asks), and to
# take the handoff's next step twice in near words.
X1 = "44444444-0000-0000-0000-00000000000a"
X2 = "55555555-0000-0000-0000-00000000000b"
SESSION_X1 = [
    prompt("commit and push", 70, X1, uuid="x1a"),
    prompt("commit and push", 70, X1, uuid="x1a"),
    request(71, X1, read=0, created=9_000, rid="rx1"),
    prompt("Commit and push!", 72, X1, uuid="x1b"),
    prompt("commit and push", 73, X1, uuid="x1c", origin={"kind": "plugin", "name": "session-kit"}),
    prompt("commit and push", 74, X1, uuid="x1d", origin={"kind": "task-notification"}),
    prompt("read the handoff and take its next step without asking", 75, X1, uuid="x1e"),
]
SESSION_X2 = [
    prompt("commit and push", 80, X2, uuid="x2a"),
    prompt("read the handoff and take the next step without asking", 81, X2, uuid="x2b"),
    prompt("tidy the readme", 82, X2, uuid="x2c"),
]


def projects(root: Path) -> None:
    for folder, session, rows in [
        ("-Users-me-proj-a", A, SESSION_A), ("-Users-me-proj-b", B, SESSION_B),
        ("-Users-me-proj-d", D, SESSION_D), ("-Users-me-proj-d", E, SESSION_E), ("-Users-me-proj-d", F, SESSION_F),
        ("-Users-me-proj-g", G, SESSION_G), ("-Users-me-proj-g", H, SESSION_H),
        ("-Users-me-proj-k", K, SESSION_K), ("-Users-me-proj-w", W, SESSION_W), ("-Users-me-proj-x", X1, SESSION_X1), ("-Users-me-proj-x", X2, SESSION_X2),
    ]:
        d = root / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{session}.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def timeline(measure: Path) -> None:
    """H's first timeline file opens with the line the kit writes after a clear, naming G."""
    d = measure / H
    d.mkdir(parents=True)
    lines = [{"at": 1792000000000, "ev": "session", "from": G, "reason": "clear"}, {"at": 1792000000001, "ev": "turn.start", "turn": "t1"}]
    (d / "1792000000500.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")


NO_TIMELINE = Path(tempfile.mkdtemp(prefix="session-transcripts-measure-"))


def run(root: Path, *args: str, measure: Path = NO_TIMELINE) -> tuple[int, str]:
    out = subprocess.run([sys.executable, TOOL, *args, "--root", str(root), "--measure-dir", str(measure)], capture_output=True, text=True, timeout=30)
    return out.returncode, out.stdout + out.stderr


failures: list[str] = []


def case(name: str, ok: bool, detail: str = "") -> None:
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        failures.append(name + ("\n" + detail if detail else ""))


root = Path(tempfile.mkdtemp(prefix="session-transcripts-"))
projects(root)

code, out = run(root, "list")
case("list exits 0 with one row per session", code == 0 and out.count("aaaaaaaa") == 1 and out.count("bbbbbbbb") == 1, out)
row_a = next((l for l in out.splitlines() if "aaaaaaaa" in l), "")
case("a row carries the project, the prompts, the requests, the compactions and the cost", all(x in row_a for x in ["proj-a", "| 4 |", "| 7 |", "| 1 |", "3.50"]), row_a)

code, out = run(root, "warnings")
case("warnings lists each warning with its tokens and percent", code == 0 and "550,000" in out and "55%" in out and "520,000" in out, out)
row = next((l for l in out.splitlines() if "550,000" in l), "")
case("a warning that was followed says how many turns later the handoff, the commit and the compaction came",
     "handoff 1" in row and "commit 1" in row and "compaction 1" in row, row)
row = next((l for l in out.splitlines() if "520,000" in l), "")
case("a warning nothing followed says so", row.count("none") == 3, row)
case("warnings ends with the count followed by a handoff", "1 of 2" in out, out)

code, out = run(root, "cache")
case("cache gives each session's share of input read from cache", code == 0 and "aaaaaaaa" in out and "%" in out, out)
row_b = next((l for l in out.splitlines() if "bbbbbbbb" in l), "")
case("a request after a long gap that wrote the context again is a cold send", "| 1 |" in row_b and "202,000" in row_b, row_b)
row_a = next((l for l in out.splitlines() if "aaaaaaaa" in l), "")
case("a session without such a gap has no cold send", "| 0 |" in row_a, row_a)
case("cache sums per project too", "proj-a" in out and "proj-b" in out, out)

code, out = run(root, "session", A)
case("session shows the context at each request and the compaction", code == 0 and "575,000" in out and "compaction" in out.lower() and "580,000" in out, out)
case("session prints no prompt text", "widget" not in out and "wrap up" not in out, out)

code, out = run(root, "compactions")
case("compactions counts by trigger with the context before", code == 0 and "| manual | 1 |" in out and "580,000" in out, out)

code, out = run(root, "hooks")
case("hooks counts each settings hook's fires by name", code == 0 and "PostToolUse:Bash" in out and "| 1 |" in out, out)

code, out = run(root, "list", "--since", "2026-10-21")
case("--since drops the sessions that started before it", code == 0 and "aaaaaaaa" not in out, out)
code, out = run(root, "list", "--project", "proj-b")
case("--project keeps one project's sessions", code == 0 and "aaaaaaaa" not in out and "bbbbbbbb" in out, out)


def cells(out: str, first: str) -> list[str]:
    """The cells of the table row whose first cell is `first`, or none."""
    for line in out.splitlines():
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if parts and parts[0] == first:
            return parts
    return []


# Regressions: the engine writes a record more than once, its compaction summaries as user records
# with string content, a fork's file with a copy of its parent's records, and a cost state that runs on
# from the session before it.
code, out = run(root, "list")
case("a record the engine wrote twice is counted once, a prompt or a compaction",
     cells(out, "dddddddd")[3:5] == ["2", "3"] and cells(out, "33333333")[7:8] == ["1"], out)
case("a compaction's summary is not a prompt", cells(out, "33333333")[3:4] == ["1"], out)
case("a fork's copy of its parent's records is counted in the parent alone", cells(out, "ffffffff")[3:5] == ["1", "1"], out)
case("a session's cost is its own, the total carried from the session before it taken out",
     [cells(out, s)[8:9] for s in ("dddddddd", "ffffffff", "eeeeeeee")] == [["2.00"], ["0.25"], ["1.50"]], out)

code, out = run(root, "chains")
case("a fork with no record of its own comes after its parent", cells(out, "aaaaaaaa")[1:2] == ["2"] and cells(out, "aaaaaaaa")[9:] == ["fork 1"], out)

# The contract with session-kit's timeline (A55): after a clear, the new session's first file opens with
# a line naming the session before it, which joins the two.
measure = Path(tempfile.mkdtemp(prefix="session-transcripts-measure-"))
timeline(measure)
code, out = run(root, "chains", measure=measure)
row = cells(out, "11111111")
case("the timeline's session line joins the session a clear started to the one before it", row[1:2] == ["2"] and "clear 1" in row[9], out)

# The asks are the person's own words: ranked, and none of them printed without --quote.
code, out = run(root, "asks")
case("asks ranks the person's repeated asks and prints none of their words without --quote",
     code == 0 and cells(out, "1")[1:3] == ["3", "2"] and cells(out, "2")[1:3] == ["2", "2"]
     and "commit" not in out.lower() and "handoff" not in out and "readme" not in out, out)

report = root / "report.md"
code, out = run(root, "report", "--out", str(report))
text = report.read_text(encoding="utf-8") if report.exists() else ""
case("report writes the sessions, warnings, cache, compactions, chains and waste tables to the file",
     code == 0 and all(h in text for h in ["## Sessions", "## Warnings", "## Cache", "## Compactions", "## Chains", "## Waste"]), out + text[:400])
case("the report sums the warnings per session", "2 warnings over 2 sessions" in text and "| 1 | 550,000 | 1 | 1 | 1 | 1 |" in text and "| 1 | 520,000 | 0 | 0 | 0 | none |" in text, text)
case("the report holds no prompt text", all(t not in text for t in ["widget", "After lunch", "commit and push", "parser"]), text)

# An archive of sessions is read beside the live ones: each `<project>/<id>.tar.xz` holds the session's
# jsonl under projects/, and an id present in both is read once, from the live file.
archive = Path(tempfile.mkdtemp(prefix="session-transcripts-archive-"))
C = "cccccccc-0000-0000-0000-000000000003"
lines = [prompt("Archived prompt", 0, C), request(1, C, read=0, created=50_000), request(2, C, read=50_000, created=100, rid="r-c")]
body = "\n".join(json.dumps(x) for x in lines).encode("utf-8") + b"\n"
(archive / "proj-c").mkdir()
with tarfile.open(archive / "proj-c" / f"{C}.tar.xz", "w:xz") as tar:
    info = tarfile.TarInfo(f"projects/proj-c/{C}.jsonl"); info.size = len(body)
    tar.addfile(info, io.BytesIO(body))
    sub = b'{"type":"user"}\n'
    info = tarfile.TarInfo(f"projects/proj-c/{C}/subagents/agent-1.jsonl"); info.size = len(sub)
    tar.addfile(info, io.BytesIO(sub))
(archive / "proj-a").mkdir()
with tarfile.open(archive / "proj-a" / f"{A}.tar.xz", "w:xz") as tar:
    info = tarfile.TarInfo(f"projects/proj-a/{A}.jsonl"); info.size = len(body)
    tar.addfile(info, io.BytesIO(body))
code, out = run(root, "list", "--archive", str(archive))
case("an archived session is listed beside the live ones", code == 0 and "cccccccc" in out and "proj-c" in out, out)
case("the archived session's requests are counted from its main jsonl alone", "| 2 |" in [l for l in out.splitlines() if "cccccccc" in l][0], out)
case("a session both live and archived is read once, from the live file", out.count("aaaaaaaa") == 1 and "| 7 |" in [l for l in out.splitlines() if "aaaaaaaa" in l][0], out)
case("an archived session prints no prompt text", "Archived prompt" not in out, out)

if failures:
    print(f"\n{len(failures)} failed")
    for f in failures:
        print(f)
    sys.exit(1)
print("\nall passed")
