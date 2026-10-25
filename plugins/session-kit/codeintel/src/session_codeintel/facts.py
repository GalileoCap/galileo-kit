"""What the quality gates know about a module, read once from its syntax tree.

The duplicate gate, the fallback finder and the file-length lint read the
same modules, so they are read in one place: every function with the key
of its body, the method names the module's ``Protocol`` classes declare,
the code lines by the measure's count, and the tree the finder walks.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

from session_codeintel.measure import PYTHON, Area, files_of, py_counts

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

TEST_DIRS = frozenset({"tests", "test"})


@dataclass(frozen=True, slots=True)
class Function:
    """One function or method, reduced to what the duplicate gate compares."""

    qualname: str
    name: str
    line: int
    statements: int
    body: str
    """The body without its docstring, dumped, so two bodies compare as text."""


@dataclass(frozen=True, slots=True)
class Module:
    """One Python file: its functions, its protocols, its code lines and its tree."""

    path: str
    """From the root, POSIX separators."""
    functions: tuple[Function, ...]
    protocol_methods: frozenset[str]
    code_lines: int
    tree: ast.Module

    @property
    def is_test(self) -> bool:
        """Whether the file is a test or a fixture, where a substitution is by design."""
        parts = self.path.split("/")
        name = parts[-1]
        return (
            name.startswith("test_")
            or name == "conftest.py"
            or any(p in TEST_DIRS for p in parts[:-1])
        )


def read_module(root: Path, path: Path) -> Module:
    """Read one module's facts; ``path`` is absolute, under the root."""
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    return Module(
        path=path.relative_to(root).as_posix(),
        functions=_functions(tree),
        protocol_methods=_protocol_methods(tree),
        code_lines=py_counts(text).code,
        tree=tree,
    )


def scan(root: Path, areas: Sequence[Area]) -> list[Module]:
    """Read every Python file under the areas once, in path order."""
    seen: dict[Path, None] = {}
    for area in areas:
        for path in files_of(root, Area(area.name, area.path, area.skip, PYTHON)):
            seen.setdefault(path, None)
    return [read_module(root, path) for path in sorted(seen)]


def protocol_methods_under(root: Path) -> frozenset[str]:
    """Return every method name a ``Protocol`` declares under the root, a directory that exists."""
    if not root.is_dir():
        msg = f"{root}: not a directory, and protocols_from names a tree that is there"
        raise FileNotFoundError(msg)
    names: set[str] = set()
    for path in sorted(root.rglob("*.py")):
        names.update(_protocol_methods(ast.parse(path.read_text(encoding="utf-8"))))
    return frozenset(names)


def _without_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    match body:
        case [ast.Expr(value=ast.Constant(value=str())), *rest]:
            return rest
        case _:
            return body


def _function(node: ast.FunctionDef | ast.AsyncFunctionDef, qualname: str) -> Function:
    body = _without_docstring(node.body)
    key = ast.dump(ast.Module(body=body, type_ignores=[]))
    return Function(qualname, node.name, node.lineno, len(body), key)


def _functions(tree: ast.Module) -> tuple[Function, ...]:
    found: list[Function] = []

    def walk(nodes: Iterable[ast.stmt], prefix: str) -> None:
        for node in nodes:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                qualname = f"{prefix}{node.name}"
                found.append(_function(node, qualname))
                walk(node.body, f"{qualname}.")
            elif isinstance(node, ast.ClassDef):
                walk(node.body, f"{prefix}{node.name}.")

    walk(tree.body, "")
    return tuple(found)


def _is_protocol_base(base: ast.expr) -> bool:
    match base:
        case ast.Name(id="Protocol") | ast.Attribute(attr="Protocol"):
            return True
        case ast.Subscript(value=value):
            return _is_protocol_base(value)
        case _:
            return False


def _protocol_methods(tree: ast.Module) -> frozenset[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and any(_is_protocol_base(b) for b in node.bases):
            names.update(
                member.name
                for member in node.body
                if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef)
            )
    return frozenset(names)
