"""Write the root pyrightconfig.json at session start, for a project that asks.

A language server started at the root of a repository of several uv
packages sees one interpreter, and answers "no references" for whatever
lives in the other packages. ``session-codeintel pyright-env`` writes one
execution environment per package. A project turns this on with
``"pyright_env": true`` in ``.claude/claude-kit.json``, because the file it
writes would replace a root ``pyrightconfig.json`` the project keeps by
hand. A package it left out is named to the session, which would otherwise
meet it as an empty answer. It never blocks and never fails the event.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

TIMEOUT = 120


def payload() -> dict[str, object]:
    """Read the event's JSON, or an empty object when stdin holds none."""
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def project_root(event: dict[str, object]) -> Path:
    """Pick the project directory, then the event's working directory, then this process's."""
    named = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd")
    return Path(named) if isinstance(named, str) and named else Path.cwd()


def asked(root: Path) -> bool:
    """Say whether the project's ``.claude/claude-kit.json`` sets ``pyright_env`` to true."""
    try:
        config = json.loads((root / ".claude" / "claude-kit.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(config, dict) and config.get("pyright_env") is True


def main() -> int:
    """Run the generator and name what it left out."""
    root = project_root(payload())
    uv = shutil.which("uv")
    if not asked(root) or uv is None:
        return 0
    plugin = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or str(plugin)
    env = {**os.environ, "UV_PROJECT_ENVIRONMENT": str(Path(base) / "venv-codeintel")}
    command = [uv, "run", "--quiet", "--frozen", "--project", str(plugin / "codeintel")]
    command += ["session-codeintel", "pyright-env", str(root)]
    try:
        done = subprocess.run(
            command, cwd=root, env=env, capture_output=True, text=True, timeout=TIMEOUT, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as failed:
        say(f"pyright-env did not finish: {failed}")
        return 0
    if done.returncode != 0:
        lines = [line.strip() for line in done.stderr.splitlines() if line.strip()]
        say("; ".join(lines) or f"pyright-env exited {done.returncode}")
    return 0


def say(detail: str) -> None:
    """Tell the person and the session that navigation misses something."""
    print(
        json.dumps(
            {
                "systemMessage": f"Navigation is partial: {detail}",
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": (
                        f"pyrightconfig.json (the language server's view of the packages): {detail}"
                    ),
                },
            }
        )
    )


if __name__ == "__main__":
    sys.exit(main())
