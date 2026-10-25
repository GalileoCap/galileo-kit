"""The ledger check over a project's suppressions and type escapes.

A suppression (the noqa and ignore comments of ruff, mypy and pyright, the
ts-ignore and expect-error directives, the eslint, oxlint and biome disables,
and the any and unknown casts) needs the owner's approval, and the approval
lives as a numbered row in the project's decisions file. ``session-suppressions
list`` prints every marker in the tree's source files with the row it cites,
and ``check`` prints one line per problem and exits 1: a marker that cites no
row, on its own line or the line above, and a citation whose row the ledger
lacks. ``.claude/claude-kit.json`` may set, under ``suppressions``, the
``ledger`` path (``docs/decisions.md``), the ``cite`` pattern whose first
group is the row's number (``decisions\\.md,?\\s*(\\d+)``) and the ``skip``
directories. A rule relaxed in a config file is outside this check. Prose
files, the ledger itself, dependencies and virtual environments (a directory
holding ``pyvenv.cfg`` or named ``site-packages``) are never read for markers.
A marker inside a string or a docstring is a mention, a test's fixture or a
reader's pattern, and is no site: Python files are read through the
tokenizer and only their comments are searched, and in a TypeScript or
JavaScript file the string literals of a line are dropped before the search,
with a directive counted only in the line's comment.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

SOURCE_SUFFIXES = {".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".direnv", ".ruff_cache", ".pytest_cache"}
DEFAULT_LEDGER = "docs/decisions.md"
DEFAULT_CITE = r"decisions\.md,?\s*(\d+)"

# Each marker's pattern is built from pieces, so this file holds none of them whole.
MARKERS: list[tuple[str, re.Pattern[str]]] = [
    ("noqa", re.compile("#" + r"\s*(?:ruff:\s*)?" + "noqa" + r"\b")),
    ("type: " + "ignore", re.compile("#" + r"\s*type:\s*" + "ignore" + r"\b")),
    ("pyright: " + "ignore", re.compile("#" + r"\s*pyright:\s*" + "ignore" + r"\b")),
    ("@ts-" + "ignore", re.compile("@ts-" + "ignore" + r"\b")),
    ("@ts-" + "expect-error", re.compile("@ts-" + "expect-error" + r"\b")),
    ("eslint-" + "disable", re.compile("eslint-" + "disable")),
    ("oxlint-" + "disable", re.compile("oxlint-" + "disable")),
    ("biome-" + "ignore", re.compile("biome-" + "ignore")),
    ("as " + "any", re.compile(r"\bas\s+" + "any" + r"\b")),
    ("as unknown " + "as", re.compile(r"\bas\s+unknown\s+" + "as" + r"\b")),
]


@dataclass
class Settings:
    ledger: str = DEFAULT_LEDGER
    cite: re.Pattern[str] = re.compile(DEFAULT_CITE)
    skip: frozenset[str] = frozenset(SKIP_DIRS)


@dataclass
class Site:
    path: Path
    line: int
    marker: str
    row: int | None


def read_settings(root: Path) -> Settings:
    settings = Settings()
    try:
        parsed = json.loads((root / ".claude" / "claude-kit.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return settings
    block = parsed.get("suppressions") if isinstance(parsed, dict) else None
    if not isinstance(block, dict):
        return settings
    if isinstance(block.get("ledger"), str) and block["ledger"]:
        settings.ledger = block["ledger"]
    if isinstance(block.get("cite"), str) and block["cite"]:
        settings.cite = re.compile(block["cite"])
    if isinstance(block.get("skip"), list):
        settings.skip = frozenset(SKIP_DIRS | {s for s in block["skip"] if isinstance(s, str)})
    return settings


def is_environment(directory: Path) -> bool:
    """A virtual environment or an installed package tree, whatever it is named."""
    return directory.name == "site-packages" or (directory / "pyvenv.cfg").is_file()


def source_files(root: Path, settings: Settings) -> list[Path]:
    ledger = (root / settings.ledger).resolve()
    out: list[Path] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        for path in sorted(directory.iterdir()):
            if path.is_dir():
                if path.name not in settings.skip and not is_environment(path):
                    pending.append(path)
            elif path.suffix in SOURCE_SUFFIXES and path.resolve() != ledger:
                out.append(path)
    return sorted(out)


def cited_row(lines: list[str], index: int, cite: re.Pattern[str]) -> int | None:
    for candidate in (lines[index], lines[index - 1] if index > 0 else ""):
        m = cite.search(candidate)
        if m:
            return int(m.group(1))
    return None


COMMENT_MARKERS = {name for name, _ in MARKERS if name.startswith(("@ts-", "eslint-", "oxlint-", "biome-"))}
STRINGS = re.compile(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`")


def python_comments(text: str) -> dict[int, str]:
    """Each comment of a Python file by its line, through the tokenizer; every line on a tokenize error."""
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError):
        return {n + 1: line for n, line in enumerate(text.splitlines())}
    return {tok.start[0]: tok.string for tok in tokens if tok.type == tokenize.COMMENT}


def script_parts(line: str) -> tuple[str, str]:
    """A TypeScript or JavaScript line without its string literals, split into its code and its comment."""
    bare = STRINGS.sub("''", line)
    at = min((i for i in (bare.find("//"), bare.find("/*")) if i >= 0), default=-1)
    return (bare, "") if at < 0 else (bare[:at], bare[at:])


def searchable(path: Path, lines: list[str]) -> dict[int, list[tuple[str, str]]]:
    """Per line, the texts to search and which markers apply to each."""
    if path.suffix in {".py", ".pyi"}:
        return {n: [(comment, "comment")] for n, comment in python_comments("\n".join(lines) + "\n").items()}
    out: dict[int, list[tuple[str, str]]] = {}
    for n, line in enumerate(lines, start=1):
        code, comment = script_parts(line)
        out[n] = [(code, "code"), (comment, "comment")]
    return out


def sites_in(path: Path, settings: Settings) -> list[Site]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    found: list[Site] = []
    for n, parts in sorted(searchable(path, lines).items()):
        for text, kind in parts:
            for name, pattern in MARKERS:
                if (name in COMMENT_MARKERS) != (kind == "comment") and path.suffix not in {".py", ".pyi"}:
                    continue
                if pattern.search(text):
                    found.append(Site(path, n, name, cited_row(lines, n - 1, settings.cite)))
    return found


def ledger_rows(root: Path, settings: Settings) -> dict[int, str] | None:
    """Each row's number and the heading it sits under; None when the ledger is missing."""
    path = root / settings.ledger
    if not path.is_file():
        return None
    rows: dict[int, str] = {}
    heading = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
        m = re.match(r"^\|\s*(\d+)\s*\|", line)
        if m:
            rows[int(m.group(1))] = heading
    return rows


def describe(site: Site, root: Path, rows: dict[int, str] | None) -> str:
    where = f"{site.path.relative_to(root)}:{site.line}"
    if site.row is None:
        return f"{where}  {site.marker}  uncited"
    under = rows.get(site.row) if rows else None
    return f"{where}  {site.marker}  row {site.row}" + (f" ({under})" if under else " (no such row)")


def problems(sites: list[Site], root: Path, rows: dict[int, str] | None, settings: Settings) -> list[str]:
    out: list[str] = []
    for site in sites:
        where = f"{site.path.relative_to(root)}:{site.line}"
        if site.row is None:
            out.append(f"{where}: `{site.marker}` cites no row of {settings.ledger} on its line or the line above")
        elif rows is None:
            out.append(f"{where}: `{site.marker}` cites row {site.row}, and {settings.ledger} does not exist")
        elif site.row not in rows:
            out.append(f"{where}: `{site.marker}` cites row {site.row}, which {settings.ledger} does not hold")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="The ledger check over a project's suppressions.")
    parser.add_argument("command", choices=("list", "check"))
    parser.add_argument("--root", default=".", help="the project root; its .claude/claude-kit.json applies")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    settings = read_settings(root)
    rows = ledger_rows(root, settings)
    sites = [s for path in source_files(root, settings) for s in sites_in(path, settings)]
    if args.command == "list":
        for site in sites:
            print(describe(site, root, rows))
        print(f"{len(sites)} suppressions" + ("" if rows is not None else f", and {settings.ledger} does not exist"))
        return 0
    found = problems(sites, root, rows, settings)
    for p in found:
        print(p)
    if not found:
        print(f"{len(sites)} suppressions, every one with its row in {settings.ledger}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
