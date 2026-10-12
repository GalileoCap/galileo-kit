"""Rust: every comment, through tree-sitter. Strings are not read.

A run of line comments of one kind (``//``, ``///`` or ``//!``) on consecutive
lines, each alone on its line, is one unit, its markers left out. A block
comment (``/* */``, ``/** */``, ``/*! */``) is one unit, its markers and each
line's leading ``*`` left out. A comment after code on its line is a unit of
its own. Doc comments are Markdown, so the lines inside a fenced code block in
one are not prose. Inline code in backticks reads as the word ``code``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tree_sitter_rust
from tree_sitter import Language, Parser

from session_tells.readers.comments import Style, comment_units

if TYPE_CHECKING:
    from session_tells.units import Unit

SUFFIXES = frozenset({".rs"})
_RUST = Language(tree_sitter_rust.language())
_STYLE = Style(
    node_types=frozenset({"line_comment", "block_comment"}),
    line_markers=("///", "//!", "//"),
    doc_markers=frozenset({"///", "//!", "/**", "/*!"}),
)


def rust(rel: str, source: str) -> list[Unit]:
    """Read the comments in one Rust file, as ``comment`` units in file order.

    A file tree-sitter cannot parse whole is still read: the comments it did
    find are returned.
    """
    data = source.encode("utf-8")
    tree = Parser(_RUST).parse(data)
    return comment_units(rel, data, tree.root_node, _STYLE)
