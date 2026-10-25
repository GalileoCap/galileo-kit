"""The code measure: size, complexity and repetition per area, per snapshot.

Size is files, lines, code, comment and docstring lines: Python through the
tokenizer and ``ast``, TypeScript and the rest by a line scan. Complexity is
McCabe per function: Python from the pinned ruff's ``C901`` with the cap at
zero, TypeScript from the pinned ast-grep counting ``if``, ``?:``, loops,
``case``, ``catch``, ``&&``, ``||`` and ``??`` inside the innermost function,
with the JSX elements beside. Repetition is the looks check's count, when the
project has a ``looks`` block. The areas come from ``measure.areas`` in
``.claude/claude-kit.json`` (``name``, ``path``, ``skip`` and ``extensions``, by
default the code's: Python, TypeScript, JavaScript and YAML), or the root alone.
A snapshot is the working tree, or a ``git archive`` of each ref asked for,
and the same tool measures every snapshot, so two rows can be read against
each other.
"""

from __future__ import annotations

import ast
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import tokenize
from dataclasses import dataclass
from pathlib import Path

from session_codeintel import looks
from session_codeintel.settings import block as read_block
from session_codeintel.settings import is_list, is_record, strings

AST_GREP = Path(sys.executable).parent / "ast-grep"
RUFF = Path(sys.executable).parent / "ruff"
SKIP_DIRS = frozenset(
    {"node_modules", ".venv", "venv", "dist", "build", ".git", "__pycache__", "site-packages"}
)
PYTHON = (".py",)
TYPESCRIPT = (".ts", ".tsx")
SCRIPT = (".js", ".jsx", ".mjs", ".cjs")
RULES = (".yml", ".yaml")
EXTENSIONS = PYTHON + TYPESCRIPT + SCRIPT + RULES
"""What an area counts unless its settings name the extensions."""
HIGH = 6
"""A function at this complexity or more is counted apart, as generic-app's report did."""
TS_RULE = """\
id: fn-{language}
language: {language}
rule:
  any:
    - kind: function_declaration
    - kind: function_expression
    - kind: arrow_function
    - kind: method_definition
    - kind: generator_function_declaration
---
id: branch-{language}
language: {language}
rule:
  any:
    - kind: if_statement
    - kind: ternary_expression
    - kind: for_statement
    - kind: for_in_statement
    - kind: while_statement
    - kind: do_statement
    - kind: catch_clause
    - kind: switch_case
    - all:
        - kind: binary_expression
        - has: {{field: operator, regex: '^(&&|\\|\\||\\?\\?)$'}}
"""
JSX_RULE = """\
id: jsx-tsx
language: tsx
rule:
  any:
    - kind: jsx_element
    - kind: jsx_self_closing_element
"""
LANGUAGES = ("typescript", "tsx")
TS_RULES = "---\n".join([*(TS_RULE.format(language=lang) for lang in LANGUAGES), JSX_RULE])
"""The functions and the branches once per language the two extensions parse as, tsx's elements."""


@dataclass(frozen=True, slots=True)
class Area:
    """A directory measured as one row."""

    name: str
    path: str
    skip: tuple[str, ...] = ()
    extensions: tuple[str, ...] = EXTENSIONS


@dataclass(frozen=True, slots=True)
class Size:
    """Line counts over an area's files."""

    files: int = 0
    lines: int = 0
    code: int = 0
    comment: int = 0
    docstring: int = 0

    def plus(self, other: Size) -> Size:
        """Add two counts."""
        return Size(
            self.files + other.files,
            self.lines + other.lines,
            self.code + other.code,
            self.comment + other.comment,
            self.docstring + other.docstring,
        )


@dataclass(frozen=True, slots=True)
class Complexity:
    """McCabe over an area's functions of one language."""

    functions: int
    total: int
    high: int
    maximum: int
    jsx: int = 0

    @classmethod
    def of(cls, values: list[int], jsx: int = 0) -> Complexity:
        """Summarise one figure per function."""
        high = sum(1 for v in values if v >= HIGH)
        return cls(len(values), sum(values), high, max(values, default=0), jsx)


@dataclass(frozen=True, slots=True)
class Row:
    """One area at one snapshot."""

    snapshot: str
    area: str
    size: Size
    python: Complexity | None
    typescript: Complexity | None
    repeats: tuple[int, int] | None


def read_areas(root: Path) -> tuple[Area, ...]:
    """Read ``measure.areas``, or the root as the one area."""
    block = read_block(root, "measure")
    entries = block.get("areas") if block is not None else None
    areas = [a for a in (_area(e) for e in entries) if a] if is_list(entries) else []
    return tuple(areas) or (Area(".", "."),)


def _area(entry: object) -> Area | None:
    if not is_record(entry):
        return None
    path = entry.get("path")
    if not isinstance(path, str) or not path:
        return None
    name = entry.get("name")
    label = name if isinstance(name, str) and name else path
    named = strings(entry.get("extensions"))
    skips = strings(entry.get("skip"))
    return Area(name=label, path=path.strip("/"), skip=skips, extensions=named or EXTENSIONS)


def files_of(root: Path, area: Area) -> list[Path]:
    """List the area's files by extension, skipping its skip, dependency directories and venvs."""
    base = root / area.path
    if not base.is_dir():
        return []
    skipped = tuple((root / s).resolve() for s in area.skip)
    venvs = tuple(p.parent.resolve() for p in base.rglob("pyvenv.cfg"))
    found: list[Path] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix not in area.extensions:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if any(path.resolve().is_relative_to(s) for s in skipped + venvs):
            continue
        found.append(path)
    return found


def py_counts(text: str) -> Size:
    """Count a Python file: a docstring line is neither code nor comment."""
    doc: set[int] = set()
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        tree = None
    if tree is not None:
        for node in ast.walk(tree):
            doc.update(_docstring_lines(node))
    comment: set[int] = set()
    code: set[int] = set()
    silent = {tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                comment.add(tok.start[0])
            elif tok.type not in silent:
                code.update(n for n in range(tok.start[0], tok.end[0] + 1) if n not in doc)
    except (tokenize.TokenError, SyntaxError):
        pass
    return Size(1, len(text.splitlines()), len(code), len(comment - code), len(doc))


def _docstring_lines(node: ast.AST) -> range:
    scopes = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    if not isinstance(node, scopes) or not node.body:
        return range(0)
    first = node.body[0]
    if not isinstance(first, ast.Expr) or not isinstance(first.value, ast.Constant):
        return range(0)
    if not isinstance(first.value.value, str):
        return range(0)
    return range(first.lineno, (first.end_lineno or first.lineno) + 1)


def line_counts(text: str, marks: tuple[str, str, str]) -> Size:
    """Count a file by its lines: blank, comment (line or block) or code."""
    line_mark, block_open, block_close = marks
    code = comment = 0
    inside = False
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        opens = bool(block_open) and stripped.startswith(block_open)
        if inside:
            comment += 1
            inside = block_close not in stripped
        elif stripped.startswith(line_mark) or opens:
            comment += 1
            inside = opens and block_close not in stripped
        else:
            code += 1
    return Size(1, len(text.splitlines()), code, comment, 0)


def size_of(path: Path) -> Size:
    """Count one file by its language."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix in PYTHON:
        return py_counts(text)
    if path.suffix in TYPESCRIPT or path.suffix in SCRIPT:
        return line_counts(text, ("//", "/*", "*/"))
    return line_counts(text, ("#", "", ""))


def _run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(  # noqa: S603  the pinned ruff and ast-grep and git archive, fixed argument lists, no shell
        argv, capture_output=True, check=False, cwd=cwd
    )


def py_complexity(root: Path, files: list[Path], ruff: Path = RUFF) -> Complexity | None:
    """Run ruff's C901 at cap zero over the Python files; None when there are none."""
    wanted = sorted({str(f.resolve()) for f in files if f.suffix in PYTHON})
    if not wanted:
        return None
    options = ["--isolated", "--select", "C901", "--config", "lint.mccabe.max-complexity = 0"]
    done = _run(
        [str(ruff), "check", *options, "--output-format", "json", "--exit-zero", *wanted], root
    )
    values: list[int] = []
    parsed: object = json.loads(done.stdout or b"[]")
    for item in parsed if is_list(parsed) else []:
        message = item.get("message") if is_record(item) else None
        if isinstance(message, str) and "(" in message:
            values.append(int(message.rsplit("(", 1)[1].split(" ")[0]))
    return Complexity.of(values)


def ts_complexity(root: Path, files: list[Path], ast_grep: Path = AST_GREP) -> Complexity | None:
    """Count branches inside the innermost function with ast-grep; None when no TypeScript."""
    wanted = sorted(str(f.resolve()) for f in files if f.suffix in TYPESCRIPT)
    if not wanted:
        return None
    done = _run(
        [str(ast_grep), "scan", "--inline-rules", TS_RULES, "--json=compact", *wanted], root
    )
    spans: dict[str, list[tuple[int, int]]] = {}
    marks: dict[str, list[tuple[str, int]]] = {}
    parsed: object = json.loads(done.stdout or b"[]")
    for item in parsed if is_list(parsed) else []:
        match = _match(item)
        if match is None:
            continue
        rule, file, start, end = match
        if rule == "fn":
            spans.setdefault(file, []).append((start, end))
        else:
            marks.setdefault(file, []).append((rule, start))
    values: list[int] = []
    jsx = 0
    for file, functions in spans.items():
        counted, elements = _attribute(functions, marks.get(file, []))
        values += counted
        jsx += elements
    return Complexity.of(values, jsx)


def _attribute(
    functions: list[tuple[int, int]], marks: list[tuple[str, int]]
) -> tuple[list[int], int]:
    """Give each branch to the innermost function around it; the counts, and the elements."""
    counts = [1] * len(functions)
    ordered = sorted(range(len(functions)), key=lambda i: functions[i][0])
    jsx = 0
    for rule, at in marks:
        if rule == "jsx":
            jsx += 1
            continue
        owner = next(
            (i for i in reversed(ordered) if functions[i][0] <= at < functions[i][1]), None
        )
        if owner is not None:
            counts[owner] += 1
    return counts, jsx


def _match(item: object) -> tuple[str, str, int, int] | None:
    if not is_record(item):
        return None
    rule, file, range_ = item.get("ruleId"), item.get("file"), item.get("range")
    offsets = range_.get("byteOffset") if is_record(range_) else None
    if not isinstance(rule, str) or not isinstance(file, str) or not is_record(offsets):
        return None
    start, end = offsets.get("start"), offsets.get("end")
    if not isinstance(start, int) or not isinstance(end, int):
        return None
    return rule.split("-", 1)[0], file, start, end


def repeats_of(root: Path, settings: looks.Settings | None) -> tuple[int, int] | None:
    """Count the repeated looks and their places, when the project has a looks block."""
    if settings is None:
        return None
    bare = looks.Settings(src=settings.src, skip=settings.skip)
    report = looks.check(looks.scan(root, bare), bare)
    return len(report.repeats), sum(len(r.places) for r in report.repeats)


def measure(
    root: Path, areas: tuple[Area, ...], snapshot: str, looks_settings: looks.Settings | None
) -> list[Row]:
    """Measure every area of one snapshot."""
    rows: list[Row] = []
    for area in areas:
        files = files_of(root, area)
        size = Size()
        for path in files:
            size = size.plus(size_of(path))
        scripted = any(f.suffix in TYPESCRIPT for f in files)
        rows.append(
            Row(
                snapshot=snapshot,
                area=area.name,
                size=size,
                python=py_complexity(root, files),
                typescript=ts_complexity(root, files),
                repeats=repeats_of(root, looks_settings) if scripted else None,
            )
        )
    return rows


def snapshot_of(repo: Path, ref: str, into: Path) -> Path:
    """Extract ``git archive <ref>`` into a directory; the directory.

    Raises:
        RuntimeError: git refused the ref.

    """
    done = _run(["git", "archive", "--format=tar", ref], repo)
    if done.returncode != 0:
        msg = f"git archive {ref}: {done.stderr.decode(errors='replace').strip()}"
        raise RuntimeError(msg)
    target = into / ref.replace("/", "-")
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(done.stdout), mode="r:") as tar:
        tar.extractall(target, filter="data")
    return target


def scratch() -> Path:
    """Make a directory of this run's own for the snapshots."""
    return Path(tempfile.mkdtemp(prefix="session-codeintel-measure-"))


def render(rows: list[Row], root: Path, title: str) -> str:
    """Render the rows as markdown, one size table and one complexity table per area."""
    out = [
        f"# {title}",
        "",
        f"Written by `session-codeintel measure` over `{root}`. Code lines leave out blank lines,"
        " comments and docstrings. Complexity is McCabe per function: Python from ruff's C901,"
        " TypeScript counted on the syntax tree, both at the same version for every row.",
        "",
    ]
    for area in dict.fromkeys(r.area for r in rows):
        out += [f"## {area}", ""]
        out += [
            "| Snapshot | Files | Lines | Code | Comment | Docstring |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        out += [_size_line(r) for r in rows if r.area == area]
        out += [
            "",
            "| Snapshot | Language | Functions | Complexity | Mean | At 6 or more | Max"
            " | JSX elements | Repeated looks | Places |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for r in (r for r in rows if r.area == area):
            out += _complexity_lines(r)
        out.append("")
    return "\n".join(out)


def _size_line(r: Row) -> str:
    s = r.size
    counts = f"{s.files:,} | {s.lines:,} | {s.code:,} | {s.comment:,} | {s.docstring:,}"
    return f"| {r.snapshot} | {counts} |"


def _complexity_lines(r: Row) -> list[str]:
    lines: list[str] = []
    for language, c in (("Python", r.python), ("TypeScript", r.typescript)):
        if c is None:
            continue
        mean = f"{c.total / c.functions:.2f}" if c.functions else "0"
        jsx = f"{c.jsx:,}" if language == "TypeScript" else ""
        looked = language == "TypeScript" and r.repeats is not None
        repeats = f"{r.repeats[0]:,} | {r.repeats[1]:,}" if looked and r.repeats else " | "
        head = f"| {r.snapshot} | {language} | {c.functions:,} | {c.total:,} | {mean}"
        lines.append(f"{head} | {c.high:,} | {c.maximum:,} | {jsx} | {repeats} |")
    return lines
