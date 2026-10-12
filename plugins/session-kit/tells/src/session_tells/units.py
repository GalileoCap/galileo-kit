"""What a reader hands the rules: one stretch of prose, kept as the lines it came from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from session_tells.rules import Role, Text


@dataclass(frozen=True)
class Unit:
    """One stretch of prose (a paragraph, a heading, a comment block, a docstring, one string).

    Kept as the source lines it spans, so a rule can match across a wrapped
    line and still name the line it hit.
    """

    path: str
    """Relative to the project root, posix."""
    text: Text
    role: Role
    pieces: tuple[tuple[int, str], ...]
    """``(line, text)`` for each source line, in order, counted from 1."""
