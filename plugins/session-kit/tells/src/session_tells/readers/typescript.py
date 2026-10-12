"""TypeScript and JavaScript: every comment, through tree-sitter. Strings are not read.

A run of ``//`` comments on consecutive lines, each alone on its line, is one
unit. A block comment is one unit, its ``/*``, ``/**``, ``*/`` and each line's
leading ``*`` left out. A comment after code on its line is a unit of its own.
Lint and type pragmas (``eslint-``, ``oxlint-``, ``biome-ignore``, ``@ts-``,
``prettier-``, ``istanbul``, ``#region``, ``#endregion``, a triple-slash
reference) are not prose, and neither is a ``#!`` line. Inline code in
backticks reads as the word ``code``. ``.tsx`` and ``.jsx`` are parsed as TSX.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import tree_sitter_typescript
from tree_sitter import Language, Parser

from session_tells.readers.comments import Style, comment_units

if TYPE_CHECKING:
    from session_tells.units import Unit

SUFFIXES = frozenset({".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"})
_TYPESCRIPT = Language(tree_sitter_typescript.language_typescript())
_TSX = Language(tree_sitter_typescript.language_tsx())
_STYLE = Style(
    node_types=frozenset({"comment"}),
    line_markers=("//",),
    doc_markers=frozenset(),
    pragma=re.compile(
        r"^(?:oxlint-|eslint-|biome-ignore|@ts-|istanbul |prettier-|#region|#endregion"
        r"|/ ?<reference|[#@]__PURE__|[#@]__NO_SIDE_EFFECTS__)"
    ),
)


def typescript(rel: str, source: str) -> list[Unit]:
    """Read the comments in one TypeScript or JavaScript file, as ``comment`` units in file order.

    A file tree-sitter cannot parse whole is still read: the comments it did
    find are returned.
    """
    grammar = _TYPESCRIPT if rel.endswith((".ts", ".mts", ".cts")) else _TSX
    data = source.encode("utf-8")
    tree = Parser(grammar).parse(data)
    return comment_units(rel, data, tree.root_node, _STYLE)
