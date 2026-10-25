"""Every document is named by the project's index.

A project's document list rots: a file is added under ``docs/`` and the
``CLAUDE.md`` line that would send a reader to it is never written, or the
file is renamed and the line stays. ``session-docs check`` reads every
``.md`` under the documents directory and fails on one that no index names,
and on a document an index names that does not exist. An index names a
document by writing its path (``docs/plan.md``), or the path of a directory
above it with its trailing slash (``docs/intent/``), which covers a set of
files one line describes, such as a generated one or one per review. The
documents directory alone (``docs/``) covers nothing. A path inside a fenced
code block is an example and names nothing for the second half of the
check. ``.claude/claude-kit.json`` may set, under ``docs``, the ``root``
(``docs``) and the ``indexes`` that must each name every document
(``CLAUDE.md``). Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

FENCE = re.compile(r"^\s*(```|~~~)")


@dataclass
class Settings:
    root: str = "docs"
    indexes: list[str] = field(default_factory=lambda: ["CLAUDE.md"])


def read_settings(root: Path) -> Settings:
    settings = Settings()
    try:
        parsed = json.loads((root / ".claude" / "claude-kit.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return settings
    block = parsed.get("docs") if isinstance(parsed, dict) else None
    if not isinstance(block, dict):
        return settings
    if isinstance(block.get("root"), str) and block["root"]:
        settings.root = block["root"].strip("/")
    if isinstance(block.get("indexes"), list) and block["indexes"]:
        settings.indexes = [i for i in block["indexes"] if isinstance(i, str)]
    return settings


def documents(root: Path, settings: Settings) -> list[str]:
    """Every markdown file under the documents directory, as a path from the root."""
    directory = root / settings.root
    if not directory.is_dir():
        return []
    return sorted(p.relative_to(root).as_posix() for p in directory.rglob("*.md") if p.is_file())


def covers(text: str, document: str, docs_root: str) -> bool:
    """Whether the text names the document, by its path or a directory's above it."""
    if document in text:
        return True
    parts = document.split("/")
    for depth in range(len(parts) - 1, 1, -1):
        prefix = "/".join(parts[:depth]) + "/"
        if prefix != docs_root + "/" and prefix in text:
            return True
    return False


def outside_fences(text: str) -> str:
    kept: list[str] = []
    inside = False
    for line in text.splitlines():
        if FENCE.match(line):
            inside = not inside
            continue
        if not inside:
            kept.append(line)
    return "\n".join(kept)


def named(text: str, docs_root: str) -> list[str]:
    """The document paths the text names outside its code blocks."""
    pattern = re.compile(r"(?<![\w/.-])" + re.escape(docs_root) + r"/[\w./-]+\.md\b")
    return sorted(set(pattern.findall(outside_fences(text))))


def problems(root: Path, settings: Settings) -> list[str]:
    found: list[str] = []
    docs = documents(root, settings)
    for index in settings.indexes:
        path = root / index
        if not path.is_file():
            found.append(f"{index}: missing, so it names no document")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        found += [f"{index} does not name {d}" for d in docs if not covers(text, d, settings.root)]
        found += [f"{index} names {d}, which does not exist" for d in named(text, settings.root) if not (root / d).is_file()]
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Every document under docs/ is named by the index, and every one named exists.")
    parser.add_argument("command", choices=("check",))
    parser.add_argument("--root", default=".", help="the project root; its .claude/claude-kit.json applies")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    settings = read_settings(root)
    found = problems(root, settings)
    for p in found:
        print(p)
    if not found:
        print(f"{len(documents(root, settings))} documents, every one named by {', '.join(settings.indexes)}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
