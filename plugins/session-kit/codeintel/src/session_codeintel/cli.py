"""The ``session-codeintel`` command: one subcommand per tool."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

from session_codeintel import layers, looks, measure, pyright_env, quality, recipes, template

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

REFUSED = 2
"""An unknown recipe, or a pyright-env that could write nothing — argparse's usage status."""
PARTIAL = 1
"""A pyright-env that wrote the file, and left some packages out or overridden."""


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``session-codeintel`` command; returns the exit status.

    ``recipes list`` and ``recipes path`` exit 0, or 2 for an unknown recipe.
    ``pyright-env`` exits 0 when every package was written as it is checked,
    1 when some were left out or have settings the root file overrides, 2
    when none could be written. ``looks``, ``layers`` and ``measure`` are in
    ``docs/api.md``.
    """
    args = _parser().parse_args(argv)
    handler: Callable[[argparse.Namespace], int] = _handlers()[args.command]
    return handler(args)


def _handlers() -> dict[str, Callable[[argparse.Namespace], int]]:
    """Map each subcommand to the function that runs it from the parsed arguments."""
    return {
        "recipes": lambda a: _recipes(a.action, a.name if a.action == "path" else ""),
        "pyright-env": lambda a: _pyright_env(Path(a.root)),
        "looks": lambda a: _looks(Path(a.root).resolve()),
        "layers": lambda a: _layers(Path(a.root).resolve()),
        "measure": lambda a: _measure(Path(a.root).resolve(), a.at, a.area, a.skip, a.out),
        "quality": lambda a: _quality(Path(a.root).resolve(), report=a.report),
        "template": _template,
    }


def _recipes(action: str, name: str) -> int:
    """List the recipes, or print one's path; 2 for an unknown name."""
    if action == "list":
        for recipe in recipes.bundled():
            _out(f"{recipe.name}\t{recipe.purpose}")
        return 0
    try:
        _out(str(recipes.find(name).path))
    except recipes.UnknownRecipeError as unknown:
        _err(str(unknown))
        return REFUSED
    return 0


def _pyright_env(root: Path) -> int:
    """Write the config under ``root``; name every package left out or overridden."""
    discovery = pyright_env.write(root)
    for directory in discovery.without_venv:
        _err(f"{directory}: pyproject.toml and no .venv — left out; run `uv sync` there")
    for directory in discovery.overridden:
        _err(
            f"{directory}: checker settings in pyproject.toml, which the root "
            f"{pyright_env.CONFIG} overrides when a checker runs there; "
            f"move them to {directory}/{pyright_env.CONFIG}"
        )
    if not discovery.packages:
        _err(f"{pyright_env.CONFIG}: not written — no package under {root} has a .venv")
        return REFUSED
    _out(f"{pyright_env.CONFIG}: {len(discovery.packages)} package(s)")
    return PARTIAL if discovery.without_venv or discovery.overridden else 0


def _looks(root: Path) -> int:
    """Print the looks written twice and the allowances that drifted; 1 on any."""
    settings = looks.read_settings(root)
    try:
        sites = looks.scan(root, settings)
    except RuntimeError as failed:
        _err(str(failed))
        return REFUSED
    report = looks.check(sites, settings)
    for line in looks.lines(report):
        _out(line)
    return 0 if report.clean else PARTIAL


def _layers(root: Path) -> int:
    """Write the layers pack from the settings; name each file's fate; 1 on a refusal."""
    settings = layers.read_settings(root)
    if settings is None:
        _err(".claude/claude-kit.json: no `layers` block, so nothing to write")
        return REFUSED
    outcome = layers.write(root, layers.render(root, settings))
    for path in outcome.written:
        _out(f"written {path}")
    for path in outcome.unchanged:
        _out(f"unchanged {path}")
    for path in outcome.refused:
        _err(f"refused {path}: it exists and was not written by session-codeintel layers")
    return PARTIAL if outcome.refused else 0


def _measure(
    root: Path, refs: list[str], paths: list[str], skip: list[str], out: str | None
) -> int:
    """Measure the working tree, or each ref's archive, and print or write the report."""
    areas = tuple(measure.Area(p, p, tuple(skip)) for p in paths) or measure.read_areas(root)
    has_settings = (root / ".claude" / "claude-kit.json").is_file()
    looks_settings = looks.read_settings(root) if has_settings else None
    rows: list[measure.Row] = []
    try:
        if refs:
            into = measure.scratch()
            for ref in refs:
                taken = measure.snapshot_of(root, ref, into)
                rows += measure.measure(taken, areas, ref, looks_settings)
        else:
            rows += measure.measure(root, areas, "working tree", looks_settings)
    except RuntimeError as failed:
        _err(str(failed))
        return REFUSED
    text = measure.render(rows, root, f"Code measure of {root.name}")
    if out:
        Path(out).write_text(text, encoding="utf-8")
        _out(f"{out}: {len(rows)} row(s)")
    else:
        _out(text.rstrip("\n"))
    return 0


def _quality(root: Path, *, report: bool) -> int:
    """Run the three gates: the problems and 1, the clean line and 0, or the rows of --report."""
    held = quality.read_settings(root)
    try:
        found = quality.check(root, held)
    except quality.LedgerError as refused:
        _err(f"{held.ledger}: {refused}")
        return REFUSED
    except (FileNotFoundError, SyntaxError) as refused:
        _err(str(refused))
        return REFUSED
    if report:
        _out(quality.skeleton(found).rstrip("\n"))
        return 0
    for line in quality.lines(found):
        _out(line)
    if found.clean:
        _out(
            f"{found.modules} modules: no duplicate, every fallback judged ({found.rows} rows), "
            "every file under its cap"
        )
        return 0
    plural = "" if found.problems == 1 else "s"
    _out(f"{found.problems} problem{plural}")
    return PARTIAL


def _template(args: argparse.Namespace) -> int:
    """Write, refresh or check a project's bar; name each file dealt with or each finding."""
    project = Path(args.dir)
    if args.verb == "new":
        answers = template.Answers(args.name, args.python, docs=args.docs)
        _written(template.new(project, answers))
        return 0
    if args.verb == "refresh":
        if not _written(template.refresh(project)):
            _out("up to date")
        return 0
    findings = template.check(project)
    for finding in findings:
        _err(finding.detail)
    if findings:
        return PARTIAL
    held = version(template.PACKAGE)
    _out(f"{len(template.base_files())} base files match {template.COMMAND} {held}")
    return 0


def _written(written: list[template.Written]) -> bool:
    """Print one line per file dealt with; whether there was any."""
    for one in written:
        note = "  (exists, this project's)" if one.action == "skipped" else ""
        _out(f"{one.action}  {one.path}{note}")
    return bool(written)


def _parser() -> argparse.ArgumentParser:
    """Build the command's parser: seven subcommands, two with actions of their own."""
    parser = argparse.ArgumentParser(prog="session-codeintel")
    commands = parser.add_subparsers(dest="command", required=True)

    recipe = commands.add_parser("recipes", help="the bundled rewrite templates")
    actions = recipe.add_subparsers(dest="action", required=True)
    actions.add_parser("list", help="one line per recipe: its name and its purpose")
    path = actions.add_parser("path", help="the absolute path of one recipe's rule file")
    path.add_argument("name")

    env = commands.add_parser("pyright-env", help="write ROOT/pyrightconfig.json")
    env.add_argument("root", nargs="?", default=".", metavar="ROOT")

    repeated = commands.add_parser(
        "looks", help="the class strings written in more than one place under ROOT's source"
    )
    repeated.add_argument("root", nargs="?", default=".", metavar="ROOT")

    pack = commands.add_parser("layers", help="write the pure-core rules from ROOT's settings")
    pack.add_argument("root", nargs="?", default=".", metavar="ROOT")

    sizes = commands.add_parser("measure", help="size, complexity and repetition per area")
    sizes.add_argument("root", nargs="?", default=".", metavar="ROOT")
    sizes.add_argument(
        "--at", action="append", default=[], metavar="REF", help="a git ref to archive"
    )
    sizes.add_argument(
        "--area", action="append", default=[], metavar="PATH", help="an area to measure"
    )
    sizes.add_argument(
        "--skip", action="append", default=[], metavar="PATH", help="left out of each area"
    )
    sizes.add_argument("--out", metavar="FILE", help="write the report there")

    gates = commands.add_parser("quality", help="the duplicate, fallback and file-length gates")
    gates.add_argument("root", nargs="?", default=".", metavar="ROOT")
    gates.add_argument("--report", action="store_true", help="print ledger rows to fill in")

    bar = commands.add_parser("template", help="the quality bar as base files a project extends")
    verbs = bar.add_subparsers(dest="verb", required=True)
    started = verbs.add_parser("new", help="start a project, or give an existing one the bar")
    started.add_argument("dir", help="the project's directory")
    started.add_argument("--name", required=True, help="the distribution name")
    started.add_argument("--python", default="3.12", help="the Python floor")
    started.add_argument(
        "--no-docs", dest="docs", action="store_false", help="leave out the five pages"
    )
    refreshed = verbs.add_parser("refresh", help="write the base files back from the template")
    refreshed.add_argument("dir", help="the project's directory")
    checked = verbs.add_parser("check", help="fail when a base file drifts from the template")
    checked.add_argument("dir", help="the project's directory")
    return parser


def _out(line: str) -> None:
    sys.stdout.write(f"{line}\n")


def _err(line: str) -> None:
    sys.stderr.write(f"{line}\n")
