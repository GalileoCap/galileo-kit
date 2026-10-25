"""The code measure: each count proven on a planted file, two snapshots read against each other."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from session_codeintel.cli import main
from session_codeintel.measure import (
    Area,
    files_of,
    py_complexity,
    py_counts,
    size_of,
    ts_complexity,
)
from tests.tools import run

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

PY = '''"""A module docstring
over two lines."""

import os  # a trailing comment


def f(x: int) -> int:
    """One line."""
    # a comment
    if x and os.sep:
        return 1
    for _ in range(2):
        pass
    return 2


class C:
    def g(self) -> None:
        pass
'''
TS = """// a comment
/* a block
   comment */
export function f(a: number): number {
  if (a) { return a && 1 }
  const g = () => (a ? 1 : 2)
  for (const x of []) { }
  switch (a) { case 1: break }
  try { } catch (e) { }
  return a ?? 0
}
export const h = (): number => 1
"""
SETTINGS = {"measure": {"areas": [{"name": "app", "path": "src"}]}, "looks": {"src": "src"}}
COMMIT = [
    "git",
    "-c",
    "user.name=t",
    "-c",
    "user.email=t@t",
    "-c",
    "commit.gpgsign=false",
    "commit",
]
TSX = 'export const P = () => <div className="a b"><span className="a b" /></div>\n'


def tree(root: Path, files: dict[str, str]) -> None:
    """Write each file under the root."""
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test_a_python_file_is_counted_by_its_tokens_and_its_functions_by_ruff(tmp_path: Path) -> None:
    """Docstrings are their own count, a trailing comment is code, and C901 gives each function."""
    size = py_counts(PY)
    assert (size.lines, size.code, size.comment, size.docstring) == (19, 10, 1, 3)
    tree(tmp_path, {"src/a.py": PY})
    complexity = py_complexity(tmp_path, files_of(tmp_path, Area("src", "src")))
    assert complexity is not None
    assert (complexity.functions, complexity.total, complexity.maximum) == (2, 4, 3)


def test_a_typescript_file_is_counted_by_lines_and_its_branches_by_the_innermost_function(
    tmp_path: Path,
) -> None:
    """A block comment counts as comment, and a branch in a nested arrow is the arrow's."""
    tree(tmp_path, {"src/a.ts": TS, "src/p.tsx": TSX, "src/components/ui/x.ts": TS, "src/n.md": TS})
    size = size_of(tmp_path / "src/a.ts")
    assert (size.lines, size.code, size.comment) == (12, 9, 3)
    files = files_of(tmp_path, Area("src", "src", ("src/components/ui",)))
    assert [f.name for f in files] == ["a.ts", "p.tsx"]
    assert [f.name for f in files_of(tmp_path, Area("src", "src", (), (".md",)))] == ["n.md"]
    complexity = ts_complexity(tmp_path, files)
    assert complexity is not None
    assert (complexity.functions, complexity.total, complexity.high) == (4, 11, 1)
    assert complexity.maximum == 7
    assert complexity.jsx == 2


def test_the_command_measures_each_ref_and_the_looks_when_the_project_has_them(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``measure --at`` archives each ref, the rows read against each other, the looks counted."""
    tree(
        tmp_path,
        {
            ".claude/claude-kit.json": json.dumps(SETTINGS),
            "src/a.py": PY,
            "src/p.tsx": TSX,
        },
    )
    for argv in (
        ["git", "init", "-q"],
        ["git", "add", "."],
        [*COMMIT, "-q", "-m", "one"],
    ):
        assert run(argv, tmp_path).returncode == 0
    (tmp_path / "src/a.py").write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
    for argv in (
        ["git", "add", "."],
        [*COMMIT, "-q", "-m", "two"],
    ):
        assert run(argv, tmp_path).returncode == 0
    out = tmp_path / "report.md"
    assert (
        main(["measure", str(tmp_path), "--at", "HEAD~1", "--at", "HEAD", "--out", str(out)]) == 0
    )
    assert capsys.readouterr().out.strip() == f"{out}: 2 row(s)"
    report = out.read_text(encoding="utf-8")
    assert "## app" in report
    assert "| HEAD~1 | 2 | 20 | 11 | 1 | 3 |" in report
    assert "| HEAD | 2 | 3 | 3 | 0 | 0 |" in report
    assert "| HEAD~1 | Python | 2 | 4 | 2.00 | 0 | 3 |  |  |  |" in report
    assert "| HEAD | TypeScript | 1 | 1 | 1.00 | 0 | 1 | 2 | 1 | 2 |" in report
    assert main(["measure", str(tmp_path), "--at", "nope"]) == 2
    assert "git archive nope" in capsys.readouterr().err
