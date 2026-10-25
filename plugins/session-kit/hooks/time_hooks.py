"""Time every command in hooks.json as the engine runs it, one payload each.

The figure the port is measured by: what the settings hooks add to a tool
call today, and what is left once a hooks module takes a concern over.
Each command runs through ``bash -c`` exactly as ``hooks.json`` spells it,
with the plugin's environment variables set and a payload of its event on
stdin, so the shell wrapper and the interpreter start are both counted.

    python3 hooks/time_hooks.py [--runs N] [--out FILE]

``CLAUDE_PLUGIN_ROOT`` defaults to this plugin's directory, and
``CLAUDE_PLUGIN_DATA`` to the installed plugin's data directory when it
exists, so ``uv run`` finds a built environment. The first run of each
command is a warm-up and is discarded.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
DATA_DEFAULT = Path.home() / ".claude/plugins/data/session-kit-galileo-kit"


def transcript(folder: Path) -> Path:
    """A transcript whose tail holds one assistant usage line, 300 kB long."""
    path = folder / "transcript.jsonl"
    filler = json.dumps({"type": "user", "message": {"content": "x" * 120}})
    lines = [filler] * 2500
    lines.append(json.dumps({
        "type": "assistant",
        "message": {"usage": {"input_tokens": 400000, "cache_read_input_tokens": 200000}},
    }))
    path.write_text("\n".join(lines) + "\n")
    return path


def payloads(folder: Path, transcript_path: Path) -> dict[str, dict]:
    base = {
        "session_id": "timing",
        "transcript_path": str(transcript_path),
        "cwd": str(folder),
    }
    doc = folder / "docs" / "note.md"
    doc.parent.mkdir(exist_ok=True)
    doc.write_text("# note\n\nA line.\n")
    return {
        "PreToolUse:Bash": {**base, "hook_event_name": "PreToolUse", "tool_name": "Bash",
                            "tool_input": {"command": "ls"}},
        "PostToolUse:Bash": {**base, "hook_event_name": "PostToolUse", "tool_name": "Bash",
                             "tool_input": {"command": "ls"},
                             "tool_response": {"stdout": "a\n", "stderr": ""}},
        "PostToolUse:Edit": {**base, "hook_event_name": "PostToolUse", "tool_name": "Edit",
                             "tool_input": {"file_path": str(doc), "old_string": "A", "new_string": "B"},
                             "tool_response": {"filePath": str(doc)}},
        "PostToolUse:*": {**base, "hook_event_name": "PostToolUse", "tool_name": "Read",
                          "tool_input": {"file_path": str(doc)}, "tool_response": {}},
    }


def commands(hooks_json: Path) -> list[tuple[str, str, str]]:
    """(event, matcher, command) for every command hook, in file order."""
    found = []
    for event, groups in json.loads(hooks_json.read_text())["hooks"].items():
        for group in groups:
            for hook in group["hooks"]:
                if hook.get("type") == "command":
                    found.append((event, group.get("matcher", ""), hook["command"]))
    return found


def payload_for(event: str, matcher: str, table: dict[str, dict]) -> dict | None:
    if event == "PreToolUse" and "Bash" in matcher:
        return table["PreToolUse:Bash"]
    if event == "PostToolUse" and matcher == "*":
        return table["PostToolUse:*"]
    if event == "PostToolUse" and matcher == "Bash":
        return table["PostToolUse:Bash"]
    if event == "PostToolUse" and "Edit" in matcher:
        return table["PostToolUse:Edit"]
    return None


def time_once(command: str, payload: dict, env: dict[str, str]) -> float:
    start = time.perf_counter()
    subprocess.run(["bash", "-c", command], input=json.dumps(payload), text=True,
                   capture_output=True, env=env, check=False)
    return (time.perf_counter() - start) * 1000


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or PLUGIN)
    data = os.environ.get("CLAUDE_PLUGIN_DATA") or (str(DATA_DEFAULT) if DATA_DEFAULT.exists() else "")
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(root)}
    if data:
        env["CLAUDE_PLUGIN_DATA"] = data

    with tempfile.TemporaryDirectory(prefix="claude-kit-time-hooks-") as tmp:
        folder = Path(tmp)
        env["CLAUDE_PROJECT_DIR"] = str(folder)
        table = payloads(folder, transcript(folder))
        rows = []
        baseline = [time_once("python3 -c pass", {}, env) for _ in range(args.runs + 1)][1:]
        rows.append(("baseline", "", "python3 -c pass", statistics.median(baseline), min(baseline)))
        for event, matcher, command in commands(root / "hooks" / "hooks.json"):
            payload = payload_for(event, matcher, table)
            if payload is None:
                continue
            samples = [time_once(command, payload, env) for _ in range(args.runs + 1)][1:]
            rows.append((event, matcher, command, statistics.median(samples), min(samples)))

    lines = [f"Runs per command: {args.runs}, the first discarded. Root: {root}", "",
             "| Event | Matcher | Command | Median ms | Min ms |", "| --- | --- | --- | --- | --- |"]
    for event, matcher, command, med, low in rows:
        short = command if len(command) <= 60 else command[:57] + "..."
        short = short.replace("|", "\\|")
        lines.append(f"| {event} | {matcher} | `{short}` | {med:.0f} | {low:.0f} |")
    text = "\n".join(lines) + "\n"
    if args.out:
        args.out.write_text(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
