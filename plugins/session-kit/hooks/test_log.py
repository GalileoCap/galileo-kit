"""PostToolUse and PostToolUseFailure (Bash): keep the last test run's whole output in a
file for the session.

A command is a test run when it holds one of the guard's runners
(``guard.BUILTIN_TEST_COMMANDS``) or a ``test_commands`` entry of the
project's ``.claude/claude-kit.json``. The file is
``<tempdir>/claude-kit-last-test-<session_id>.log``, written whole each time:
the time, the directory, the command, whether it passed, and its output. A
Bash call that exits non-zero fires PostToolUseFailure, whose ``error`` holds
the output; one that passes fires PostToolUse, with ``stdout`` and ``stderr``
in its tool response. When the run failed, the session is told in one line
where the output is.
Anything unexpected exits silently.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import tempfile
from typing import Any

import guard

EVENTS = ("PostToolUse", "PostToolUseFailure")


def log_path(session_id: str) -> str:
    """The session's log file, in the system's temporary directory."""
    safe = re.sub(r"[^\w-]", "_", session_id) or "session"
    return os.path.join(tempfile.gettempdir(), f"claude-kit-last-test-{safe}.log")


def is_test_run(command: str, cwd: str) -> bool:
    """Whether a Bash command runs tests, by the guard's runners and the project's own."""
    names = guard.BUILTIN_TEST_COMMANDS + guard.project_test_commands(cwd)
    return any(re.search(rf"(?<![\w/.-]){re.escape(n)}(?![\w-])", command) for n in names)


def respond(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Write the log for a test run and return the one-line notice for a failed one.

    Pass or fail is the payload's ``hook_event_name``. The notice is
    ``hookSpecificOutput.additionalContext`` for that event. ``None`` when not a
    test run, or when it passed.
    """
    event = payload.get("hook_event_name")
    command = str((payload.get("tool_input") or {}).get("command") or "")
    cwd = str(payload.get("cwd") or os.getcwd())
    if event not in EVENTS or payload.get("tool_name") != "Bash" or not is_test_run(command, cwd):
        return None
    failed = event == "PostToolUseFailure"
    if failed:
        output = str(payload.get("error") or "")
    else:
        response = payload.get("tool_response") or {}
        output = f"{response.get('stdout') or ''}\n--- stderr ---\n{response.get('stderr') or ''}"
    path = log_path(str(payload.get("session_id") or "session"))
    when = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"--- {when} ---\nDirectory: {cwd}\nCommand: {command}\n")
        fh.write(f"Result: {'failed' if failed else 'passed'}\n--- output ---\n{output}\n")
    if not failed:
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": f"The test run failed; its whole output is in {path}.",
        }
    }


def main() -> None:
    try:
        answer = respond(json.load(sys.stdin))
    except Exception:  # a hook never breaks the session
        return
    if answer is not None:
        json.dump(answer, sys.stdout)


if __name__ == "__main__":
    main()
