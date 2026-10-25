"""The index and check over a project's ``docs/intent/``.

``session-intent index`` writes ``docs/intent/INDEX.md``: the entries that
wait on the owner first, oldest first, then the ladder downward (each goal
with its objectives, each objective with its actions), the constraints, and
the retired entries with their successors. ``session-intent check`` reads
the record and prints one line per problem: an id that does not resolve, a
path in ``implemented_by`` or ``proven_by`` that does not exist, an approved
objective with no action, an action that names no objective, a status
without a date, a retired entry nothing supersedes, a file whose name does
not carry its id, a missing field, the ``CLAUDE.md`` Intent block out of
step with the active entries, and an ``INDEX.md`` that is missing or stale.
It exits 1 on any. ``session-intent names [id ...]`` prints each entry's
id and name, every entry when no id is given, so a session that lost the
names to a compaction gets them back in one call; an unknown id is a
problem. ``session-intent next <level>`` claims the next id of a level
(``G``, ``O``, ``A`` or ``C``) under a lock and prints it: the floor is the
highest id the record holds or the last one claimed, whichever is higher,
so a fresh clone needs no seeding, and an id once claimed is never given
again, since by then it is usually in a reply, a commit message or a
handoff that outlives the claim. The claims live outside every checkout,
under ``~/.claude/session-kit/intent/``, one directory per clone (named
after its git common directory, so every worktree shares it), with one
``<level>.next`` file per level and an append-only ``claims.log`` saying
which checkout took each id, at which commit, with what title. Links are
written upward only, so everything downward is derived here and never kept
by hand.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

LEVELS = {"G": "goal", "O": "objective", "A": "action", "C": "constraint"}
LEVEL_OF_WORD = {word: letter for letter, word in LEVELS.items()}
LOCK_WAIT_SECONDS = 10.0
STATUSES = {
    "G": ("stated", "retired"),
    "O": ("proposed", "approved", "retired"),
    "A": ("decided", "validated", "retired"),
    "C": ("proposed", "stated", "retired"),
}
QUEUED = {"O": "proposed", "A": "decided", "C": "proposed"}
ACTION_FIELDS = ("kind", "implemented_by", "proven_by", "supersedes")
ID = re.compile(r"^([GOAC])(\d+)$")
STATUS = re.compile(r"^(\w+)(?:\s+(\d{4}-\d{2}-\d{2}))?$")
BLOCK_ID = re.compile(r"^- `([GOAC]\d+)`")


@dataclass
class Entry:
    id: str
    path: Path
    title: str
    fields: dict[str, str]
    lists: dict[str, list[str]] = field(default_factory=dict)
    status: str = ""
    date: str = ""
    says_no_action: bool = False

    @property
    def level(self) -> str:
        return self.id[0]

    @property
    def retired(self) -> bool:
        return self.status == "retired"

    def key(self) -> tuple[str, int]:
        m = ID.match(self.id)
        return (self.id[0], int(m.group(2))) if m else (self.id, 0)


def split_list(value: str) -> list[str]:
    inner = value.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    return [item.strip() for item in inner.split(",") if item.strip()]


def is_placeholder(items: list[str]) -> bool:
    return not items or items[0].startswith("not yet") or items[0] == "unproven"


def read_entry(path: Path, problems: list[str]) -> Entry | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        problems.append(f"{path.name}: no header")
        return None
    fields: dict[str, str] = {}
    end = 0
    for n, line in enumerate(lines[1:], start=1):
        if line == "---":
            end = n
            break
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    if not end:
        problems.append(f"{path.name}: header never closes")
        return None
    title = next((l[2:].strip() for l in lines[end:] if l.startswith("# ")), path.stem)
    entry_id = fields.get("id", "")
    if entry_id and title.startswith(entry_id + " "):
        title = title[len(entry_id) + 1:]
    entry = Entry(id=entry_id, path=path, title=title, fields=fields)
    entry.says_no_action = "no action yet" in "\n".join(lines[end:]).lower()
    for key in ("from", "supersedes", "implemented_by", "proven_by"):
        if key in fields:
            entry.lists[key] = split_list(fields[key])
    m = STATUS.match(fields.get("status", ""))
    if m:
        entry.status, entry.date = m.group(1), m.group(2) or ""
    return entry


def read_record(intent: Path) -> tuple[dict[str, Entry], list[str]]:
    problems: list[str] = []
    entries: dict[str, Entry] = {}
    for path in sorted(intent.glob("*.md")):
        if path.name == "INDEX.md":
            continue
        entry = read_entry(path, problems)
        if entry is None:
            continue
        stem_id = path.name.split("-", 1)[0]
        if not ID.match(entry.id):
            problems.append(f"{path.name}: id `{entry.id}` is not G, O, A or C followed by a number")
            continue
        if stem_id != entry.id:
            problems.append(f"{path.name}: the file name does not carry its id `{entry.id}`")
        if entry.id in entries:
            problems.append(f"{path.name}: id `{entry.id}` is also {entries[entry.id].path.name}")
            continue
        entries[entry.id] = entry
    return entries, problems


def check_entry(entry: Entry, entries: dict[str, Entry], root: Path, problems: list[str]) -> None:
    name = entry.path.name
    level = entry.level
    if entry.status not in STATUSES[level]:
        allowed = ", ".join(STATUSES[level])
        problems.append(f"{name}: status `{entry.fields.get('status', '')}` is none of {allowed} for a {LEVELS[level]}")
    elif not entry.date:
        problems.append(f"{name}: status `{entry.status}` has no date")
    if level in ("O", "A") and "from" not in entry.lists:
        problems.append(f"{name}: no `from` field")
    for key in ("from", "supersedes"):
        for target in entry.lists.get(key, []):
            if target not in entries:
                problems.append(f"{name}: `{key}` names `{target}`, which does not exist")
    wanted = {"O": "G", "A": "O"}.get(level)
    if wanted:
        named = [t for t in entry.lists.get("from", []) if t in entries]
        if not entry.retired and not any(t.startswith(wanted) for t in named):
            problems.append(f"{name}: a {LEVELS[level]} names no {LEVELS[wanted]} in `from`")
    if level == "A":
        for key in ACTION_FIELDS:
            if key not in entry.fields:
                problems.append(f"{name}: an action without `{key}`")
        if entry.retired:
            # What implemented it may be gone by design; git keeps it.
            return
        for key in ("implemented_by", "proven_by"):
            items = entry.lists.get(key, [])
            if is_placeholder(items):
                continue
            for item in items:
                if not (root / item).exists():
                    problems.append(f"{name}: `{key}` names `{item}`, which does not exist")


def check_record(entries: dict[str, Entry], root: Path) -> list[str]:
    problems: list[str] = []
    for entry in entries.values():
        check_entry(entry, entries, root, problems)
    superseded = {t for e in entries.values() for t in e.lists.get("supersedes", [])}
    served = {t for e in entries.values() if e.level == "A" and not e.retired for t in e.lists.get("from", [])}
    for entry in entries.values():
        if entry.retired and entry.id not in superseded:
            problems.append(f"{entry.path.name}: retired, and no entry names it in `supersedes`")
        if entry.level == "O" and entry.status == "approved" and entry.id not in served and not entry.says_no_action:
            problems.append(f"{entry.path.name}: approved, no action names it in `from`, and it does not say \"no action yet\"")
    return problems


def check_block(entries: dict[str, Entry], root: Path) -> list[str]:
    claude = root / "CLAUDE.md"
    if not claude.exists():
        return ["CLAUDE.md: missing, so no Intent block lists the active entries"]
    lines = claude.read_text(encoding="utf-8").splitlines()
    listed: list[str] = []
    inside = False
    for line in lines:
        if line.startswith("## "):
            inside = line.strip() == "## Intent"
            continue
        m = BLOCK_ID.match(line) if inside else None
        if m:
            listed.append(m.group(1))
    if not listed:
        return ["CLAUDE.md: no `## Intent` block lists the active entries"]
    problems: list[str] = []
    active = {e.id for e in entries.values() if e.level in ("G", "O", "C") and not e.retired}
    for id_ in sorted(active - set(listed), key=lambda i: (i[0], int(i[1:]))):
        problems.append(f"CLAUDE.md: the Intent block lacks the active entry `{id_}`")
    for id_ in listed:
        if id_ not in entries:
            problems.append(f"CLAUDE.md: the Intent block lists `{id_}`, which does not exist")
        elif id_ not in active:
            problems.append(f"CLAUDE.md: the Intent block lists `{id_}`, which is retired or an action")
    return problems


def link(entry: Entry) -> str:
    return f"[{entry.id} {entry.title}]({entry.path.name})"


def line(entry: Entry) -> str:
    when = f" {entry.date}" if entry.date else ""
    return f"- {link(entry)}: {entry.status}{when}"


def render_index(entries: dict[str, Entry]) -> str:
    ordered = sorted(entries.values(), key=Entry.key)
    out = ["# Intent index", "", "Generated by `session-intent index` from the entries beside it. Do not edit by hand: the check fails when it is stale.", ""]
    queue = sorted(
        (e for e in ordered if e.status == QUEUED.get(e.level)),
        key=lambda e: (e.date, e.key()),
    )
    out += ["## Waiting on the owner", ""]
    out += [line(e) + (" (an objective to approve)" if e.level == "O" else " (a constraint to state)" if e.level == "C" else " (an action to validate)") for e in queue] or ["Nothing."]
    out += ["", "## Goals", ""]
    children: dict[str, list[Entry]] = {}
    for e in ordered:
        if e.retired:
            continue
        for parent in e.lists.get("from", []):
            children.setdefault(parent, []).append(e)
    for goal in (e for e in ordered if e.level == "G" and not e.retired):
        out.append(line(goal))
        for objective in children.get(goal.id, []):
            out.append("  " + line(objective))
            for action in children.get(objective.id, []):
                out.append("    " + line(action) + f" ({action.fields.get('kind', '')})")
    orphans = [e for e in ordered if e.level in ("O", "A") and not e.retired and not any(p in entries for p in e.lists.get("from", []))]
    if orphans:
        out += ["", "## Without a parent", ""] + [line(e) for e in orphans]
    out += ["", "## Constraints", ""]
    out += [line(e) for e in ordered if e.level == "C" and not e.retired] or ["None."]
    successors: dict[str, list[str]] = {}
    for e in ordered:
        for target in e.lists.get("supersedes", []):
            successors.setdefault(target, []).append(e.id)
    retired = [e for e in ordered if e.retired]
    out += ["", "## Retired", ""]
    out += [
        line(e) + (", superseded by " + ", ".join(f"`{s}`" for s in successors[e.id]) if e.id in successors else ", nothing supersedes it")
        for e in retired
    ] or ["None."]
    return "\n".join(out) + "\n"


def names(entries: dict[str, Entry], wanted: list[str]) -> tuple[list[str], list[str]]:
    """Each entry's id and name, goals first and the ladder downward, a retired one marked."""
    lines: list[str] = []
    problems: list[str] = []
    ladder = {"G": 0, "O": 1, "A": 2, "C": 3}
    chosen = sorted(entries.values(), key=lambda e: (ladder.get(e.level, 9), e.key())) if not wanted else []
    for id_ in wanted:
        if id_ in entries:
            chosen.append(entries[id_])
        else:
            problems.append(f"{id_}: no such entry")
    for e in chosen:
        lines.append(f"{e.id} {e.title}" + (" (retired)" if e.retired else ""))
    return lines, problems


def git(root: Path, *args: str) -> str | None:
    """git's first output line from the root, or None outside a repository."""
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip().splitlines()[0] if out.stdout.strip() else None


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


def claim(entries: dict[str, Entry], level: str, state: Path, root: Path, title: str) -> str:
    """The next id of the level, taken under the lock and logged. Never reissued."""
    state.mkdir(parents=True, exist_ok=True)
    with Lock(state):
        counter = state / f"{level}.next"
        try:
            kept = int(counter.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            kept = 1
        number = max(kept, highest(entries, level) + 1)
        tmp = state / f".{level}.next.{os.getpid()}"
        tmp.write_text(f"{number + 1}\n", encoding="utf-8")
        tmp.replace(counter)
        id_ = f"{level}{number}"
        when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        commit = git(root, "rev-parse", "--short", "HEAD") or "none"
        with (state / "claims.log").open("a", encoding="utf-8") as log:
            log.write(f"{id_} {when} {root.name} {commit} {title.replace(chr(10), ' ')}\n")
    return id_


def level_of(word: str) -> str | None:
    if word in LEVELS:
        return word
    return LEVEL_OF_WORD.get(word.lower())


def main() -> int:
    parser = argparse.ArgumentParser(description="The index, check, names and next id over docs/intent.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".", help="the project root; its docs/intent and CLAUDE.md are read")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("index", parents=[common], help="write docs/intent/INDEX.md")
    commands.add_parser("check", parents=[common], help="the problems in the record, one per line")
    names_parser = commands.add_parser("names", parents=[common], help="each entry's id and name")
    names_parser.add_argument("ids", nargs="*", help="the ids to print, all when none")
    next_parser = commands.add_parser("next", parents=[common], help="claim the next id of a level")
    next_parser.add_argument("level", help="G, O, A or C, or goal, objective, action, constraint")
    next_parser.add_argument("--title", default="", help="what the entry will be, kept in the claims log")
    next_parser.add_argument("--state", default=None, help="where the claims live, instead of ~/.claude/session-kit/intent/<clone>")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    intent = root / "docs" / "intent"
    if not intent.is_dir():
        print(f"{intent}: no such directory")
        return 2
    entries, problems = read_record(intent)
    if args.command == "names":
        lines, missing = names(entries, args.ids)
        for l in lines:
            print(l)
        for p in problems + missing:
            print(p)
        return 1 if missing else 0
    if args.command == "next":
        level = level_of(args.level)
        if level is None:
            print(f"{args.level}: no such level; one of G, O, A, C")
            return 2
        try:
            print(claim(entries, level, state_dir(root, args.state), root, args.title))
        except TimeoutError as error:
            print(error)
            return 1
        return 0
    index = intent / "INDEX.md"
    if args.command == "index":
        index.write_text(render_index(entries), encoding="utf-8")
        for p in problems:
            print(p)
        print(f"{index}: {len(entries)} entries")
        return 0
    problems += check_record(entries, root)
    problems += check_block(entries, root)
    if not index.exists():
        problems.append("docs/intent/INDEX.md: missing; run `session-intent index`")
    elif index.read_text(encoding="utf-8") != render_index(entries):
        problems.append("docs/intent/INDEX.md: stale; run `session-intent index`")
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
