"""The rulebook against its word budget.

Every turn loads the rules: the user's ``~/.claude/CLAUDE.md`` and the
project's ``CLAUDE.md``, each with the files its ``@path`` lines import, the
files under ``.claude/rules/``, and ``CLAUDE.local.md``. A skill is loaded
when its work starts, so the skills are a budget of their own. Instruction
following degrades as instructions stack, so each group has a budget, and
``session-rulebook`` counts the words of each file, prints the two totals
against their budgets, and exits 1 when one is over: a rule that takes the
rulebook over its budget removes another. ``.claude/claude-kit.json`` may
set, under ``rulebook``, the ``rules`` and ``skills`` budgets in words and
``skills_from``, globs of further skill files from the root (a plugin
repository names its own). Standard library only.

The budget is in words, which the standard library counts. Beside them, the
engine's own token estimate of each memory file a turn loads is read from
the timeline session-kit's module writes under
``~/.claude/session-kit/measure/`` (its ``memory`` lines), the newest that
lists a file of this project. A file the engine loads and the rulebook does
not count (auto memory, a managed file) is listed apart.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

RULES_BUDGET = 7500
SKILLS_BUDGET = 16000
IMPORT_DEPTH = 5
MEASURE_DIR = Path.home() / ".claude" / "session-kit" / "measure"


@dataclass
class Settings:
    rules: int = RULES_BUDGET
    skills: int = SKILLS_BUDGET
    skills_from: list[str] = field(default_factory=list)


def read_settings(root: Path) -> Settings:
    settings = Settings()
    try:
        parsed = json.loads((root / ".claude" / "claude-kit.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return settings
    block = parsed.get("rulebook") if isinstance(parsed, dict) else None
    if not isinstance(block, dict):
        return settings
    if isinstance(block.get("rules"), int):
        settings.rules = block["rules"]
    if isinstance(block.get("skills"), int):
        settings.skills = block["skills"]
    if isinstance(block.get("skills_from"), list):
        settings.skills_from = [g for g in block["skills_from"] if isinstance(g, str)]
    return settings


def with_imports(path: Path, seen: set[Path], depth: int = 0) -> list[Path]:
    """The file and, in order, the files its ``@path`` lines import, each once."""
    resolved = path.resolve()
    if resolved in seen or not path.is_file():
        return []
    seen.add(resolved)
    found = [path]
    if depth >= IMPORT_DEPTH:
        return found
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("@") or line.startswith("@@"):
            continue
        target = line[1:].strip()
        if not target:
            continue
        imported = Path(target).expanduser()
        if not imported.is_absolute():
            imported = path.parent / imported
        found += with_imports(imported, seen, depth + 1)
    return found


def rule_files(root: Path, claude_dir: Path) -> list[Path]:
    seen: set[Path] = set()
    found = with_imports(claude_dir / "CLAUDE.md", seen)
    found += with_imports(root / "CLAUDE.md", seen)
    found += [p for p in sorted((root / ".claude" / "rules").rglob("*.md")) if p.resolve() not in seen]
    found += with_imports(root / "CLAUDE.local.md", seen)
    return found


def skill_files(root: Path, settings: Settings) -> list[Path]:
    found = sorted((root / ".claude" / "skills").glob("*/SKILL.md"))
    for pattern in settings.skills_from:
        found += sorted(root.glob(pattern))
    return found


def words(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").split())


def shown(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        pass
    try:
        return "~/" + str(path.resolve().relative_to(Path.home()))
    except ValueError:
        return str(path)


@dataclass
class Measured:
    """One memory line of the timeline: the session it came from and each file's tokens, by resolved path."""
    session: str
    tokens: dict[Path, int]
    kinds: dict[Path, str]


def memory_line(text: str, session: str) -> Measured | None:
    """The last memory line of a timeline file, or None."""
    for line in reversed(text.splitlines()):
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict) or record.get("ev") != "memory" or not isinstance(record.get("files"), list):
            continue
        measured = Measured(session, {}, {})
        for f in record["files"]:
            if isinstance(f, dict) and isinstance(f.get("path"), str) and isinstance(f.get("tokens"), int):
                path = Path(f["path"]).resolve()
                measured.tokens[path] = f["tokens"]
                measured.kinds[path] = str(f.get("type") or "?")
        return measured
    return None


def latest_measured(measure_dir: Path, wanted: set[Path]) -> Measured | None:
    """The newest memory line that lists one of the wanted files. A timeline file is named for the epoch milliseconds it was written at."""
    for path in sorted(measure_dir.glob("*/*.jsonl"), key=lambda p: p.name, reverse=True):
        try:
            measured = memory_line(path.read_text(encoding="utf-8", errors="replace"), path.parent.name)
        except OSError:
            continue
        if measured is not None and wanted & measured.tokens.keys():
            return measured
    return None


def report(name: str, files: list[Path], budget: int, root: Path, measured: Measured | None = None) -> tuple[list[str], bool]:
    counted = [(words(p), p) for p in files]
    total = sum(n for n, _ in counted)
    lines = []
    for n, p in counted:
        tokens = measured.tokens.get(p.resolve()) if measured else None
        lines.append(f"{n:>7}  {shown(p, root)}" + (f"  ({tokens:,} tokens)" if tokens is not None else ""))
    over = total > budget
    verdict = f"over its budget of {budget:,}" if over else f"of {budget:,} words"
    lines.append(f"{name}: {total:,} words {verdict}" if over else f"{name}: {total:,} {verdict}")
    return lines, over


def engine_report(measured: Measured, counted: list[Path], root: Path) -> list[str]:
    """What the engine loads that the rulebook does not count, and the engine's total."""
    known = {p.resolve() for p in counted}
    lines = [
        f"{n:>7}  {shown(p, root)}  ({n:,} tokens, {measured.kinds[p]}, loaded by the engine and not counted)"
        for p, n in measured.tokens.items() if p not in known
    ]
    lines.append(f"engine: {sum(measured.tokens.values()):,} tokens of memory files, as session {measured.session[:8]} measured them")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="The rulebook's word count against its budget.")
    parser.add_argument("--root", default=".", help="the project root; its .claude/claude-kit.json applies")
    parser.add_argument("--claude-dir", default=str(Path.home() / ".claude"), help="the user's Claude directory, whose CLAUDE.md every session loads")
    parser.add_argument("--measure-dir", default=str(MEASURE_DIR), help="the timeline session-kit's module writes, read for the engine's token counts")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    settings = read_settings(root)
    rules = rule_files(root, Path(args.claude_dir).expanduser())
    ours = {p.resolve() for p in rules if p.resolve().is_relative_to(root)}
    measured = latest_measured(Path(args.measure_dir).expanduser(), ours)
    rules_lines, rules_over = report("rules", rules, settings.rules, root, measured)
    skills_lines, skills_over = report("skills", skill_files(root, settings), settings.skills, root)
    engine_lines = engine_report(measured, rules, root) if measured else []
    for line in rules_lines + skills_lines + engine_lines:
        print(line)
    return 1 if rules_over or skills_over else 0


if __name__ == "__main__":
    sys.exit(main())
