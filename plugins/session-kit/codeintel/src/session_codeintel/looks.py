"""The looks written in more than one place.

A look is a class string of two or more classes, in a ``className`` or
``*ClassName`` prop, an argument of ``cn``, or a value in a ``*-looks.ts``
file. A look kept in one component or one looks file is written once, so a
look found in two places is one nothing names yet, and the fix is a
component named for what it shows or an entry in a looks file. One class
alone is a token. The sites come from the pinned ``ast-grep`` over the
project's source directory, and the project's settings may allow a look
that repeats by coincidence, naming the files it is written in, so the
check also fails when an allowed look spreads to another file or leaves
one.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TypeGuard

AST_GREP = Path(sys.executable).parent / "ast-grep"
"""The pinned binary this package's environment installs, never PATH's."""

RULES = """\
id: look-in-tsx
language: tsx
rule:
  any:
    - kind: string
    - kind: template_string
  not:
    has: {kind: template_substitution}
  inside:
    stopBy: end
    any:
      - kind: jsx_attribute
        has: {kind: property_identifier, regex: '(^className$)|(ClassName$)'}
      - kind: call_expression
        has: {field: function, regex: '^cn$'}
---
id: look-in-ts
language: typescript
rule:
  any:
    - kind: string
    - kind: template_string
  not:
    has: {kind: template_substitution}
  inside:
    stopBy: end
    kind: call_expression
    has: {field: function, regex: '^cn$'}
---
id: look-in-looks-file
language: typescript
files: ['**/*-looks.ts']
rule:
  any:
    - kind: string
    - kind: template_string
  not:
    has: {kind: template_substitution}
  inside:
    stopBy: end
    kind: pair
"""
"""Three rules, one per language and file kind, each matching the strings that hold classes."""


@dataclass(frozen=True, slots=True)
class Site:
    """One class string: where it is written and the look it spells, classes sorted."""

    file: str
    line: int
    look: str


@dataclass(frozen=True, slots=True)
class Allowance:
    """A look that may repeat, in the files its entry lists and nowhere else."""

    look: str
    files: tuple[str, ...]
    reason: str = ""


@dataclass(frozen=True, slots=True)
class Settings:
    """The ``looks`` block of ``.claude/claude-kit.json``."""

    src: str = "src"
    skip: tuple[str, ...] = ("src/components/ui",)
    allowed: tuple[Allowance, ...] = ()


@dataclass(frozen=True, slots=True)
class Repeat:
    """A look written in more than one place."""

    look: str
    places: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Drift:
    """An allowed look whose files no longer match its entry."""

    look: str
    listed: tuple[str, ...]
    found: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Report:
    """What the check found."""

    sites: int
    repeats: tuple[Repeat, ...]
    drifts: tuple[Drift, ...]

    @property
    def clean(self) -> bool:
        """No look repeats and no allowance drifted."""
        return not self.repeats and not self.drifts


def normalized(classes: str) -> str:
    """Sort the classes, so their order does not matter."""
    return " ".join(sorted(name for name in classes.split() if name))


def _is_record(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _strings(value: object) -> tuple[str, ...]:
    return tuple(s for s in value if isinstance(s, str)) if _is_list(value) else ()


def read_settings(root: Path) -> Settings:
    """Read the ``looks`` block; the defaults when the file or the block is missing."""
    try:
        text = (root / ".claude" / "claude-kit.json").read_text(encoding="utf-8")
        parsed: object = json.loads(text)
    except (OSError, ValueError):
        return Settings()
    block = parsed.get("looks") if _is_record(parsed) else None
    if not _is_record(block):
        return Settings()
    src = block.get("src")
    src = src.strip("/") if isinstance(src, str) and src else "src"
    skip = block.get("skip")
    skip_dirs = _strings(skip) if _is_list(skip) else (f"{src}/components/ui",)
    allowed = block.get("allowed")
    return Settings(src=src, skip=skip_dirs, allowed=_allowances(allowed))


def _allowances(entries: object) -> tuple[Allowance, ...]:
    found: list[Allowance] = []
    for entry in entries if _is_list(entries) else []:
        if not _is_record(entry):
            continue
        look = entry.get("look")
        if not isinstance(look, str):
            continue
        reason = entry.get("reason")
        files = tuple(sorted(set(_strings(entry.get("files")))))
        why = reason if isinstance(reason, str) else ""
        found.append(Allowance(look=normalized(look), files=files, reason=why))
    return tuple(found)


def scan(root: Path, settings: Settings, ast_grep: Path = AST_GREP) -> list[Site]:
    """List every class string under the source directory, skip directories left out.

    Raises:
        RuntimeError: ast-grep failed, with its stderr.

    """
    src = root / settings.src
    if not src.is_dir():
        return []
    done = subprocess.run(  # noqa: S603  (decisions.md, 5)
        [str(ast_grep), "scan", "--inline-rules", RULES, "--json=compact", str(src)],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
    )
    if done.returncode != 0:
        msg = f"ast-grep failed: {done.stderr.strip()}"
        raise RuntimeError(msg)
    skipped = tuple(s.strip("/") + "/" for s in settings.skip)
    sites = [site for site in _sites(done.stdout, root) if not site.file.startswith(skipped)]
    return sorted(sites, key=lambda s: (s.file, s.line))


def _sites(output: str, root: Path) -> list[Site]:
    matches: object = json.loads(output or "[]")
    found: list[Site] = []
    for match in matches if _is_list(matches) else []:
        if not _is_record(match):
            continue
        text, file, line = match.get("text"), match.get("file"), _line(match.get("range"))
        if not isinstance(text, str) or not isinstance(file, str) or line is None:
            continue
        look = normalized(text[1:-1])
        if " " in look:
            found.append(Site(file=_relative(file, root), line=line, look=look))
    return found


def _line(range_: object) -> int | None:
    start = range_.get("start") if _is_record(range_) else None
    line = start.get("line") if _is_record(start) else None
    return line + 1 if isinstance(line, int) else None


def _relative(file: str, root: Path) -> str:
    path = Path(file)
    if path.is_absolute():
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def check(sites: list[Site], settings: Settings) -> Report:
    """Find the looks that repeat and the allowances that drifted."""
    allowed = {normalized(a.look): a for a in settings.allowed}
    by_look: dict[str, list[str]] = {}
    for site in sites:
        by_look.setdefault(site.look, []).append(f"{site.file}:{site.line}")
    repeats = tuple(
        Repeat(look=look, places=tuple(places))
        for look, places in by_look.items()
        if len(places) > 1 and look not in allowed
    )
    drifts: list[Drift] = []
    for look, allowance in allowed.items():
        found = tuple(sorted({s.file for s in sites if s.look == look}))
        if found != allowance.files:
            drifts.append(Drift(look=look, listed=allowance.files, found=found))
    return Report(sites=len(sites), repeats=repeats, drifts=tuple(drifts))


def lines(report: Report) -> list[str]:
    """Render what the command prints, one line each."""
    out: list[str] = []
    for repeat in report.repeats:
        out.append(f'"{repeat.look}" is written in {len(repeat.places)} places:')
        out += [f"  {place}" for place in repeat.places]
    for drift in report.drifts:
        where = ", ".join(drift.found) if drift.found else "none"
        listed = ", ".join(drift.listed)
        out.append(f'The allowed look "{drift.look}" lists {listed} but is written in {where}.')
    if report.repeats:
        out.append("Each look belongs to one component or one *-looks.ts entry.")
    if report.drifts:
        out.append(
            "Update the entry under looks.allowed in .claude/claude-kit.json: drop it once the "
            "look no longer repeats, and name the look once its places share a meaning."
        )
    if report.clean:
        out.append(f"{report.sites} class strings, none written twice")
    return out
