"""Python: comment blocks and every bare string statement (docstrings), pragmas left out."""

from __future__ import annotations

import ast
import io
import re
import tokenize

from session_tells.readers.common import carries_words, without_code
from session_tells.units import Unit

SUFFIXES = frozenset({".py", ".pyi"})
PRAGMA = re.compile(r"^(?:noqa|type:|pyright:|fmt:|ruff:|pragma|isort:|-\*-)")


def python(rel: str, source: str) -> list[Unit]:
    """Read the prose in one Python file: comment blocks, then every bare string statement."""
    units: list[Unit] = []
    block: list[tuple[int, str]] = []
    last = 0
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        line = token.start[0]
        body = token.string.lstrip("#").strip()
        if PRAGMA.match(body) or token.string.startswith("#!"):
            continue
        if block and line != last + 1:
            units.append(Unit(rel, "comment", "text", tuple(block)))
            block = []
        block.append((line, without_code(body)))
        last = line
    if block:
        units.append(Unit(rel, "comment", "text", tuple(block)))
    units.extend(
        Unit(rel, "comment", "text", _docstring(node.lineno, node.value.value))
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )
    return [unit for unit in units if carries_words(unit)]


def _docstring(first: int, value: str) -> tuple[tuple[int, str], ...]:
    return tuple(
        (first + offset, without_code(line.strip()))
        for offset, line in enumerate(value.splitlines())
        if not line.strip().startswith((">>>", "..."))
    )
