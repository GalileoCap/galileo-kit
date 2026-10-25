"""The fallback finder: every site where an absence or a failure becomes a value.

Six forms, each a substitution the caller cannot see: ``x or v``,
``.get(k, v)``, ``getattr(o, n, v)``, a broad ``except``, an ``except``
that returns a literal or swallows, and ``if x is None: x = v`` in either
of its spellings, where the test is any presence test, ``isinstance``
included, since over untyped JSON an absence is spelled as the wrong type
as often as ``None``. The finder lists, and the ledger judges.

Two shapes that look like these are not found. A ``.get`` whose second
argument is not a value substitutes nothing: ``session.get(Run, run_id)``
is a lookup by key. And ``None if x is None else f(x)`` carries an absence
through unchanged, which is propagation.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from session_codeintel.facts import Module

EMPTY_CONSTRUCTORS = frozenset({"dict", "list", "set", "tuple", "frozenset", "str", "bytes"})
BROAD = frozenset({"Exception", "BaseException"})
MAX_CODE = 120
MODULE_LEVEL = "<module>"
BARE = "<bare>"
FORMS = ("or", "get", "getattr", "broad-except", "except-returns", "if-none")


class SiteKey(NamedTuple):
    """What identifies one site across edits that move its line.

    The file, the enclosing definition, the form and the code itself. Two
    identical substitutions in one function share a key and are told apart
    by a count.
    """

    site: str
    where: str
    form: str
    code: str


@dataclass(frozen=True, order=True, slots=True)
class Site:
    """One found substitution: its key and the line it was seen on."""

    key: SiteKey
    line: int


def sites(module: Module) -> list[Site]:
    """Return every fallback site in one module, in line order."""
    finder = _Finder(module.path)
    finder.visit(module.tree)
    return sorted(finder.found)


class _Finder(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.found: list[Site] = []
        self._scope: list[str] = []
        self._tests: set[int] = set()

    def visit(self, node: ast.AST) -> None:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            self._scope.append(node.name)
            self.generic_visit(node)
            self._scope.pop()
            return
        self._mark_tests(node)
        self._inspect(node)
        self.generic_visit(node)

    def _mark_tests(self, node: ast.AST) -> None:
        if isinstance(node, ast.If | ast.While | ast.Assert | ast.IfExp):
            self._tests.add(id(node.test))
        elif isinstance(node, ast.comprehension):
            self._tests.update(id(test) for test in node.ifs)

    def _inspect(self, node: ast.AST) -> None:
        match node:
            case ast.BoolOp(op=ast.Or(), values=values):
                if id(node) not in self._tests and _literalish(values[-1]):
                    self._add("or", node, _code(node))
            case ast.Call():
                self._call(node)
            case ast.ExceptHandler():
                self._handler(node)
            case ast.If():
                self._if_none(node)
            case ast.IfExp():
                self._ternary(node)
            case _:
                pass

    def _add(self, form: str, node: ast.expr | ast.stmt | ast.excepthandler, code: str) -> None:
        where = ".".join(self._scope) or MODULE_LEVEL
        self.found.append(Site(SiteKey(self.path, where, form, code), node.lineno))

    def _call(self, node: ast.Call) -> None:
        match node:
            case ast.Call(func=ast.Attribute(attr="get"), args=[_, default], keywords=[]):
                if _literalish(default) and not _is_none(default):
                    self._add("get", node, _code(node))
            case ast.Call(func=ast.Name(id="getattr"), args=[_, _, _]):
                self._add("getattr", node, _code(node))
            case _:
                pass

    def _handler(self, node: ast.ExceptHandler) -> None:
        kind = ast.unparse(node.type) if node.type is not None else BARE
        if _is_broad(node.type):
            self._add("broad-except", node, f"except {kind}")
            return
        last = node.body[-1]
        swallows = isinstance(last, ast.Pass | ast.Continue)
        returns = (
            isinstance(last, ast.Return) and last.value is not None and _literalish(last.value)
        )
        if swallows or returns:
            self._add("except-returns", node, f"except {kind}: {_code(last)}")

    def _if_none(self, node: ast.If) -> None:
        match node:
            case ast.If(
                test=ast.Compare(
                    left=ast.Name(id=name), ops=[ast.Is()], comparators=[ast.Constant(value=None)]
                ),
                body=[ast.Assign(targets=[ast.Name(id=target)], value=value)],
                orelse=[],
            ) if name == target and _literalish(value) and not _is_none(value):
                self._add("if-none", node, f"if {name} is None: {name} = {_code(value)}")
            case _:
                pass

    def _ternary(self, node: ast.IfExp) -> None:
        literal = [branch for branch in (node.body, node.orelse) if _literalish(branch)]
        if len(literal) == 1 and not _is_none(literal[0]) and _is_presence_test(node.test):
            self._add("if-none", node, _code(node))


def _is_presence_test(test: ast.expr) -> bool:
    """Whether a condition asks *is there something here*, with ``isinstance`` as one such ask."""
    match test:
        case ast.Compare(ops=[ast.Is() | ast.IsNot()], comparators=[ast.Constant(value=None)]):
            return True
        case ast.Name() | ast.Attribute():
            return True
        case ast.Call(func=ast.Name(id="isinstance"), args=[_, _], keywords=[]):
            return True
        case ast.UnaryOp(op=ast.Not(), operand=operand):
            return _is_presence_test(operand)
        case ast.BoolOp(op=ast.And(), values=values):
            return all(_is_presence_test(value) for value in values)
        case _:
            return False


def _is_broad(node: ast.expr | None) -> bool:
    match node:
        case None:
            return True
        case ast.Name(id=name):
            return name in BROAD
        case ast.Tuple(elts=elts):
            return any(_is_broad(element) for element in elts)
        case _:
            return False


def _literalish(node: ast.expr) -> bool:
    """Whether an expression is a value and no computation: a substitute."""
    match node:
        case ast.Constant() | ast.JoinedStr():
            return True
        case ast.Name(id=name) | ast.Attribute(attr=name):
            return name.isupper()
        case ast.UnaryOp(operand=operand):
            return _literalish(operand)
        case ast.List() | ast.Tuple() | ast.Set() | ast.Dict() | ast.Call():
            return _display(node)
        case _:
            return False


def _display(node: ast.expr) -> bool:
    match node:
        case ast.List(elts=elts) | ast.Tuple(elts=elts) | ast.Set(elts=elts):
            return all(_literalish(element) for element in elts)
        case ast.Dict(keys=keys, values=values):
            keys_ok = all(key is None or _literalish(key) for key in keys)
            return keys_ok and all(_literalish(value) for value in values)
        case ast.Call(func=ast.Name(id=name), args=[], keywords=[]):
            return name in EMPTY_CONSTRUCTORS
        case _:
            return False


def _is_none(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _code(node: ast.AST) -> str:
    text = " ".join(ast.unparse(node).split())
    return text if len(text) <= MAX_CODE else text[: MAX_CODE - 1] + "…"
