"""PostToolUse (Edit, Write, Bash): format the files an edit wrote, with the
project's own formatters, and say what lint the fix could not clear.

The tools are chosen by what the project has, never assumed:

- Python (``.py``, ``.pyi``): ruff, when a ``ruff.toml`` or ``.ruff.toml`` sits in
  the nearest directory up from the file that holds one of them or a
  ``pyproject.toml``, or that ``pyproject.toml`` has a ``[tool.ruff`` table. Run
  as ``uv run ruff`` when that directory has a ``uv.lock`` and ``uv`` is on PATH,
  otherwise as ``ruff`` from PATH, otherwise not at all. ``ruff check --fix``,
  then ``ruff format``, from that directory.
- TypeScript and JavaScript (``.ts``, ``.tsx``, ``.mts``, ``.cts``, ``.js``,
  ``.jsx``, ``.mjs``, ``.cjs``): oxlint when an ``.oxlintrc.json`` or
  ``oxlint.json`` is found, then biome when a ``biome.json`` or ``biome.jsonc``
  is, each looked for from the file's directory upward. Each runs from the
  nearest ``node_modules/.bin`` up from the file that holds it, and from the
  directory holding that ``node_modules``: ``oxlint --fix``, ``biome check
  --write``. A tool with a config and no binary is skipped.

A Bash call's files are the ones Claude Code reports it edited, in the tool
response's ``bashEditDiff``, whatever did the editing. Anything unexpected exits
silently.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

PYTHON = (".py", ".pyi")
SCRIPT = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
RUFF_CONFIGS = ("ruff.toml", ".ruff.toml")
NODE_TOOLS = (
    ("oxlint", (".oxlintrc.json", "oxlint.json"), ("--fix",)),
    ("biome", ("biome.json", "biome.jsonc"), ("check", "--write")),
)
SHOWN = 20
"""Lines of one tool's complaint passed on; the rest is one run away."""


@dataclass(frozen=True)
class Step:
    """One tool run: its argv and the directory it runs from."""

    argv: tuple[str, ...]
    cwd: str


def written_files(payload: dict[str, Any]) -> list[str]:
    """The absolute paths of the existing files an Edit or a Write wrote, or a Bash call
    edited (``tool_response.bashEditDiff.files[].filePath``), in order, each once."""
    tool = payload.get("tool_name")
    response = payload.get("tool_response") or {}
    if tool == "Bash":
        diff = response.get("bashEditDiff") or {}
        named = [str(one.get("filePath") or "") for one in diff.get("files") or []]
    elif tool in ("Edit", "Write", "MultiEdit"):
        named = [str((payload.get("tool_input") or {}).get("file_path") or "")]
    else:
        named = []
    cwd = str(payload.get("cwd") or os.getcwd())
    found: list[str] = []
    for one in named:
        path = os.path.abspath(os.path.join(cwd, one)) if one else ""
        if path and os.path.isfile(path) and path not in found:
            found.append(path)
    return found


def _upward(start: str):
    here = start
    while True:
        yield here
        parent = os.path.dirname(here)
        if parent == here:
            return
        here = parent


def _ruff(path: str) -> list[Step]:
    home = next(
        (
            d
            for d in _upward(os.path.dirname(path))
            if any(os.path.isfile(os.path.join(d, n)) for n in (*RUFF_CONFIGS, "pyproject.toml"))
        ),
        None,
    )
    if home is None:
        return []
    configured = any(os.path.isfile(os.path.join(home, n)) for n in RUFF_CONFIGS)
    if not configured:
        try:
            with open(os.path.join(home, "pyproject.toml"), encoding="utf-8") as fh:
                configured = "[tool.ruff" in fh.read()
        except OSError:
            configured = False
    if not configured:
        return []
    if os.path.isfile(os.path.join(home, "uv.lock")) and shutil.which("uv"):
        runner: tuple[str, ...] = ("uv", "run", "ruff")
    elif shutil.which("ruff"):
        runner = ("ruff",)
    else:
        return []
    return [Step((*runner, "check", "--fix", path), home), Step((*runner, "format", path), home)]


def _node(path: str) -> list[Step]:
    steps: list[Step] = []
    start = os.path.dirname(path)
    for tool, configs, args in NODE_TOOLS:
        if not any(
            os.path.isfile(os.path.join(d, n)) for d in _upward(start) for n in configs
        ):
            continue
        home = next(
            (d for d in _upward(start) if os.path.isfile(os.path.join(d, "node_modules", ".bin", tool))),
            None,
        )
        if home is not None:
            steps.append(Step((os.path.join(home, "node_modules", ".bin", tool), *args, path), home))
    return steps


def steps_for(path: str) -> list[Step]:
    """The tool runs that format one file, in order; empty when the project has none for it."""
    if path.endswith(PYTHON):
        return _ruff(path)
    if path.endswith(SCRIPT):
        return _node(path)
    return []


def respond(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Run every step for every written file. The answer names each lint finding the
    fix left, as ``hookSpecificOutput.additionalContext``; ``None`` when all ran clean."""
    said: list[str] = []
    for path in written_files(payload):
        for step in steps_for(path):
            try:
                done = subprocess.run(
                    step.argv, cwd=step.cwd, capture_output=True, text=True, timeout=60
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                said.append(f"{os.path.basename(step.argv[0])} on {path} did not run: {error}")
                continue
            if done.returncode != 0:
                out = (done.stdout.strip() or done.stderr.strip()).splitlines()
                more = f"\n... {len(out) - SHOWN} more lines" if len(out) > SHOWN else ""
                tool = " ".join(os.path.basename(a) for a in step.argv[:3] if not a.startswith("/"))
                said.append(f"{tool or step.argv[0]} left this in {path}:\n" + "\n".join(out[:SHOWN]) + more)
    if not said:
        return None
    event = str(payload.get("hook_event_name") or "PostToolUse")
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": "\n\n".join(said)}}


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        answer = respond(payload)
    except Exception:  # a hook never breaks the session
        return
    if answer is not None:
        json.dump(answer, sys.stdout)


if __name__ == "__main__":
    main()
