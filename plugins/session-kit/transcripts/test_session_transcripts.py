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


def prompt(text: str, minutes: float, session: str) -> dict:
    return {"type": "user", "isSidechain": False, "message": {"role": "user", "content": [{"type": "text", "text": text}]},
            "timestamp": stamp(minutes), "sessionId": session, "uuid": f"u{minutes}"}


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
            "compactMetadata": {"trigger": trigger, "preTokens": pre, "durationMs": 40000}}


def cost(session: str, usd: float) -> dict:
    return {"type": "cost-state", "sessionId": session, "totalCostUSD": usd, "totalLinesAdded": 10, "totalLinesRemoved": 2,
            "modelUsage": {"claude-fable-5-1": {"inputTokens": 1, "outputTokens": 2, "cacheReadInputTokens": 3, "cacheCreationInputTokens": 4, "costUSD": usd}}}


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


def projects(root: Path) -> None:
    for folder, session, rows in [("-Users-me-proj-a", A, SESSION_A), ("-Users-me-proj-b", B, SESSION_B)]:
        d = root / folder
        d.mkdir(parents=True)
        (d / f"{session}.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def run(root: Path, *args: str) -> tuple[int, str]:
    out = subprocess.run([sys.executable, TOOL, *args, "--root", str(root)], capture_output=True, text=True, timeout=30)
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

report = root / "report.md"
code, out = run(root, "report", "--out", str(report))
text = report.read_text(encoding="utf-8") if report.exists() else ""
case("report writes the sessions, warnings, cache and compactions tables to the file", code == 0 and all(h in text for h in ["## Sessions", "## Warnings", "## Cache", "## Compactions"]), out + text[:400])
case("the report sums the warnings per session", "2 warnings over 2 sessions" in text and "| 1 | 550,000 | 1 | 1 | 1 | 1 |" in text and "| 1 | 520,000 | 0 | 0 | 0 | none |" in text, text)
case("the report holds no prompt text", "widget" not in text and "After lunch" not in text, text)

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
