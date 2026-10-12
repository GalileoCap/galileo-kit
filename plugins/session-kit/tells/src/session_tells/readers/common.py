"""What every reader shares: inline code read as a word, and the test for prose."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from session_tells.units import Unit

CODE_SPAN = re.compile(r"``[^`]*``|`[^`]*`")
LETTER = re.compile(r"[^\W\d_]")


def without_code(text: str) -> str:
    """Read inline code as the word ``code``, so the sentence around it keeps its shape."""
    return CODE_SPAN.sub("code", text)


def carries_words(unit: Unit) -> bool:
    """Whether a unit carries words: a cell holding a dash or a number is not prose."""
    return any(LETTER.search(text) for _, text in unit.pieces)
