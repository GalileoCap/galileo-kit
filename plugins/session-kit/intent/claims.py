"""The claims behind ``session-intent next`` and the claim check behind
``session-intent check``: the counter and log kept outside every checkout,
the mkdir lock over them, and the refusal of an entry whose id this checkout
never claimed or the integration branch has since given to another file.
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from session_intent import Entry, Ladder

LOCK_WAIT_SECONDS = 10.0


def git(root: Path, *args: str) -> str | None:
    """git's output from the root, stripped, or None when git fails."""
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def state_dir(root: Path, override: str | None) -> Path:
    """Where the claims live: outside every checkout, one directory per clone."""
    if override:
        return Path(override).resolve()
    common = git(root, "rev-parse", "--git-common-dir")
    key = (root / common).resolve() if common else root
    slug = str(key).replace(os.sep, "-")
    return Path.home() / ".claude" / "session-kit" / "intent" / slug


class Lock:
    """A mkdir mutex, the one atomic primitive every filesystem gives. The
    holder's pid is kept inside so a lock a dead process left is reclaimed."""

    def __init__(self, directory: Path) -> None:
        self.path = directory / ".lock"

    def __enter__(self) -> "Lock":
        deadline = time.monotonic() + LOCK_WAIT_SECONDS
        while True:
            try:
                self.path.mkdir()
                break
            except FileExistsError:
                holder = self.holder()
                if holder is not None and not alive(holder):
                    for child in self.path.iterdir():
                        child.unlink()
                    self.path.rmdir()
                    continue
                if time.monotonic() > deadline:
                    raise TimeoutError(f"{self.path}: held by pid {holder or 'unknown'} and not released in {LOCK_WAIT_SECONDS:g}s")
                time.sleep(0.05)
        (self.path / "pid").write_text(str(os.getpid()), encoding="utf-8")
        return self

    def __exit__(self, *_: object) -> None:
        try:
            (self.path / "pid").unlink()
        except FileNotFoundError:
            pass
        try:
            self.path.rmdir()
        except FileNotFoundError:
            pass

    def holder(self) -> int | None:
        try:
            return int((self.path / "pid").read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def highest(entries: dict[str, Entry], level: str) -> int:
    return max((e.key()[1] for e in entries.values() if e.level == level), default=0)


def claim(entries: dict[str, Entry], level: str, state: Path, root: Path, titles: list[str]) -> list[str]:
    """One id of the level per title, consecutive, taken under one lock and logged. Never reissued."""
    state.mkdir(parents=True, exist_ok=True)
    with Lock(state):
        counter = state / f"{level}.next"
        try:
            kept = int(counter.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            kept = 1
        number = max(kept, highest(entries, level) + 1)
        tmp = state / f".{level}.next.{os.getpid()}"
        tmp.write_text(f"{number + len(titles)}\n", encoding="utf-8")
        tmp.replace(counter)
        ids = [f"{level}{number + n}" for n in range(len(titles))]
        when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        commit = git(root, "rev-parse", "--short", "HEAD") or "none"
        with (state / "claims.log").open("a", encoding="utf-8") as log:
            for id_, title in zip(ids, titles):
                log.write(f"{id_} {when} {root.name} {commit} {title.replace(chr(10), ' ')}\n")
    return ids


def read_claims(state: Path) -> dict[str, set[str]] | None:
    """Each claimed id with the checkouts that claimed it, or None when this machine has no log."""
    try:
        text = (state / "claims.log").read_text(encoding="utf-8")
    except OSError:
        return None
    holders: dict[str, set[str]] = {}
    for line in text.splitlines():
        parts = line.split(maxsplit=4)
        if len(parts) >= 3:
            holders.setdefault(parts[0], set()).add(parts[2])
    return holders


@dataclass
class Integration:
    """The integration branch as this branch sees it: the entry files it held where
    this branch forked from it, and those at its tip, each by id."""

    ref: str = ""
    at_base: dict[str, str] | None = None
    at_tip: dict[str, str] = field(default_factory=dict)


def entry_files(root: Path, ladder: Ladder, commit: str) -> dict[str, str]:
    listed = git(root, "ls-tree", "-r", "--name-only", commit, "--", ladder.directory) or ""
    names = (Path(line).name for line in listed.splitlines())
    return {name.split("-", 1)[0]: name for name in names if name != "INDEX.md"}


def integration(root: Path, ladder: Ladder) -> tuple[Integration, list[str]]:
    """With no integration branch, every entry counts as this branch's."""
    ref = ladder.integration or git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if not ref:
        return Integration(), []
    base = git(root, "merge-base", "HEAD", ref)
    if base is None:
        if ladder.integration:
            return Integration(), [f"intent.integration: `{ref}` has no merge base with HEAD, so every entry was checked for its claim"]
        return Integration(), []
    return Integration(ref, entry_files(root, ladder, base), entry_files(root, ladder, ref)), []


def check_claims(entries: dict[str, Entry], root: Path, ladder: Ladder, state: Path) -> list[str]:
    """An entry this branch adds needs a claim this checkout made, and an id the
    integration branch has not since given to another file. Ids below a level's
    first claim are older than the log, and a machine with no log checks nothing."""
    holders = read_claims(state)
    if holders is None:
        return []
    floors: dict[str, int] = {}
    for id_ in holders:
        m = ladder.id_pattern.match(id_)
        if m:
            floors[m.group(1)] = min(floors.get(m.group(1), int(m.group(2))), int(m.group(2)))
    branch, problems = integration(root, ladder)
    for e in sorted(entries.values(), key=lambda e: (ladder.rank(e.level), e.key()[1])):
        level, number = e.key()
        if level not in floors or number < floors[level]:
            continue
        if branch.at_base is not None and e.id in branch.at_base:
            continue
        claimed_by = holders.get(e.id, set())
        taken = branch.at_tip.get(e.id)
        if taken and taken != e.path.name:
            why = f"also {taken} on {branch.ref}"
        elif root.name not in claimed_by:
            why = f"claimed by {', '.join(sorted(claimed_by))}, not by this checkout, {root.name}" if claimed_by else "never claimed"
        else:
            continue
        word = ladder.by_letter(level).word
        problems.append(
            f"{e.path.name}: `{e.id}` is {why}; take an id with `session-intent next {word} --title <its name>`, "
            "then give the entry that id in its file name, its `id`, and every `from`, `supersedes` and Intent-block line that names it"
        )
    return problems
