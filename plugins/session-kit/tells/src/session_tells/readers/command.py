"""A project's own reader: a command that prints the prose in the files it is handed.

The command runs from its ``under`` directory with the files as arguments,
relative to that directory, and prints one JSON object::

    {"units": [{"path": "src/app.ts", "text": "comment", "pieces": [[3, "words"]]}]}

``path`` is relative to ``under`` too, ``text`` is ``comment`` or ``copy``, and
each piece is ``[line, text]`` counted from 1. Every unit comes back with its
path relative to the project root and the role ``text``.
"""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING, cast

from session_tells.readers.common import carries_words
from session_tells.units import Unit

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from session_tells.config import Command


class CommandError(Exception):
    """The command could not be run, exited non-zero, or printed something else.

    The message names the command and its stderr, never the list of files.
    """


def run(root: Path, command: Command, files: Sequence[str]) -> list[Unit]:
    """Run ``command`` over ``files`` (root-relative, each under ``command.under``).

    Units that carry no words are left out, as every reader leaves them.
    """
    named = " ".join(command.run)
    try:
        # The argv is the project's own config and paths it chose; no shell between.
        done = subprocess.run(  # noqa: S603
            [*command.run, *(one.removeprefix(command.under) for one in files)],
            cwd=root / command.under,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        msg = f"{named!r} could not run: {error}"
        raise CommandError(msg) from error
    if done.returncode != 0:
        msg = f"{named!r} exited {done.returncode}: {done.stderr.strip()}"
        raise CommandError(msg)
    try:
        printed = cast("dict[str, list[dict[str, object]]]", json.loads(done.stdout))
        units = [
            Unit(
                command.under + cast("str", one["path"]),
                "copy" if one["text"] == "copy" else "comment",
                "text",
                tuple(
                    (int(line), str(text))
                    for line, text in cast("list[tuple[int, str]]", one["pieces"])
                ),
            )
            for one in printed["units"]
        ]
    except (ValueError, KeyError, TypeError) as error:
        msg = f"{named!r} printed something other than units: {error}"
        raise CommandError(msg) from error
    return [unit for unit in units if carries_words(unit)]
