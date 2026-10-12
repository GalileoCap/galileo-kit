"""Markdown: headings, paragraphs, list items and table cells, with the code left out.

Fences, HTML, link targets and front matter are not prose. Inline code reads as
the word ``code``, so the sentence around it keeps its shape.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from markdown_it import MarkdownIt

from session_tells.readers.common import carries_words
from session_tells.units import Unit

if TYPE_CHECKING:
    from collections.abc import Sequence

    from markdown_it.token import Token

    from session_tells.rules import Role, Text

SUFFIXES = frozenset({".md", ".markdown"})
_MD = MarkdownIt("commonmark").enable("table")


def markdown(rel: str, source: str, *, guide: bool = False) -> list[Unit]:
    """Read the prose in one Markdown file: headings, paragraphs, list items, table cells.

    ``guide`` marks a page a product's users read, which the guide's own rules hold.
    """
    text: Text = "guide" if guide else "doc"
    units: list[Unit] = []
    items = 0
    tokens = _MD.parse(_without_front_matter(source))
    for index, token in enumerate(tokens):
        items += int(token.type == "list_item_open") - int(token.type == "list_item_close")
        if token.type != "inline" or token.map is None:
            continue
        role = _role(tokens[index - 1].type, items)
        units.append(Unit(rel, text, role, _inline(token.map[0] + 1, token.children)))
    return [unit for unit in units if carries_words(unit)]


def quoted_lines(source: str) -> frozenset[int]:
    """Name the lines of a Markdown ``source`` that sit inside a blockquote, counted from 1."""
    found: set[int] = set()
    for token in _MD.parse(_without_front_matter(source)):
        if token.type == "blockquote_open" and token.map is not None:
            found.update(range(token.map[0] + 1, token.map[1] + 1))
    return frozenset(found)


def _role(opened_by: str, items: int) -> Role:
    """Place an inline run by the block that opened it and the list items around it."""
    if opened_by == "heading_open":
        return "heading"
    if items:
        return "item"
    return "text"


def _without_front_matter(source: str) -> str:
    """Blank the front matter out, keeping its lines so the line numbers hold."""
    if not source.startswith("---\n"):
        return source
    end = source.find("\n---\n", 4)
    if end == -1:
        return source
    cut = end + len("\n---\n")
    return "\n" * source[:cut].count("\n") + source[cut:]


def _inline(first: int, children: Sequence[Token] | None) -> tuple[tuple[int, str], ...]:
    if children is None:
        return ()
    pieces: list[tuple[int, str]] = []
    line = first
    current: list[str] = []
    for child in children:
        match child.type:
            case "softbreak" | "hardbreak":
                pieces.append((line, "".join(current)))
                current = []
                line += 1
            case "text":
                current.append(child.content)
            case "code_inline":
                current.append("code")
            case "strong_open" | "strong_close":
                current.append("**")
            case "em_open" | "em_close":
                current.append("*")
            case _:
                pass
    pieces.append((line, "".join(current)))
    return tuple(pieces)
