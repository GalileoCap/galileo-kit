"""The generated pyrightconfig.json: one environment per package, nothing silent."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, TypedDict

from session_codeintel.cli import main
from session_codeintel.pyright_env import discover, write

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


class Environment(TypedDict):
    """One entry of ``executionEnvironments``; the keys are pyright's own."""

    root: str
    pythonVersion: str
    extraPaths: list[str]


class Config(TypedDict):
    """The parts of the generated file these tests read."""

    pythonVersion: str
    include: list[str]
    executionEnvironments: list[Environment]


def package(
    root: Path,
    name: str,
    *,
    pyproject: str,
    venv: str | None = "3.14.5",
    layout: tuple[str, ...] = ("src", "tests"),
) -> None:
    """Make a package directory; ``venv`` is the interpreter's version, None for none."""
    d = root / name
    d.mkdir()
    (d / "pyproject.toml").write_text(pyproject)
    for sub in layout:
        (d / sub).mkdir()
    if venv is not None:
        (d / ".venv").mkdir()
        (d / ".venv" / "pyvenv.cfg").write_text(f"home = /x\nversion_info = {venv}\n")


LOOP = '[project]\nname = "loop"\nrequires-python = ">=3.11"\n'
LOOP_CHECKER = '{\n  // the floor, not the venv\n  "pythonVersion": "3.12"\n}\n'
"""The package's own ``pyrightconfig.json``: JSON with comments, as pyright reads it."""
IN_PYPROJECT = '[project]\nname = "old"\n[tool.basedpyright]\npythonVersion = "3.13"\n'
DEMO = (
    '[project]\nname = "demo"\nrequires-python = ">=3.13"\n'
    '[tool.uv.sources]\nloop = { path = "../loop", editable = true }\n'
)


def config(root: Path) -> Config:
    """Read the generated file."""
    loaded: Config = json.loads((root / "pyrightconfig.json").read_text())
    return loaded


def environment(root: Path, directory: str) -> Environment:
    """Return the one execution environment whose root is ``directory``."""
    [env] = [e for e in config(root)["executionEnvironments"] if e["root"] == directory]
    return env


def test_one_environment_per_package_with_its_own_interpreter(tmp_path: Path) -> None:
    """Each package gets its own version, sources, path dependencies and venv."""
    package(tmp_path, "loop", pyproject=LOOP)
    (tmp_path / "loop" / "pyrightconfig.json").write_text(LOOP_CHECKER)
    package(tmp_path, "demo", pyproject=DEMO, venv="3.13.2")

    assert main(["pyright-env", str(tmp_path)]) == 0

    loop = environment(tmp_path, "loop")
    assert loop["pythonVersion"] == "3.12"
    assert loop["extraPaths"] == [
        "loop/src",
        "loop/tests",
        "loop/.venv/lib/python3.14/site-packages",
    ]
    demo = environment(tmp_path, "demo")
    assert demo["pythonVersion"] == "3.13"
    assert demo["extraPaths"] == [
        "demo/src",
        "demo/tests",
        "loop/src",
        "demo/.venv/lib/python3.13/site-packages",
    ]
    assert sorted(config(tmp_path)["include"]) == [
        "demo/src",
        "demo/tests",
        "loop/src",
        "loop/tests",
    ]


def test_a_flat_package_is_its_own_source_root(tmp_path: Path) -> None:
    """With no ``src`` and no ``tests``, the package directory is the source root."""
    package(tmp_path, "flat", pyproject=LOOP, layout=())
    assert main(["pyright-env", str(tmp_path)]) == 0
    assert environment(tmp_path, "flat")["extraPaths"] == [
        "flat",
        "flat/.venv/lib/python3.14/site-packages",
    ]


def test_a_package_without_a_venv_is_named_and_the_rest_still_written(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A package with no ``.venv`` is left out and named; the exit says so."""
    package(tmp_path, "loop", pyproject=LOOP)
    package(tmp_path, "client", pyproject=LOOP, venv=None)

    assert main(["pyright-env", str(tmp_path)]) == 1

    assert "client" in capsys.readouterr().err
    roots = [e["root"] for e in config(tmp_path)["executionEnvironments"]]
    assert roots == ["loop"]
    assert discover(tmp_path).without_venv == ("client",)


def test_nothing_writable_writes_nothing(tmp_path: Path) -> None:
    """With no package that can be written, no file appears and the exit is 2."""
    package(tmp_path, "client", pyproject=LOOP, venv=None)
    assert main(["pyright-env", str(tmp_path)]) == 2
    assert not (tmp_path / "pyrightconfig.json").exists()


def test_a_directory_without_a_pyproject_is_not_a_package(tmp_path: Path) -> None:
    """A directory with no ``pyproject.toml`` is neither written nor named."""
    package(tmp_path, "loop", pyproject=LOOP)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "src").mkdir()
    discovery = write(tmp_path)
    assert [p.directory for p in discovery.packages] == ["loop"]
    assert discovery.without_venv == ()


def test_two_runs_are_byte_identical(tmp_path: Path) -> None:
    """The output is deterministic and ends with a newline."""
    package(tmp_path, "loop", pyproject=LOOP)
    package(tmp_path, "demo", pyproject=DEMO)
    write(tmp_path)
    first = (tmp_path / "pyrightconfig.json").read_bytes()
    write(tmp_path)
    assert (tmp_path / "pyrightconfig.json").read_bytes() == first
    assert first.endswith(b"\n")


def test_a_checker_configured_in_pyproject_is_named_as_overridden(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The root file would override its pyproject settings: named, still written, exit 1."""
    package(tmp_path, "old", pyproject=IN_PYPROJECT)
    package(tmp_path, "loop", pyproject=LOOP)
    (tmp_path / "loop" / "pyrightconfig.json").write_text(LOOP_CHECKER)

    assert main(["pyright-env", str(tmp_path)]) == 1

    err = capsys.readouterr().err
    assert "old" in err
    assert "pyrightconfig.json" in err
    assert "loop" not in err
    assert environment(tmp_path, "old")["pythonVersion"] == "3.13"
    assert discover(tmp_path).overridden == ("old",)


def test_a_package_with_no_checker_settings_is_not_named(tmp_path: Path) -> None:
    """Nothing to override: the version falls to requires-python, the exit is 0."""
    package(tmp_path, "loop", pyproject=LOOP)
    assert main(["pyright-env", str(tmp_path)]) == 0
    assert environment(tmp_path, "loop")["pythonVersion"] == "3.11"
    assert discover(tmp_path).overridden == ()


def test_the_top_level_version_is_the_newest_packages(tmp_path: Path) -> None:
    """The standard library is read at the top-level version: the newest, by number."""
    package(tmp_path, "old", pyproject='[project]\nname = "old"\nrequires-python = ">=3.9"\n')
    package(tmp_path, "new", pyproject='[project]\nname = "new"\nrequires-python = ">=3.12"\n')
    assert main(["pyright-env", str(tmp_path)]) == 0
    assert config(tmp_path)["pythonVersion"] == "3.12"
