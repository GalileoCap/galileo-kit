"""The project template: new, refresh and check, and the bar live over a fresh project."""

from __future__ import annotations

import json
import os
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

from session_codeintel import template
from session_codeintel.cli import main
from tests.tools import run

if TYPE_CHECKING:
    import pytest

RUFF = Path(sys.executable).parent / "ruff"
BASEDPYRIGHT = Path(sys.executable).parent / "basedpyright"
BASE = ("pyright.base.json", "ruff.base.toml", "scripts/check.base.sh")
PROJECT = (
    "docs/CHANGELOG.md",
    "docs/README.md",
    "docs/api.md",
    "docs/integrating.md",
    "docs/operating.md",
    "pyproject.toml",
    "pyrightconfig.json",
    "scripts/check",
    "scripts/test",
    "src/my_lib/__init__.py",
    "src/my_lib/py.typed",
    "tests/__init__.py",
)


def fresh(root: Path, *, docs: bool = True) -> Path:
    """Write a new project under the root, as the command does."""
    project = root / "my-lib"
    template.new(project, template.Answers("my-lib", "3.12", docs=docs))
    return project


def test_new_writes_the_base_files_and_the_project_files(tmp_path: Path) -> None:
    """Every file of the kind, the base files headed, the module named, the scripts runnable."""
    project = fresh(tmp_path)
    written = sorted(p.relative_to(project).as_posix() for p in project.rglob("*") if p.is_file())
    assert written == sorted(BASE + PROJECT)
    for base in BASE:
        assert "Written by session-codeintel template" in (project / base).read_text()
    pyproject = tomllib.loads((project / "pyproject.toml").read_text())
    assert pyproject["project"]["name"] == "my-lib"
    assert pyproject["project"]["readme"] == "docs/README.md"
    assert pyproject["project"]["requires-python"] == ">=3.12"
    assert pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["src/my_lib"]
    assert pyproject["tool"]["ruff"]["extend"] == "ruff.base.toml"
    assert os.access(project / "scripts/check", os.X_OK)
    assert os.access(project / "scripts/test", os.X_OK)
    assert json.loads(template.without_comments((project / "pyrightconfig.json").read_text())) == {
        "extends": "./pyright.base.json",
        "include": ["src", "tests"],
        "pythonVersion": "3.12",
    }


def test_without_docs_the_five_pages_and_the_readme_line_are_left_out(tmp_path: Path) -> None:
    """A project that keeps no developer docs gets no docs directory and no readme field."""
    project = fresh(tmp_path, docs=False)
    assert not (project / "docs").exists()
    assert "readme" not in tomllib.loads((project / "pyproject.toml").read_text())["project"]


def test_new_over_an_existing_project_leaves_its_files_alone(tmp_path: Path) -> None:
    """The base files are written, the project's own files are skipped and said so."""
    project = tmp_path / "old"
    (project / "src" / "old").mkdir(parents=True)
    (project / "pyproject.toml").write_text("[project]\nname = 'old'\n", encoding="utf-8")
    written = template.new(project, template.Answers("old", "3.12", docs=True))
    assert (project / "pyproject.toml").read_text() == "[project]\nname = 'old'\n"
    assert {w.action for w in written if w.path in BASE} == {"created"}
    assert [w.action for w in written if w.path == "pyproject.toml"] == ["skipped"]
    assert (project / "ruff.base.toml").is_file()


def test_refresh_writes_a_drifted_base_back_and_says_when_none_drifted(tmp_path: Path) -> None:
    """A base file edited by hand is replaced, a project file is never touched."""
    project = fresh(tmp_path)
    assert template.refresh(project) == []
    base = project / "ruff.base.toml"
    kept = base.read_bytes()
    base.write_text("line-length = 80\n", encoding="utf-8")
    (project / "pyproject.toml").write_text("[project]\nname = 'mine'\n", encoding="utf-8")
    assert [w.path for w in template.refresh(project)] == ["ruff.base.toml"]
    assert base.read_bytes() == kept
    assert (project / "pyproject.toml").read_text() == "[project]\nname = 'mine'\n"


def test_check_names_each_way_a_project_leaves_the_bar(tmp_path: Path) -> None:
    """A drifted base, a missing one, a file no longer extending its base, a discarding setting."""
    project = fresh(tmp_path)
    assert template.check(project) == []
    (project / "ruff.base.toml").write_text("line-length = 80\n", encoding="utf-8")
    (project / "pyright.base.json").unlink()
    pyproject = project / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text().replace('extend = "ruff.base.toml"', 'select = ["E"]')
        + '\n[tool.ruff.lint.per-file-ignores]\n"src/**" = ["D"]\n',
        encoding="utf-8",
    )
    check = project / "scripts/check"
    check.write_text("#!/usr/bin/env bash\n# bash scripts/check.base.sh\n", encoding="utf-8")
    findings = template.check(project)
    assert [(f.path, f.problem) for f in findings] == [
        ("pyright.base.json", "missing"),
        ("ruff.base.toml", "differs"),
        ("pyproject.toml", "unlinked"),
        ("scripts/check", "unlinked"),
        ("pyproject.toml", "discards-base"),
        ("pyproject.toml", "discards-base"),
    ]
    assert findings[1].detail == (
        f"ruff.base.toml differs from session-codeintel template {version('session-codeintel')}: "
        f"run `session-codeintel template refresh {project}`, "
        "or move the change into pyproject.toml"
    )
    assert findings[2].detail == (
        "pyproject.toml does not extend ruff.base.toml, so the bar does not apply to this "
        'project: set [tool.ruff] extend = "ruff.base.toml"'
    )
    assert findings[3].detail.endswith("run `bash scripts/check.base.sh` from it")
    assert findings[4].detail == (
        "pyproject.toml sets [tool.ruff] select, which discards ruff.base.toml's: use extend-select"
    )


def test_the_command_prints_and_exits_by_the_verdict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """New lists each file, refresh says up to date, check is one clean line or findings and 1."""
    project = tmp_path / "my-lib"
    assert main(["template", "new", str(project), "--name", "my-lib"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "created  pyright.base.json"
    assert len(lines) == len(BASE + PROJECT)
    assert main(["template", "refresh", str(project)]) == 0
    assert capsys.readouterr().out == "up to date\n"
    assert main(["template", "check", str(project)]) == 0
    assert capsys.readouterr().out == (
        f"3 base files match session-codeintel template {version('session-codeintel')}\n"
    )
    (project / "scripts/check.base.sh").unlink()
    assert main(["template", "check", str(project)]) == 1
    assert capsys.readouterr().err == (
        f"scripts/check.base.sh is missing: run `session-codeintel template refresh {project}`\n"
    )


def test_a_fresh_project_passes_the_bar_it_was_given(tmp_path: Path) -> None:
    """Ruff and basedpyright, run over the rendered project, find nothing to say."""
    project = fresh(tmp_path)
    for argv in (
        [str(RUFF), "check", "."],
        [str(RUFF), "format", "--check", "."],
        [str(BASEDPYRIGHT), "--warnings"],
    ):
        done = run(argv, project)
        assert done.returncode == 0, done.stdout + done.stderr
