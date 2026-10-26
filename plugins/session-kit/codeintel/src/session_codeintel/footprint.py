"""The footprint gate: a plugin's reach as the engine's validator reports it, held in a file.

``claude plugin validate`` prints, for each hooks module, the events it
hooks, its gating hooks, the ``$`` calls with the functions they are made
through, and the environment and state it reads and writes. A plugin's
``footprint.toml`` holds those lines as the validator printed them, compared
as counts since their order is the registration's, and a reason for each
``$`` member and each hook event. A line the file lacks, a line the
validator no longer prints, a member or an event with no reason, and a
reason for one gone each fail, so a new reach is a reviewed change. The
plugins come from ``footprint.plugins`` in ``.claude/claude-kit.json``, and
the engine is the one the session runs on (``CLAUDE_CODE_EXECPATH``), else
``claude`` on PATH.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from session_codeintel import settings

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

FILE = "footprint.toml"
EXECPATH = "CLAUDE_CODE_EXECPATH"
MARK = chr(0x276F)
"""How the validator opens each line of its findings."""
END = "Plugin directory checks"
"""The line after which the validator checks a catalogue submission, not the reach."""
CUT = re.compile("… \\[\\+[0-9]+ chars\\]")
"""How the engine marks a line it shortened, at about a thousand characters."""
TIMEOUT_SECONDS = 120
HEADER = """\
# This plugin's reach as `claude plugin validate` reports it, held by
# `session-codeintel footprint`. [validator] is what the engine printed,
# written by --write and compared as counts. [why] gives the reason for each
# $ member and each hook event, and a new one waits on its reason.
"""


class FootprintError(ValueError):
    """A footprint or a validation the gate cannot read: refused, never skipped."""


@dataclass(frozen=True, slots=True)
class Footprint:
    """What a footprint holds, or what one validation printed with no reasons yet."""

    engine: str
    lines: dict[str, tuple[str, ...]]
    why: dict[str, str]


@dataclass(frozen=True, slots=True)
class Finding:
    """How a plugin's validation differs from its footprint."""

    plugin: str
    added: tuple[tuple[str, str], ...]
    removed: tuple[tuple[str, str], ...]
    unreasoned: tuple[str, ...]
    stale: tuple[str, ...]
    taken_with: str
    checked_with: str

    @property
    def clean(self) -> bool:
        """Whether the footprint holds the validation whole, with every reason."""
        return not (self.added or self.removed or self.unreasoned or self.stale)


def read_settings(root: Path) -> tuple[str, ...] | None:
    """Return the plugin directories under ``footprint.plugins``; None without the block."""
    block = settings.block(root, "footprint")
    return None if block is None else settings.strings(block.get("plugins"))


def engine_of(named: str | None) -> str:
    """Return the engine to validate with: the one named, the session's, or ``claude``."""
    if named is not None:
        return named
    running = os.environ.get(EXECPATH)
    return running or "claude"


def validate(engine: str, plugin: Path) -> Footprint:
    """Run the engine's validator over the plugin; its lines, or its errors refused."""
    version = run([engine, "--version"]).stdout.split()
    if not version:
        msg = f"{engine} --version printed nothing"
        raise FootprintError(msg)
    done = run([engine, "plugin", "validate", str(plugin)])
    if done.returncode != 0:
        msg = "\n".join(
            line.strip() for line in (done.stdout + done.stderr).splitlines() if line.strip()
        )
        raise FootprintError(msg)
    found = parse(done.stdout)
    if shortened := cut(found):
        msg = f"the engine cut short {', '.join(shortened)}: what follows the cut is unseen"
        raise FootprintError(msg)
    return Footprint(version[0], found, {})


def run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run a program by its argument vector; a missing one or one that hangs is refused."""
    try:
        return subprocess.run(  # noqa: S603  the engine, git or the pinned ast-grep, an argument vector and no shell
            argv, capture_output=True, text=True, check=False, timeout=TIMEOUT_SECONDS, cwd=cwd
        )
    except (OSError, subprocess.TimeoutExpired) as failed:
        msg = f"{argv[0]}: {failed}"
        raise FootprintError(msg) from failed


def parse(report: str) -> dict[str, tuple[str, ...]]:
    """Read the validator's findings up to the directory's checks, as ``notes`` reads them."""
    marked: list[str] = []
    for raw in report.splitlines():
        if raw.startswith(END):
            break
        line = raw.strip()
        if line.startswith(MARK):
            marked.append(line.removeprefix(MARK).strip())
    return notes(marked)


def notes(found: Iterable[str]) -> dict[str, tuple[str, ...]]:
    """Read the validator's notes as each one's head and its items, sorted."""
    lines: dict[str, list[str]] = {}
    for note in found:
        head, _, rest = note.partition(": ")
        lines.setdefault(head, []).extend(items(rest))
    return {head: tuple(sorted(listed)) for head, listed in lines.items()}


def items(text: str) -> tuple[str, ...]:
    """Split a finding's list at the commas outside quotes, braces and parentheses."""
    if text == "nothing" or text.startswith("nothing ("):
        return ()
    found: list[str] = []
    depth = 0
    quoted = False
    start = 0
    for at, char in enumerate(text):
        if char == '"':
            quoted = not quoted
        elif not quoted and char in "({":
            depth += 1
        elif not quoted and char in ")}":
            depth -= 1
        elif char == "," and not quoted and depth == 0:
            found.append(text[start:at].strip())
            start = at + 1
    found.append(text[start:].strip())
    return tuple(found)


def cut(lines: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    """Return the heads of the lines the engine shortened, whose last items are unseen."""
    return tuple(head for head, found in lines.items() if any(CUT.search(i) for i in found))


def names(lines: dict[str, tuple[str, ...]]) -> set[str]:
    """Return what owes a reason: each ``$`` member called and each event hooked."""
    owed: set[str] = set()
    for head, found in lines.items():
        if head.endswith(" calls"):
            owed.update(item.partition(" (via ")[0] for item in found)
        elif head.endswith(" hooks"):
            owed.update(item.partition("{")[0] for item in found)
    return owed


def read(path: Path) -> Footprint | None:
    """Read a footprint file; None when it is missing, refused when it cannot be read."""
    if not path.is_file():
        return None
    try:
        held: dict[str, object] = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as broken:
        raise FootprintError(str(broken)) from broken
    engine, lines, why = held.get("engine"), held.get("validator"), held.get("why")
    if not isinstance(engine, str) or not settings.is_record(lines):
        msg = "needs `engine` and a [validator] table"
        raise FootprintError(msg)
    if not settings.is_record(why) or not all(isinstance(v, str) for v in why.values()):
        msg = "needs a [why] table of strings"
        raise FootprintError(msg)
    taken = {head: tuple(sorted(settings.strings(found))) for head, found in lines.items()}
    return Footprint(engine, taken, {name: str(reason) for name, reason in why.items()})


def compare(plugin: str, held: Footprint, seen: Footprint) -> Finding:
    """Find what the validation added to the footprint, removed from it, and owes."""
    added: list[tuple[str, str]] = []
    removed: list[tuple[str, str]] = []
    for head in sorted(set(held.lines) | set(seen.lines)):
        before = Counter(held.lines.get(head, ()))
        after = Counter(seen.lines.get(head, ()))
        added += [(head, item) for item in sorted((after - before).elements())]
        removed += [(head, item) for item in sorted((before - after).elements())]
    owed = names(seen.lines)
    return Finding(
        plugin,
        tuple(added),
        tuple(removed),
        tuple(sorted(name for name in owed if not held.why.get(name, "").strip())),
        tuple(sorted(set(held.why) - owed)),
        held.engine,
        seen.engine,
    )


def taken(seen: Footprint, before: Footprint | None) -> Footprint:
    """Return the validation as a footprint, with each reason kept that still has its name."""
    kept = {} if before is None else before.why
    return Footprint(
        seen.engine, seen.lines, {n: kept.get(n, "") for n in sorted(names(seen.lines))}
    )


def render(held: Footprint) -> str:
    """Write a footprint as TOML, one item per line so a change reads as a diff."""
    out = [HEADER, f"engine = {_quoted(held.engine)}", "", "[validator]"]
    for head in sorted(held.lines):
        out += [f"{_quoted(head)} = [", *_listed(held.lines[head]), "]"]
    out += ["", "[why]"]
    out += [f"{_quoted(name)} = {_quoted(reason)}" for name, reason in sorted(held.why.items())]
    return "\n".join(out) + "\n"


def _listed(found: Iterable[str]) -> list[str]:
    return [f"  {_quoted(item)}," for item in found]


def _quoted(text: str) -> str:
    """Quote a TOML basic string, whose escapes are JSON's."""
    return json.dumps(text, ensure_ascii=False)


def lines(finding: Finding) -> list[str]:
    """Return one line per difference, per reason owed and per reason left over."""
    at = f"{finding.plugin}/{FILE}"
    out = [f"{at}: + {head}: {item}" for head, item in finding.added]
    out += [f"{at}: - {head}: {item}" for head, item in finding.removed]
    out += [f"{at}: no reason for {name}" for name in finding.unreasoned]
    out += [
        f"{at}: a reason for {name}, which the validator no longer lists" for name in finding.stale
    ]
    if finding.taken_with != finding.checked_with:
        out.append(f"{at}: taken with {finding.taken_with}, checked with {finding.checked_with}")
    return out
