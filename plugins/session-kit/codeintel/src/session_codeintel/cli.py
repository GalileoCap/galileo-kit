"""The ``session-codeintel`` command: ``recipes``, ``pyright-env`` and ``looks``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from session_codeintel import looks, pyright_env, recipes

if TYPE_CHECKING:
    from collections.abc import Sequence

REFUSED = 2
"""An unknown recipe, or a pyright-env that could write nothing — argparse's usage status."""
PARTIAL = 1
"""A pyright-env that wrote the file, and left some packages out or overridden."""


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``session-codeintel`` command; returns the exit status.

    ``recipes list`` and ``recipes path`` exit 0, or 2 for an unknown recipe.
    ``pyright-env`` exits 0 when every package was written as it is checked,
    1 when some were left out or have settings the root file overrides, 2
    when none could be written.
    """
    args = _parser().parse_args(argv)
    if args.command == "pyright-env":
        return _pyright_env(Path(args.root))
    if args.command == "looks":
        return _looks(Path(args.root).resolve())
    if args.action == "list":
        for recipe in recipes.bundled():
            _out(f"{recipe.name}\t{recipe.purpose}")
        return 0
    try:
        _out(str(recipes.find(args.name).path))
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


def _parser() -> argparse.ArgumentParser:
    """Build the command's parser: three subcommands, one of them with two actions."""
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
    return parser


def _out(line: str) -> None:
    sys.stdout.write(f"{line}\n")


def _err(line: str) -> None:
    sys.stderr.write(f"{line}\n")
