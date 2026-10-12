"""``session-tells``: the tells in a project's files, from the command line or the hook.

    session-tells show [--root DIR] FILE...    every tell, banned and rationed, with its fix
    session-tells check [--root DIR] FILE...   the banned ones; exits 1 when there are any
    session-tells hook                          the PostToolUse hook, payload on stdin

``--root`` is the project root (default: the current directory), whose
``.claude/claude-kit.json`` is read, and the files are given relative to it or
absolute inside it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from session_tells import config as config_module
from session_tells import find, hook, readers


def main(argv: list[str] | None = None) -> int:
    """Run one verb and return its exit status."""
    parser = argparse.ArgumentParser(prog="session-tells")
    verbs = parser.add_subparsers(dest="verb", required=True)
    for verb, what in (
        ("show", "every tell, banned and rationed, with its fix"),
        ("check", "the banned tells; exits 1 when there are any"),
    ):
        one = verbs.add_parser(verb, help=what)
        one.add_argument("--root", type=Path, default=Path.cwd())
        one.add_argument("files", nargs="+")
    verbs.add_parser("hook", help="the PostToolUse hook, payload on stdin")
    args = parser.parse_args(argv)
    if args.verb == "hook":
        hook.main()
        return 0
    root: Path = args.root.resolve()
    try:
        config = config_module.load(root)
    except config_module.ConfigError as error:
        sys.stderr.write(f"session-tells: {error}\n")
        return 2
    rules = config.rules()
    if args.verb == "check":
        rules = tuple(rule for rule in rules if rule.kind == "banned")
    files = [_relative(root, one) for one in args.files]
    try:
        units = readers.read(root, files, config)
    except readers.CommandError as error:
        sys.stderr.write(f"session-tells: {error}\n")
        return 2
    allowed = {
        rel: find.markers((root / rel).read_text(encoding="utf-8", errors="replace"))
        for rel in files
        if (root / rel).is_file()
    }
    found = find.hits(units, rules, languages=config.languages, allowed=allowed)
    fixes = {rule.name: rule.fix for rule in rules}
    for hit in found:
        sys.stdout.write(f"{hit.path}:{hit.line}  {hit.rule}  {hit.found!r}: {fixes[hit.rule]}\n")
    return 1 if args.verb == "check" and found else 0


def _relative(root: Path, given: str) -> str:
    path = Path(given)
    if path.is_absolute():
        return path.resolve().relative_to(root).as_posix()
    return path.as_posix()
