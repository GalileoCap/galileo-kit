"""The PostToolUse hook: say which banned tells an edit wrote.

It reads what an Edit, a Write or a Bash call that edited files wrote.

It lists the banned tells on the lines the edit wrote, each with its fix, and
counts the banned tells elsewhere in the file with the command that shows
them. Rationed tells are not mentioned. It never blocks: what it says reaches
the session as context. A file no reader reads, a file outside the project, or
anything unexpected says nothing, and a config the project got wrong is said
in one line.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from session_tells import config as config_module
from session_tells import find, readers
from session_tells.ruleset import RULES

if TYPE_CHECKING:
    from collections.abc import Sequence

    from session_tells.find import Hit
    from session_tells.rules import Rule

HEADER = (
    "Banned prose tells in what this edit wrote. "
    "Rewrite each sentence; swapping the mark is not enough:"
)


def edited(payload: dict[str, Any]) -> dict[str, frozenset[int] | None]:
    """Each file an Edit, a Write or a Bash call wrote, absolute, with the lines it wrote.

    Lines are those of the file as it now stands, counted from 1: each hunk's
    added lines (``+``), placed from its ``newStart`` and counted past its
    context lines (`` ``) and over its removed ones (``-``). The hunks are the
    tool response's ``structuredPatch`` for an Edit or a Write, and each file's
    ``hunks`` in ``bashEditDiff.files`` for a Bash call. An Edit without a patch
    is placed by finding its ``new_string`` in the file. ``None`` means the
    whole file: a Write that created it (no patch), or an edit that cannot be
    placed. A Bash call that edited nothing, or another tool, gives ``{}``.
    """
    tool = payload.get("tool_name")
    given = cast("dict[str, Any]", payload.get("tool_input") or {})
    response = cast("dict[str, Any]", payload.get("tool_response") or {})
    if tool == "Bash":
        diff = cast("dict[str, Any]", response.get("bashEditDiff") or {})
        files = cast("list[dict[str, Any]]", diff.get("files") or [])
        return {
            str(one["filePath"]): _added(cast("list[dict[str, Any]]", one.get("hunks") or []))
            for one in files
            if one.get("filePath")
        }
    if tool not in {"Edit", "Write", "MultiEdit"} or not given.get("file_path"):
        return {}
    path = str(given["file_path"])
    patch = cast("list[dict[str, Any]]", response.get("structuredPatch") or [])
    if patch:
        return {path: _added(patch)}
    if tool == "Edit" and isinstance(given.get("new_string"), str):
        return {path: _placed(path, str(given["new_string"]))}
    return {path: None}


def _added(hunks: list[dict[str, Any]]) -> frozenset[int] | None:
    """Return the new-file line numbers of every ``+`` line in the hunks; ``None`` without hunks."""
    if not hunks:
        return None
    lines: set[int] = set()
    for hunk in hunks:
        line = int(hunk["newStart"])
        for text in cast("list[str]", hunk.get("lines") or []):
            if text.startswith("+"):
                lines.add(line)
                line += 1
            elif not text.startswith(("-", "\\")):
                line += 1
    return frozenset(lines)


def _placed(path: str, new: str) -> frozenset[int] | None:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
    at = text.find(new) if new else -1
    if at == -1:
        return None
    first = text.count("\n", 0, at) + 1
    return frozenset(range(first, first + new.count("\n") + 1))


def message(rel: str, found: Sequence[Hit], lines: frozenset[int] | None) -> str | None:
    """Say what the session is told about one file's banned tells, or ``None`` for nothing to say.

    ``found`` holds the file's banned hits. Those on the ``lines`` written (every
    line when it is ``None``) are listed one per line as
    ``<rel>:<line>  <rule>  '<found>': <fix>``. The others are counted in one
    closing line naming ``session-tells show <rel>``. With nothing on an
    edited line there is nothing to say, whatever the rest of the file holds.
    """
    fixes = {rule.name: rule.fix for rule in RULES}
    written = [hit for hit in found if lines is None or hit.line in lines]
    if not written:
        return None
    said = [
        f"{rel}:{hit.line}  {hit.rule}  {hit.found!r}: {fixes.get(hit.rule, '')}" for hit in written
    ]
    rest = len(found) - len(written)
    if rest:
        said.append(
            f"{rest} more banned tell(s) elsewhere in this file, to remove while you are in it: "
            f"session-tells show {rel}"
        )
    return "\n".join(said)


def respond(payload: dict[str, Any], root: Path) -> dict[str, Any] | None:
    """Return the hook's whole answer to one PostToolUse payload, as the JSON object to print.

    ``root`` is the project root. The answer carries the message as
    ``hookSpecificOutput.additionalContext`` for ``PostToolUse``; ``None``
    means print nothing.
    """
    files = edited(payload)
    if not files:
        return None
    try:
        config = config_module.load(root)
    except config_module.ConfigError as error:
        return _answer(f"session-tells: {error}")
    rules = [rule for rule in config.rules() if rule.kind == "banned"]
    said = [
        one
        for path, lines in files.items()
        if (one := _told(root.resolve(), Path(path).resolve(), lines, config, rules)) is not None
    ]
    if not said:
        return None
    return _answer("\n".join([HEADER, *said]))


def _told(
    root: Path,
    absolute: Path,
    lines: frozenset[int] | None,
    config: config_module.Config,
    rules: Sequence[Rule],
) -> str | None:
    """Say what one edited file's banned tells are, or ``None`` when it is not read."""
    if not absolute.is_relative_to(root):
        return None
    rel = absolute.relative_to(root).as_posix()
    if readers.reader_for(rel, config) is None:
        return None
    try:
        units = readers.read(root, [rel], config)
        source = absolute.read_text(encoding="utf-8", errors="replace")
    except (OSError, readers.CommandError) as error:
        return f"session-tells could not read {rel}: {error}"
    found = find.hits(units, rules, languages=config.languages, allowed={rel: find.markers(source)})
    return message(rel, found, lines)


def _answer(text: str) -> dict[str, Any]:
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}}


def main() -> None:
    """Read the payload on stdin and print the answer, if any. Never raises, always exits 0."""
    try:
        payload = cast("dict[str, Any]", json.load(sys.stdin))
        root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or Path.cwd())
        answer = respond(payload, root)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return
    if answer is not None:
        json.dump(answer, sys.stdout)
