"""The quality gates: the duplicate gate, the fallback ledger and the file-length lint.

A function body written twice fails, at any length under one name and at
three statements or more under different names, dunders and the methods a
``Protocol`` declares aside. A fallback site the ledger has not judged
fails, and so does a row the tree no longer matches, so the ledger is a
ratchet: full on day one, shrinking, deleted when empty. A file over the
code-line cap fails unless a ``long`` entry in the settings raises or lifts
its cap with a reason. The areas come from ``quality.areas`` in
``.claude/claude-kit.json`` (``name``, ``path``, ``skip``) or the root
alone, the ledger from ``quality.ledger`` (``quality-ledger.toml``), the cap
from ``quality.max_code_lines`` (500), and ``quality.protocols_from`` names
other trees whose protocols count.
"""

from __future__ import annotations

import tomllib
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from session_codeintel import facts, fallbacks, settings
from session_codeintel.measure import PYTHON, Area

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from session_codeintel.fallbacks import Site, SiteKey

MIN_SHARED_STATEMENTS = 3
"""How long two differently named bodies must be before sharing one is a copy."""
MAX_CODE_LINES = 500
LEDGER = "quality-ledger.toml"
PAIR = 2
DEFAULT_AREAS = (Area(".", ".", (), PYTHON),)
CLASSES = ("declared", "spoken", "silent", "refusal-class")
FALLBACK_DISPOSITIONS = ("keep", "speak", "refuse", "remove", "raised")
DUPLICATE_DISPOSITIONS = ("move", "keep")


@dataclass(frozen=True, slots=True)
class Long:
    """A file whose cap is raised, or lifted when ``cap`` is None, with the reason."""

    file: str
    cap: int | None
    reason: str


@dataclass(frozen=True, slots=True)
class Settings:
    """The ``quality`` block, with its defaults."""

    areas: tuple[Area, ...] = DEFAULT_AREAS
    ledger: str = LEDGER
    max_code_lines: int = MAX_CODE_LINES
    long: tuple[Long, ...] = ()
    protocols_from: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DuplicateRow:
    """One family of functions sharing a body, and where the one copy should live."""

    members: tuple[str, ...]
    home: str
    disposition: str
    why: str


@dataclass(frozen=True, slots=True)
class FallbackRow:
    """One site where an absence or a failure becomes a value, judged."""

    site: str
    where: str
    form: str
    code: str
    count: int
    classification: str
    disposition: str
    why: str

    @property
    def key(self) -> SiteKey:
        """What the finder matches this row against."""
        return fallbacks.SiteKey(self.site, self.where, self.form, self.code)


@dataclass(frozen=True, slots=True)
class Ledger:
    """The whole of the ledger file; absent means empty."""

    duplicates: tuple[DuplicateRow, ...] = ()
    fallbacks: tuple[FallbackRow, ...] = ()


class LedgerError(ValueError):
    """A ledger row the gate cannot read: an error, never a row it skips."""


@dataclass(frozen=True, order=True, slots=True)
class Family:
    """Functions sharing one body: ``path:qualname`` members, sorted."""

    members: tuple[str, ...]
    statements: int


@dataclass(frozen=True, slots=True)
class Duplicates:
    """Families the ledger does not name, and rows no family matches."""

    new: tuple[Family, ...]
    stale: tuple[DuplicateRow, ...]


@dataclass(frozen=True, slots=True)
class Fallbacks:
    """Sites the ledger does not cover, with the counts, and rows the tree no longer has."""

    new: tuple[tuple[Site, int, int], ...]
    stale: tuple[tuple[FallbackRow, int], ...]


@dataclass(frozen=True, slots=True)
class Offender:
    """A file over its cap."""

    path: str
    lines: int
    cap: int


@dataclass(frozen=True, slots=True)
class Report:
    """What the three gates found."""

    modules: int
    rows: int
    duplicates: Duplicates
    fallbacks: Fallbacks
    length: tuple[Offender, ...]
    drift: tuple[str, ...]

    @property
    def problems(self) -> int:
        """How many lines ``lines`` prints."""
        return (
            len(self.duplicates.new)
            + len(self.duplicates.stale)
            + len(self.fallbacks.new)
            + len(self.fallbacks.stale)
            + len(self.length)
            + len(self.drift)
        )

    @property
    def clean(self) -> bool:
        """Whether every gate passes."""
        return self.problems == 0


def read_settings(root: Path) -> Settings:
    """Read the ``quality`` block; the defaults when the file or the block is missing."""
    block = settings.block(root, "quality")
    if block is None:
        return Settings()
    entries = block.get("areas")
    areas = tuple(a for a in map(_area, entries) if a) if settings.is_list(entries) else ()
    cap = block.get("max_code_lines")
    return Settings(
        areas=areas or DEFAULT_AREAS,
        ledger=settings.text(block, "ledger") or LEDGER,
        max_code_lines=cap if isinstance(cap, int) and cap > 0 else MAX_CODE_LINES,
        long=_longs(block.get("long")),
        protocols_from=settings.strings(block.get("protocols_from")),
    )


def _area(entry: object) -> Area | None:
    if not settings.is_record(entry):
        return None
    path = settings.text(entry, "path")
    if path is None:
        return None
    name = settings.text(entry, "name") or path
    return Area(name, path, settings.strings(entry.get("skip")), PYTHON)


def _longs(value: object) -> tuple[Long, ...]:
    found: list[Long] = []
    for entry in value if settings.is_list(value) else ():
        if not settings.is_record(entry):
            continue
        file = settings.text(entry, "file")
        reason = entry.get("reason")
        cap = entry.get("cap")
        if file and isinstance(reason, str) and reason:
            found.append(Long(file, cap if isinstance(cap, int) else None, reason))
    return tuple(found)


def read_ledger(root: Path, held: Settings) -> Ledger:
    """Read the ledger under the root; a missing file is an empty ledger."""
    path = root / held.ledger
    if not path.is_file():
        return Ledger()
    try:
        parsed: dict[str, object] = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as unreadable:
        raise LedgerError(str(unreadable)) from unreadable
    unknown = set(parsed) - {"duplicates", "fallbacks"}
    if unknown:
        msg = f"unknown table {', '.join(sorted(unknown))}"
        raise LedgerError(msg)
    duplicates = _rows(parsed.get("duplicates"), "duplicates")
    found = _rows(parsed.get("fallbacks"), "fallbacks")
    return Ledger(
        tuple(_duplicate_row(row, i) for i, row in enumerate(duplicates)),
        tuple(_fallback_row(row, i) for i, row in enumerate(found)),
    )


def _rows(value: object, table: str) -> list[dict[str, object]]:
    if value is None:
        return []
    if not settings.is_list(value) or not all(settings.is_record(r) for r in value):
        msg = f"{table} must be an array of tables"
        raise LedgerError(msg)
    return [r for r in value if settings.is_record(r)]


def _field(row: dict[str, object], index: int, table: str, key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        msg = f"{table}[{index}]: {key} must be a non-empty string"
        raise LedgerError(msg)
    return value


def _choice(
    row: dict[str, object], index: int, table: str, key: str, among: tuple[str, ...]
) -> str:
    value = _field(row, index, table, key)
    if value not in among:
        msg = f'{table}[{index}]: {key} "{value}" is not one of {", ".join(among)}'
        if key == "class" and value == "dead":
            msg += ". A dead fallback is removed, not judged"
        raise LedgerError(msg)
    return value


def _only(row: dict[str, object], index: int, table: str, keys: tuple[str, ...]) -> None:
    extra = set(row) - set(keys)
    if extra:
        msg = f"{table}[{index}]: unknown key {', '.join(sorted(extra))}"
        raise LedgerError(msg)


def _duplicate_row(row: dict[str, object], index: int) -> DuplicateRow:
    table = "duplicates"
    _only(row, index, table, ("members", "home", "disposition", "why"))
    members = settings.strings(row.get("members"))
    if len(members) < PAIR:
        msg = f"{table}[{index}]: members must list two or more path:qualname strings"
        raise LedgerError(msg)
    return DuplicateRow(
        tuple(sorted(members)),
        _field(row, index, table, "home"),
        _choice(row, index, table, "disposition", DUPLICATE_DISPOSITIONS),
        _field(row, index, table, "why"),
    )


def _fallback_row(row: dict[str, object], index: int) -> FallbackRow:
    table = "fallbacks"
    _only(
        row, index, table, ("site", "where", "form", "code", "count", "class", "disposition", "why")
    )
    count = row.get("count", 1)
    if not isinstance(count, int) or count < 1:
        msg = f"{table}[{index}]: count must be a positive integer"
        raise LedgerError(msg)
    return FallbackRow(
        _field(row, index, table, "site"),
        _field(row, index, table, "where"),
        _choice(row, index, table, "form", fallbacks.FORMS),
        _field(row, index, table, "code"),
        count,
        _choice(row, index, table, "class", CLASSES),
        _choice(row, index, table, "disposition", FALLBACK_DISPOSITIONS),
        _field(row, index, table, "why"),
    )


def families(
    modules: Sequence[facts.Module], protocol_methods: frozenset[str] = frozenset()
) -> list[Family]:
    """Return every group of two or more functions with the same body, worth reporting."""
    protocol = protocol_methods | {n for m in modules for n in m.protocol_methods}
    by_body: defaultdict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for module in modules:
        for function in module.functions:
            if function.statements == 0 or _excluded(function.name, protocol):
                continue
            member = f"{module.path}:{function.qualname}"
            by_body[function.body].append((member, function.name, function.statements))
    found: list[Family] = []
    for group in by_body.values():
        if len(group) < PAIR:
            continue
        names = {name for _, name, _ in group}
        statements = group[0][2]
        if len(names) == 1 or statements >= MIN_SHARED_STATEMENTS:
            found.append(Family(tuple(sorted(member for member, _, _ in group)), statements))
    return sorted(found)


def _excluded(name: str, protocol: frozenset[str]) -> bool:
    return (name.startswith("__") and name.endswith("__")) or name in protocol


def compare_duplicates(found: Sequence[Family], ledger: Ledger) -> Duplicates:
    """Match found families against the ledger's rows, both ways."""
    known = {row.members for row in ledger.duplicates}
    seen = {family.members for family in found}
    return Duplicates(
        new=tuple(family for family in found if family.members not in known),
        stale=tuple(row for row in ledger.duplicates if row.members not in seen),
    )


def compare_fallbacks(found: Sequence[Site], ledger: Ledger) -> Fallbacks:
    """Match found sites against the ledger's rows, counts included, both ways."""
    counts = Counter(site.key for site in found)
    first: dict[SiteKey, Site] = {}
    for site in found:
        first.setdefault(site.key, site)
    known = {row.key: row for row in ledger.fallbacks}
    new = tuple(
        (first[key], count, known[key].count if key in known else 0)
        for key, count in counts.items()
        if key not in known or count > known[key].count
    )
    stale = tuple(
        (row, counts.get(row.key, 0))
        for row in ledger.fallbacks
        if counts.get(row.key, 0) < row.count
    )
    return Fallbacks(new=tuple(sorted(new)), stale=stale)


def offenders(modules: Sequence[facts.Module], held: Settings) -> tuple[Offender, ...]:
    """Return every module over its cap, largest first."""
    caps = {entry.file: entry.cap for entry in held.long}
    found: list[Offender] = []
    for module in modules:
        cap = caps.get(module.path, held.max_code_lines)
        if cap is not None and module.code_lines > cap:
            found.append(Offender(module.path, module.code_lines, cap))
    return tuple(sorted(found, key=lambda o: o.lines, reverse=True))


def check(root: Path, held: Settings) -> Report:
    """Run the three gates over the root and the ledger."""
    modules = facts.scan(root, held.areas)
    ledger = read_ledger(root, held)
    outside: set[str] = set()
    for tree in held.protocols_from:
        outside.update(facts.protocol_methods_under((root / tree).resolve()))
    sites = [s for m in modules if not m.is_test for s in fallbacks.sites(m)]
    present = {module.path for module in modules}
    return Report(
        modules=len(modules),
        rows=len(ledger.fallbacks),
        duplicates=compare_duplicates(families(modules, frozenset(outside)), ledger),
        fallbacks=compare_fallbacks(sites, ledger),
        length=offenders(modules, held),
        drift=tuple(entry.file for entry in held.long if entry.file not in present),
    )


def lines(report: Report) -> list[str]:
    """Describe every problem, one family per block and one site per line."""
    out: list[str] = []
    for family in report.duplicates.new:
        plural = "" if family.statements == 1 else "s"
        out.append(
            f"new duplicate ({family.statements} statement{plural}): keep one copy, "
            "or add a ledger row naming its home:"
        )
        out.extend(f"    {member}" for member in family.members)
    for row in report.duplicates.stale:
        out.append("stale duplicate row: the family is no longer as listed, remove or fix it:")
        out.extend(f"    {member}" for member in row.members)
    for site, found, known in report.fallbacks.new:
        key = site.key
        out.append(
            f"unjudged fallback  {key.site}:{site.line}  in {key.where}  [{key.form}]  "
            f"{key.code}  (found {found}, ledger {known})"
        )
    for row, found in report.fallbacks.stale:
        out.append(
            f"stale fallback row  {row.site}  in {row.where}  [{row.form}]  {row.code}  "
            f"(ledger {row.count}, found {found}): remove or fix it"
        )
    out.extend(
        f"{o.path}: {o.lines} code lines, {o.lines - o.cap} over its cap of {o.cap}"
        for o in report.length
    )
    out.extend(f"the long entry for {f} names a file that is not there" for f in report.drift)
    return out


def skeleton(report: Report) -> str:
    """Return ledger rows for every new family and unjudged site, the judgement left blank."""
    blocks: list[str] = []
    for family in report.duplicates.new:
        members = "\n".join(f"    {_toml(member)}," for member in family.members)
        blocks.append(
            f'[[duplicates]]\nmembers = [\n{members}\n]\nhome = ""\n'
            f'disposition = "move"\nwhy = "{family.statements} statement(s) shared"\n'
        )
    for site, found, _ in report.fallbacks.new:
        key = site.key
        count = f"count = {found}\n" if found > 1 else ""
        blocks.append(
            f"[[fallbacks]]\nsite = {_toml(key.site)}\nwhere = {_toml(key.where)}\n"
            f"form = {_toml(key.form)}\ncode = {_toml(key.code)}\n{count}"
            f'class = ""\ndisposition = ""\nwhy = ""  # line {site.line}\n'
        )
    return "\n".join(blocks)


def _toml(text: str) -> str:
    if '"' not in text and "\\" not in text:
        return f'"{text}"'
    if "'" not in text:
        return f"'{text}'"
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
