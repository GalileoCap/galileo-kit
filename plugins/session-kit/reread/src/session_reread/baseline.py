"""Find the version the owner last read.

It is the commit HEAD was on when the owner's prompt opened the latest turn that committed a change
to the files. The owner reads, writes feedback, and the session edits and commits in the turn that
feedback opens. A prompt sent after that turn, such as one asking what changed, opens a turn that
commits nothing to the files, so it does not move the baseline. The prompts' times come from the
session's transcript, and HEAD's position at a time from the reflog.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeGuard

PROJECTS = Path.home() / ".claude" / "projects"
# Lines Claude Code writes as the user's that the person did not type.
NOT_TYPED = (
    "<local-command",
    "<command-name>",
    "<task-notification",
    "<side-sessions-event",
    "<ci-monitor-event",
)
QUOTED = 80


@dataclass(frozen=True)
class Prompt:
    """A prompt the person typed, and when it arrived, in seconds since the epoch."""

    at: float
    text: str


@dataclass(frozen=True)
class Baseline:
    """The git ref compared with, and the sentence saying why it was chosen."""

    ref: str
    why: str


def is_record(value: object) -> TypeGuard[dict[str, object]]:
    """Tell whether a JSON value is an object."""
    return isinstance(value, dict)


def is_list(value: object) -> TypeGuard[list[object]]:
    """Tell whether a JSON value is an array."""
    return isinstance(value, list)


def git(root: Path, *args: str) -> str | None:
    """Return git's output in the checkout, or None when it fails."""
    exe = shutil.which("git")
    if exe is None:
        return None
    done = subprocess.run(  # noqa: S603  git with an argument vector and no shell
        [exe, "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    return done.stdout if done.returncode == 0 else None


def transcript(root: Path, projects: Path = PROJECTS) -> Path | None:
    """Return the running session's transcript, or else the newest one of the checkout's."""
    folder = projects / re.sub(r"[^A-Za-z0-9]", "-", str(root))
    session = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if session and (folder / f"{session}.jsonl").is_file():
        return folder / f"{session}.jsonl"
    found = sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    return found[-1] if found else None


def prompts(path: Path) -> list[Prompt]:
    """Return the person's typed prompts in the transcript, in order."""
    found: list[Prompt] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                r: object = json.loads(line)
            except ValueError:
                continue
            if not is_record(r) or r.get("type") != "user":
                continue
            if any(
                r.get(k) for k in ("isSidechain", "isMeta", "isCompactSummary", "toolUseResult")
            ):
                continue
            text = typed(r.get("message"))
            stamp = r.get("timestamp")
            if text and isinstance(stamp, str) and not text.lstrip().startswith(NOT_TYPED):
                found.append(Prompt(datetime.fromisoformat(stamp).timestamp(), text))
    return found


def typed(message: object) -> str:
    """Return the text of a user message, empty when it holds none."""
    if not is_record(message):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not is_list(content):
        return ""
    blocks = content
    return "\n".join(
        str(b.get("text", "")) for b in blocks if is_record(b) and b.get("type") == "text"
    )


def head_at(root: Path, at: float) -> str | None:
    """Return the commit HEAD was on at a time, from the reflog."""
    log = git(root, "log", "-g", "--date=unix", "--format=%H %gd", "HEAD") or ""
    for line in log.splitlines():
        commit, _, selector = line.partition(" ")
        stamp = re.search(r"\{(\d+)\}", selector)
        if stamp and int(stamp.group(1)) <= at:
            return commit
    return None


def find(root: Path, paths: list[str], said: list[Prompt]) -> Baseline:
    """Return HEAD when the prompt came that opened the last turn committing to the paths."""
    if not said:
        return Baseline("HEAD", "the last commit, since no prompt of the person's was found")
    log = (
        git(
            root,
            "log",
            "--since=" + datetime.fromtimestamp(said[0].at, UTC).isoformat(),
            "--format=%ct",
            "--",
            *paths,
        )
        or ""
    )
    times = [int(t) for t in log.split()]
    if not times:
        return Baseline("HEAD", "the last commit, since none touched these files in this session")
    prompt = [p for p in said if p.at <= times[0]][-1]
    commit = head_at(root, prompt.at)
    if commit is None:
        return Baseline("HEAD", "the last commit, since the reflog does not reach that prompt")
    when = datetime.fromtimestamp(prompt.at).astimezone().strftime("%H:%M on %Y-%m-%d")
    words = " ".join(prompt.text.split())
    quoted = words if len(words) <= QUOTED else words[:QUOTED] + "…"
    return Baseline(commit, f"HEAD when your prompt arrived at {when}: “{quoted}”")
