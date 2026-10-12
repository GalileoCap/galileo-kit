"""Find the prose in a project's files: Markdown always, the rest as the project turns it on."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from session_tells.readers import markdown, python, rust, typescript
from session_tells.readers.command import CommandError, run

__all__ = ["CommandError", "read", "reader_for"]

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from session_tells.config import Command, Config
    from session_tells.units import Unit

_READERS: dict[str, tuple[frozenset[str], Callable[[str, str], list[Unit]]]] = {
    "python": (python.SUFFIXES, python.python),
    "typescript": (typescript.SUFFIXES, typescript.typescript),
    "rust": (rust.SUFFIXES, rust.rust),
}


def reader_for(rel: str, config: Config) -> str | None:
    """Name the reader for one root-relative file, or ``None`` when nothing reads it.

    A project's command wins for the files under its prefix with its suffixes;
    it is named ``command``. Otherwise Markdown always reads ``.md`` and
    ``.markdown``, and ``python``, ``typescript`` and ``rust`` read their
    suffixes when the config turns them on.
    """
    if _command_for(rel, config) is not None:
        return "command"
    suffix = PurePosixPath(rel).suffix
    if suffix in markdown.SUFFIXES:
        return "markdown"
    for name in sorted(config.readers):
        if suffix in _READERS[name][0]:
            return name
    return None


def _command_for(rel: str, config: Config) -> Command | None:
    suffix = PurePosixPath(rel).suffix
    return next(
        (one for one in config.commands if rel.startswith(one.under) and suffix in one.suffixes),
        None,
    )


def read(root: Path, files: Sequence[str], config: Config) -> list[Unit]:
    """Every unit of prose in ``files`` (root-relative), in the order the files are given.

    A file no reader reads, or that is missing, is skipped. The files of one
    command go to it in one run. A Markdown file under one of the config's
    ``guide`` prefixes reads as the guide.
    """
    units: list[Unit] = []
    batches: dict[Command, list[str]] = {}
    for rel in files:
        name = reader_for(rel, config)
        path = root / rel
        if name is None or not path.is_file():
            continue
        if name == "command":
            command = _command_for(rel, config)
            if command is not None:
                batches.setdefault(command, []).append(rel)
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        if name == "markdown":
            units.extend(markdown.markdown(rel, source, guide=rel.startswith(config.guide)))
        else:
            units.extend(_READERS[name][1](rel, source))
    for command, batch in batches.items():
        units.extend(run(root, command, batch))
    return units
