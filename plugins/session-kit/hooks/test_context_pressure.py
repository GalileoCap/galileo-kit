"""Cases for context_pressure.py. Run it: python3 .claude/hooks/test_context_pressure.py

Each case plants a transcript whose last assistant message carries a context
size and a reply, hands the hook the payload Claude Code sends, and reads what
it answers. The hook keeps its warning state in the temporary directory, so
every case runs with its own.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = str(Path(__file__).with_name("context_pressure.py"))


def transcript(folder: Path, tokens: int, reply: str) -> str:
    path = folder / "session.jsonl"
    line = {
        "type": "assistant",
        "message": {
            "usage": {
                "input_tokens": 10,
                "cache_read_input_tokens": tokens - 10,
                "cache_creation_input_tokens": 0,
            },
            "content": [{"type": "text", "text": reply}],
        },
    }
    path.write_text(json.dumps(line) + "\n", encoding="utf-8")
    return str(path)


def run(
    event: str, tokens: int, reply: str = "Done.", warned_at: int = 0, **extra: object
) -> str:
    """What the hook prints for one event, empty when it says nothing.

    ``warned_at`` plants the state a earlier warning left in the session.
    """
    with tempfile.TemporaryDirectory() as folder:
        if warned_at:
            Path(folder, "claude-kit-ctx-case-case.json").write_text(
                json.dumps({"warned_at": warned_at}), encoding="utf-8"
            )
        payload = {
            "hook_event_name": event,
            "session_id": "case",
            "transcript_path": transcript(Path(folder), tokens, reply),
            **extra,
        }
        args = [sys.executable, HOOK]
        env = {**os.environ, "TMPDIR": folder, "CLAUDE_PROJECT_DIR": "/somewhere/case"}
        return subprocess.run(
            args, input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=30
        ).stdout.strip()


def field(out: str, *keys: str) -> str:
    """The string at ``keys`` in the hook's answer, or an empty one."""
    try:
        value = json.loads(out)
        for key in keys:
            value = value[key]
    except (ValueError, KeyError, TypeError):
        return ""
    return value if isinstance(value, str) else ""


CASES: list[tuple[str, bool]] = []


def case(name: str, ok: bool) -> None:
    CASES.append((name, ok))


# The end of a turn is never held. The warnings during it are the signal.
WIRING = json.loads((Path(HOOK).parent / "hooks.json").read_text())["hooks"]
case(
    "no Stop hook runs the context check",
    not any("context_pressure" in h["command"] for m in WIRING.get("Stop", []) for h in m["hooks"]),
)

# In the middle of a turn.
case("a tool call under half the window says nothing", run("PostToolUse", 400_000) == "")
advice = field(run("PostToolUse", 700_000), "hookSpecificOutput", "additionalContext")
case("past 65% the advice is to end the turn", "end this turn" in advice.lower())

# The state a warning leaves behind.
case(
    "a second tool call within a step of the last warning says nothing",
    run("PostToolUse", 710_000, warned_at=700_000) == "",
)
case(
    "a tool call a step past the last warning warns again",
    run("PostToolUse", 730_000, warned_at=700_000) != "",
)
case(
    "a context compacted below the last warning warns afresh once over half",
    run("PostToolUse", 520_000, warned_at=850_000) != "",
)


failed = [name for name, ok in CASES if not ok]
for name, ok in CASES:
    print(("ok    " if ok else "FAIL  ") + name)
print(f"{len(CASES) - len(failed)} passed, {len(failed)} failed")
sys.exit(1 if failed else 0)
