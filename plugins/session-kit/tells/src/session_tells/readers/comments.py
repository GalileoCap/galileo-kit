"""Comments found by tree-sitter, cut into units the way a person reads them.

Shared by the C-family readers. Line comments of one kind, each alone on its
line, on consecutive lines, are one unit. A block comment is one unit. A
comment after code on its line is a unit of its own. Markers, each block line's
leading ``*``, pragmas and, in doc comments, fenced code are left out.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from session_tells.readers.common import carries_words, without_code
from session_tells.units import Unit

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from tree_sitter import Node

FENCE = re.compile(r"^(```|~~~)")


@dataclass(frozen=True)
class Style:
    """How one language writes its comments."""

    node_types: frozenset[str]
    line_markers: tuple[str, ...]
    """Longest first: ``///`` before ``//``."""
    doc_markers: frozenset[str]
    """The markers whose comments are Markdown, so fenced code in them is not prose."""
    pragma: re.Pattern[str] | None = None


@dataclass(frozen=True)
class _Comment:
    row: int
    """Counted from 0, as tree-sitter counts."""
    alone: bool
    text: str


def comment_units(rel: str, source: bytes, root: Node, style: Style) -> list[Unit]:
    """Every unit of prose in the comments under ``root``, in file order."""
    lines = source.split(b"\n")
    found = [
        _Comment(
            node.start_point.row,
            not lines[node.start_point.row][: node.start_point.column].strip(),
            (node.text or b"").decode("utf-8", "replace"),
        )
        for node in _walk(root, style.node_types)
    ]
    units: list[Unit] = []
    run: list[tuple[int, str]] = []
    run_marker = ""
    last_row = -2
    for comment in found:
        marker = next((m for m in style.line_markers if comment.text.startswith(m)), None)
        joins = (
            marker is not None
            and comment.alone
            and marker == run_marker
            and comment.row == last_row + 1
        )
        if run and not joins:
            units.extend(_unit(rel, run, run_marker, style))
            run = []
        if marker is None:
            units.extend(_unit(rel, _block(comment), _block_marker(comment.text), style))
            run_marker = ""
            continue
        body = comment.text[len(marker) :].rstrip("\r\n")
        if style.pragma is not None and style.pragma.match(body.strip()):
            run_marker = ""
            last_row = -2
            continue
        run.append((comment.row + 1, body))
        run_marker = marker if comment.alone else ""
        last_row = comment.row if comment.alone else -2
        if not comment.alone:
            units.extend(_unit(rel, run, marker, style))
            run = []
    if run:
        units.extend(_unit(rel, run, run_marker, style))
    return sorted(
        (unit for unit in units if carries_words(unit)), key=lambda unit: unit.pieces[0][0]
    )


def _walk(node: Node, types: frozenset[str]) -> Iterator[Node]:
    if node.type in types:
        yield node
        return
    for child in node.children:
        yield from _walk(child, types)


def _block_marker(text: str) -> str:
    for marker in ("/**", "/*!", "/*"):
        if text.startswith(marker) and not text.startswith("/**/"):
            return marker
    return "/*"


def _block(comment: _Comment) -> list[tuple[int, str]]:
    body = comment.text.removesuffix("*/")
    body = body[len(_block_marker(comment.text)) :]
    pieces: list[tuple[int, str]] = []
    for offset, line in enumerate(body.split("\n")):
        stripped = line.strip()
        if offset and stripped.startswith("*"):
            stripped = stripped[1:]
        pieces.append((comment.row + 1 + offset, stripped))
    while pieces and not pieces[-1][1].strip():
        pieces.pop()
    while pieces and not pieces[0][1].strip():
        pieces.pop(0)
    return pieces


def _unit(rel: str, pieces: Sequence[tuple[int, str]], marker: str, style: Style) -> list[Unit]:
    if not pieces:
        return []
    joined = " ".join(text.strip() for _, text in pieces)
    if style.pragma is not None and style.pragma.match(joined):
        return []
    kept: list[tuple[int, str]] = []
    fenced = False
    for line, text in pieces:
        stripped = text.strip()
        if marker in style.doc_markers and FENCE.match(stripped):
            fenced = not fenced
            continue
        if fenced:
            continue
        kept.append((line, without_code(stripped)))
    if not kept:
        return []
    return [Unit(rel, "comment", "text", tuple(kept))]
