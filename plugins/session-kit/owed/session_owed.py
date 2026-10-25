"""What a change leaves to do outside the code, read across a range of history.

A change can leave a step nobody's code runs: a key to set on an instance,
a command to run once after a deploy, a tool every worktree has to upgrade.
``OWED.md`` at the project's root holds one entry per such change, written
by hand in the commit that makes it owed, under a ``###`` heading naming
the branch, the commit and the change, inside a ``##`` section naming when
it is due (at a deploy, in every worktree). The file is only ever appended
to, so what a range of history owes is the entries the file holds at its
end and did not hold at its start. ``session-owed --since <ref> [--until
<ref>]`` prints them by section, the working file standing for ``--until``
when it is not given, and fails on an entry the range removed, which is the
one half of the rule a program can hold. ``.claude/claude-kit.json`` may
name the file under ``owed`` as ``file``. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_FILE = "OWED.md"


def read_file_name(root: Path) -> str:
    try:
        parsed = json.loads((root / ".claude" / "claude-kit.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return DEFAULT_FILE
    block = parsed.get("owed") if isinstance(parsed, dict) else None
    name = block.get("file") if isinstance(block, dict) else None
    return name if isinstance(name, str) and name else DEFAULT_FILE


def entries(text: str) -> list[tuple[str, str, str]]:
    """The file's entries as (section, heading, body), in file order."""
    found: list[tuple[str, str, str]] = []
    section = ""
    heading: str | None = None
    body: list[str] = []

    def close() -> None:
        if heading is not None:
            found.append((section, heading, "\n".join(body).strip("\n")))

    for line in text.splitlines():
        if line.startswith("## "):
            close()
            section, heading, body = line[3:].strip(), None, []
        elif line.startswith("### "):
            close()
            heading, body = line[4:].strip(), []
        elif heading is not None:
            body.append(line)
    close()
    return found


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False, timeout=30)


def text_at(root: Path, ref: str, name: str) -> str:
    """The file as it stood at the ref, empty when the ref did not hold it.

    Raises ValueError when git does not know the ref.
    """
    known = git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if known.returncode != 0:
        raise ValueError(f"{ref}: not a commit git knows")
    shown = git(root, "show", f"{ref}:{name}")
    return shown.stdout if shown.returncode == 0 else ""


def working_text(root: Path, name: str) -> str:
    path = root / name
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def gained_and_removed(
    before: str, after: str
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]]]:
    """The entries after holds and before did not, and the headings before held that are gone."""
    held = {(section, heading) for section, heading, _ in entries(before)}
    now = entries(after)
    present = {(section, heading) for section, heading, _ in now}
    gained = [e for e in now if (e[0], e[1]) not in held]
    removed = [key for key in ((s, h) for s, h, _ in entries(before)) if key not in present]
    return gained, removed


def render(found: list[tuple[str, str, str]]) -> str:
    blocks: list[str] = []
    last: str | None = None
    for section, heading, body in found:
        if section != last:
            blocks.append(f"## {section}")
            last = section
        blocks.append(f"### {heading}\n\n{body}" if body else f"### {heading}")
    return "\n\n".join(blocks) + "\n" if blocks else ""


def main() -> int:
    parser = argparse.ArgumentParser(prog="session-owed", description="what a range of history owes")
    parser.add_argument("--root", default=".", help="the repository (default: the current directory)")
    parser.add_argument("--since", help="the ref before the range; without it, everything is owed")
    parser.add_argument("--until", help="the ref ending the range (default: the working file)")
    parser.add_argument("--section", help="keep one section, by its heading")
    parser.add_argument("--file", help="the file's name (default: owed.file in the settings, or OWED.md)")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    name = args.file or read_file_name(root)
    try:
        before = text_at(root, args.since, name) if args.since else ""
        after = text_at(root, args.until, name) if args.until else working_text(root, name)
    except ValueError as unknown:
        print(f"session-owed: {unknown}", file=sys.stderr)
        return 2
    gained, removed = gained_and_removed(before, after)
    if args.section:
        gained = [e for e in gained if e[0] == args.section]
        removed = [key for key in removed if key[0] == args.section]
    sys.stdout.write(render(gained))
    for _, heading in removed:
        print(f"removed: {heading}", file=sys.stderr)
    return 1 if removed else 0


if __name__ == "__main__":
    sys.exit(main())
