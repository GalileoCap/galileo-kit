"""Split two versions of a Markdown document into sections, pair them, and judge each pair.

A section is a heading and its own body, the lines up to the next heading at any depth. A parent's
verdict is about its own text, and each subsection gets its own. The text before the first heading
is a section with no heading, and a YAML front matter block is one too. Bodies are compared word by
word, so a paragraph wrapped again counts as unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import StrEnum
from typing import TYPE_CHECKING

from markdown_it import MarkdownIt

if TYPE_CHECKING:
    from collections.abc import Callable

# A section paired by its body alone must share this much of its words with its old self.
PAIRED_BY_BODY = 0.5
FRONT_MATTER = "(front matter)"


class Verdict(StrEnum):
    """What happened to a section between the two versions."""

    UNCHANGED = "unchanged"
    MOVED = "moved"
    RENAMED = "renamed"
    EDITED = "edited"
    REWRITTEN = "rewritten"
    NEW = "new"
    REMOVED = "removed"


# The verdicts whose new text the owner reads whole.
READ_WHOLE = frozenset({Verdict.REWRITTEN, Verdict.NEW})


@dataclass(frozen=True)
class Section:
    """A heading, the headings above it, and its own body."""

    path: tuple[str, ...]
    level: int
    heading: str
    body: str
    line: int

    @property
    def title(self) -> str:
        """Return the heading, or a name for the text before the first heading."""
        return self.heading or "(before the first heading)"

    @property
    def words(self) -> list[str]:
        """Return the body's words, so wrapping a line again changes nothing."""
        return self.body.split()


@dataclass
class Change:
    """A section's verdict, with its old side, its new side or both."""

    verdict: Verdict
    old: Section | None
    new: Section | None
    changed: float = 0.0
    notes: list[str] = field(default_factory=list[str])

    @property
    def section(self) -> Section:
        """Return the new side, or the old one for a removed section."""
        if self.new is not None:
            return self.new
        if self.old is not None:
            return self.old
        msg = "a change has an old side, a new side or both"
        raise ValueError(msg)


def front_matter(lines: list[str]) -> int:
    """Return how many lines a YAML front matter block takes at the top, its fences included."""
    if not lines or lines[0].strip() != "---":
        return 0
    for i in range(1, len(lines)):
        if lines[i].strip() in {"---", "..."}:
            return i + 1
    return 0


def split(text: str) -> list[Section]:
    """Return the document's sections in order."""
    lines = text.splitlines()
    sections: list[Section] = []
    skip = front_matter(lines)
    if skip:
        body = "\n".join(lines[1 : skip - 1])
        sections.append(Section((FRONT_MATTER,), 0, FRONT_MATTER, body, 1))
    blanked = "\n" * skip + "\n".join(lines[skip:])
    starts: list[tuple[int, int, int, str]] = []
    tokens = MarkdownIt("commonmark").enable("table").parse(blanked)
    for i, token in enumerate(tokens):
        if token.type == "heading_open" and token.map is not None:
            heading = tokens[i + 1].content.strip()
            starts.append((token.map[0], token.map[1], int(token.tag[1:]), heading))
    first = starts[0][0] if starts else len(lines)
    preamble = "\n".join(lines[skip:first])
    if preamble.strip():
        sections.append(Section((), 0, "", preamble, skip + 1))
    stack: list[tuple[int, str]] = []
    for n, (start, after, level, heading) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, heading))
        path = tuple(h for _, h in stack)
        sections.append(Section(path, level, heading, "\n".join(lines[after:end]), start + 1))
    return sections


def likeness(a: list[str], b: list[str]) -> float:
    """Return the share of words two bodies have in common, in order."""
    if not a and not b:
        return 1.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


@dataclass
class Pairing:
    """The old and new sections paired, and those of each side left without a pair."""

    pairs: list[tuple[Section, Section]]
    removed: list[Section]
    added: list[Section]


def pair(old: list[Section], new: list[Section]) -> Pairing:
    """Pair sections by heading path, then by heading alone, then by the likeness of their bodies.

    A key pairs two sections only when each side has one section with it.
    """
    pairs: list[tuple[Section, Section]] = []
    old_left = list(old)
    new_left = list(new)
    keys: list[Callable[[Section], object]] = [lambda s: s.path, lambda s: s.heading]
    for key in keys:
        for n in list(new_left):
            wanted = [o for o in old_left if key(o) == key(n)]
            if len(wanted) == 1 and sum(key(m) == key(n) for m in new_left) == 1:
                pairs.append((wanted[0], n))
                old_left.remove(wanted[0])
                new_left.remove(n)
    scored = sorted(
        (
            (likeness(o.words, n.words), i, j)
            for i, o in enumerate(old_left)
            for j, n in enumerate(new_left)
            if o.words and n.words
        ),
        reverse=True,
    )
    used_old: set[int] = set()
    used_new: set[int] = set()
    for score, i, j in scored:
        if score >= PAIRED_BY_BODY and i not in used_old and j not in used_new:
            used_old.add(i)
            used_new.add(j)
            pairs.append((old_left[i], new_left[j]))
    return Pairing(
        pairs,
        [o for i, o in enumerate(old_left) if i not in used_old],
        [n for j, n in enumerate(new_left) if j not in used_new],
    )


def parent(sections: list[Section], section: Section) -> Section | None:
    """Return the nearest section before this one at a shallower level."""
    found: Section | None = None
    for s in sections:
        if s is section:
            return found
        if s.level < section.level:
            found = s
    return None


def judge(old: Section, new: Section, moved_from: str | None, threshold: float) -> Change:
    """Judge a pair. `moved_from` names the old parent when the section now sits under another."""
    changed = 1.0 - likeness(old.words, new.words)
    notes: list[str] = []
    if old.heading != new.heading:
        notes.append(f"renamed from “{old.title}”")
    if moved_from is not None:
        notes.append(f"moved from {moved_from}")
    if changed > threshold:
        verdict = Verdict.REWRITTEN
    elif changed > 0:
        verdict = Verdict.EDITED
    elif old.heading != new.heading:
        verdict = Verdict.RENAMED
    elif moved_from is not None:
        verdict = Verdict.MOVED
    else:
        verdict = Verdict.UNCHANGED
    return Change(verdict, old, new, changed, notes)


def compare(old_text: str, new_text: str, threshold: float) -> list[Change]:
    """Return every section of either version with its verdict.

    The new document's sections come in its order, and each removed one follows the section that
    preceded it in the old document.
    """
    old = split(old_text)
    new = split(new_text)
    pairing = pair(old, new)
    new_of = {id(o): n for o, n in pairing.pairs}
    judged: dict[int, Change] = {}
    for o, n in pairing.pairs:
        was = parent(old, o)
        now = parent(new, n)
        moved = (was is None) != (now is None) or (
            was is not None and new_of.get(id(was)) is not now
        )
        moved_from = (f"under “{was.title}”" if was else "the top level") if moved else None
        judged[id(n)] = judge(o, n, moved_from, threshold)
    changes = [judged.get(id(n)) or Change(Verdict.NEW, None, n, 1.0) for n in new]
    for gone in pairing.removed:
        before = [o for o in old if o.line < gone.line]
        at = 0 if not before else len(changes)
        for i, change in enumerate(changes):
            if before and change.old is before[-1]:
                at = i + 1
                break
        changes.insert(at, Change(Verdict.REMOVED, gone, None, 1.0))
    return changes
