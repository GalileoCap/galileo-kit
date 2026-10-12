"""Find the tells in units of prose, less what a marker allows or a document quotes.

A line may carry ``tells: allow <rule>`` (several, comma-separated) for a hit
the rule cannot tell from plain prose; the hit on that line is not reported.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from session_tells.readers import markdown as markdown_reader

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from session_tells.rules import Language, Rule, Text
    from session_tells.units import Unit

ALLOW = re.compile(r"tells: allow ([\w-]+(?:\s*,\s*[\w-]+)*)")

type Allowed = Mapping[str, frozenset[tuple[int, str]]]
"""For each file, the ``(line, rule)`` pairs a ``tells: allow`` marker allows."""


@dataclass(frozen=True, order=True)
class Hit:
    """One tell found: where, which rule, and the words it matched."""

    path: str
    line: int
    rule: str
    found: str
    text: Text


def language_of(path: str, languages: Mapping[str, Language]) -> Language:
    """Return the language of a file: its tree's, and English outside a translated tree."""
    for part in path.split("/"):
        if part in languages:
            return languages[part]
    return "en"


def hits(
    units: Iterable[Unit],
    rules: Sequence[Rule],
    *,
    languages: Mapping[str, Language] | None = None,
    allowed: Allowed | None = None,
) -> list[Hit]:
    """Every tell the rules find in the units, less the ones a marker on their line allows."""
    found: list[Hit] = []
    for unit in units:
        joined, starts = _join(unit)
        marked = (allowed or {}).get(unit.path)
        language = language_of(unit.path, languages or {})
        for rule in rules:
            if (
                unit.text not in rule.texts
                or unit.role not in rule.roles
                or language not in rule.languages
            ):
                continue
            for match in rule.pattern.finditer(joined):
                line = _line(starts, match.start())
                if marked is not None and (line, rule.name) in marked:
                    continue
                found.append(Hit(unit.path, line, rule.name, match.group(0).strip(), unit.text))
    return sorted(found)


def _join(unit: Unit) -> tuple[str, list[tuple[int, int]]]:
    """Join the unit into one string, with ``(offset, line)`` where each piece starts."""
    starts: list[tuple[int, int]] = []
    parts: list[str] = []
    offset = 0
    for line, text in unit.pieces:
        starts.append((offset, line))
        parts.append(text)
        offset += len(text) + 1
    return " ".join(parts), starts


def _line(starts: Sequence[tuple[int, int]], offset: int) -> int:
    line = starts[0][1]
    for start, at in starts:
        if start > offset:
            break
        line = at
    return line


def markers(text: str) -> frozenset[tuple[int, str]]:
    """Return the ``(line, rule)`` pairs the ``tells: allow`` markers in one file's text allow."""
    return frozenset(
        (number, name.strip())
        for number, line in enumerate(text.splitlines(), 1)
        if (match := ALLOW.search(line)) is not None
        for name in match.group(1).split(",")
    )


def in_document(path: str, source: str, rules: Sequence[Rule]) -> list[Hit]:
    """Find the banned tells in one Markdown document, its quoted words left out.

    A blockquote holds somebody else's words, so it is not the document's own
    prose, and neither are words in quotation marks or single-star emphasis,
    which a record uses to cite. A marker on a line allows its rule there.
    """
    quoted = markdown_reader.quoted_lines(source)
    banned = [rule for rule in rules if rule.kind == "banned"]
    units = [_unquoted(unit) for unit in markdown_reader.markdown(path, source)]
    found = hits(units, banned, allowed={path: markers(source)})
    return [hit for hit in found if hit.line not in quoted]


_QUOTED = re.compile(r'"[^"]*"|“[^”]*”|(?<!\*)\*(?!\*)[^*]+(?<!\*)\*(?!\*)')
"""Words in quotation marks, or in single-star emphasis, which a record uses to cite."""


def _unquoted(unit: Unit) -> Unit:
    """Blank out the quoted words of a unit, keeping every piece's length and line."""
    joined = " ".join(text for _, text in unit.pieces)
    blank = _QUOTED.sub(lambda match: " " * len(match.group(0)), joined)
    pieces: list[tuple[int, str]] = []
    offset = 0
    for line, text in unit.pieces:
        pieces.append((line, blank[offset : offset + len(text)]))
        offset += len(text) + 1
    return replace(unit, pieces=tuple(pieces))
