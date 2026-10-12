"""A ``pyrightconfig.json`` with one execution environment per package.

A language server started at the root of a repository that holds several
``uv`` projects sees one interpreter and one set of imports, and answers
"no references" for everything that lives in the others. This writes the
root config that gives each package its own: its sources, the sources of
the packages it depends on by path, and its own venv's ``site-packages``.

A checker run inside a package looks for a ``pyrightconfig.json`` in every
directory up to the root *before* it reads the package's own
``pyproject.toml``, so a package that keeps its checker settings in
``pyproject.toml`` would be checked under this file instead. Such a package
is named: its settings belong in a ``pyrightconfig.json`` of its own, which
the checker finds first.
"""

from __future__ import annotations

import json
import os
import re
import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

CONFIG = "pyrightconfig.json"


# The parts of a pyproject.toml this reads. The file is TOML, so tomllib's
# answer is untyped; these say which shape is trusted. A file that breaks it
# is one uv itself would refuse.
class _Checker(TypedDict, total=False):
    pythonVersion: str


_Project = TypedDict("_Project", {"requires-python": str}, total=False)


class _Source(TypedDict, total=False):
    path: str


class _Uv(TypedDict, total=False):
    sources: dict[str, _Source | list[_Source]]


class _Tool(TypedDict, total=False):
    basedpyright: _Checker
    pyright: _Checker
    uv: _Uv


class _Pyproject(TypedDict):
    project: _Project
    tool: _Tool


_FLOOR = re.compile(r">=\s*(\d+)\.(\d+)")
_VERSION = re.compile(r"^\s*version(?:_info)?\s*=\s*(\d+)\.(\d+)", re.MULTILINE)
_OWN_VERSION = re.compile(r'"pythonVersion"\s*:\s*"(\d+)\.(\d+)"')
_COMMENTS = re.compile(r"/\*.*?\*/|^\s*//[^\n]*", re.DOTALL | re.MULTILINE)


@dataclass(frozen=True, slots=True)
class Package:
    """One package of the repository, as the language server has to see it."""

    directory: str
    """Relative to the root, POSIX separators — also the environment's root."""
    python_version: str
    """``major.minor`` the package is checked against: ``pythonVersion`` in
    its own ``pyrightconfig.json``, else in ``[tool.basedpyright]`` or
    ``[tool.pyright]``, else the floor of ``requires-python``, else its
    interpreter's."""
    interpreter: str
    """``major.minor`` of the interpreter in its ``.venv`` (``pyvenv.cfg``),
    which names the ``site-packages`` directory."""
    sources: tuple[str, ...]
    """Its own source roots, relative to the root: ``src`` if it exists, else
    the package directory; then ``tests`` if it exists."""
    path_dependencies: tuple[str, ...]
    """Source roots of every ``[tool.uv.sources]`` entry with a ``path``,
    relative to the root, in the order the table lists them."""


@dataclass(frozen=True, slots=True)
class Discovery:
    """What a root holds: packages that can be written, and those that cannot."""

    packages: tuple[Package, ...]
    """Sorted by directory."""
    without_venv: tuple[str, ...]
    """Directories with a ``pyproject.toml`` and no ``.venv``, sorted."""
    overridden: tuple[str, ...] = ()
    """Written packages whose checker settings are in ``pyproject.toml``
    (``[tool.basedpyright]`` or ``[tool.pyright]``) with no
    ``pyrightconfig.json`` beside it, so the root file overrides them;
    sorted."""


def discover(root: Path) -> Discovery:
    """Every immediate subdirectory of ``root`` holding a ``pyproject.toml``.

    A directory without one is not a package and is ignored. POSIX venv
    layout only (``.venv/lib/python<major.minor>/site-packages``). A ``.venv``
    whose ``pyvenv.cfg`` names no version counts as none: ``uv sync`` is the
    fix for both.
    """
    packages: list[Package] = []
    without_venv: list[str] = []
    overridden: list[str] = []
    for directory in sorted(d for d in root.iterdir() if d.is_dir()):
        pyproject = directory / "pyproject.toml"
        if not pyproject.is_file():
            continue
        interpreter = _interpreter(directory / ".venv" / "pyvenv.cfg")
        if interpreter is None:
            without_venv.append(directory.name)
            continue
        project = _read(pyproject)
        own = directory / CONFIG
        if not own.is_file() and _configures_a_checker(project):
            overridden.append(directory.name)
        packages.append(
            Package(
                directory=directory.name,
                python_version=_own_version(own) or _python_version(project) or interpreter,
                interpreter=interpreter,
                sources=_sources(root, directory, with_tests=True),
                path_dependencies=_path_dependencies(root, directory, project),
            )
        )
    return Discovery(
        packages=tuple(packages),
        without_venv=tuple(without_venv),
        overridden=tuple(overridden),
    )


def render(packages: Sequence[Package]) -> str:
    """Render the ``pyrightconfig.json`` text: deterministic, trailing newline.

    Top-level ``pythonVersion`` is the newest package's: pyright reads the
    standard library's stubs at the top-level version whatever an
    environment says, and without one it takes whatever ``python3`` the
    server finds, which may predate names every package uses. Each
    package's own version still holds for its own code. Top-level
    ``include`` is every package's sources. One entry in
    ``executionEnvironments`` per package: ``root`` its directory,
    ``pythonVersion`` its python_version, ``extraPaths`` its sources, then its
    path dependencies' sources, then its venv's ``site-packages``.
    """
    newest = max((package.python_version for package in packages), key=_as_numbers)
    config = {
        "pythonVersion": newest,
        "include": [source for package in packages for source in package.sources],
        "executionEnvironments": [
            {
                "root": package.directory,
                "pythonVersion": package.python_version,
                "extraPaths": [
                    *package.sources,
                    *package.path_dependencies,
                    f"{package.directory}/.venv/lib/python{package.interpreter}/site-packages",
                ],
            }
            for package in packages
        ],
    }
    return json.dumps(config, indent=2) + "\n"


def write(root: Path) -> Discovery:
    """Discover, and write ``root/pyrightconfig.json`` if any package can be.

    Writes nothing when ``discover`` finds no writable package. Returns the
    discovery either way, so the caller can name what was left out. An
    unchanged file is not rewritten, so a server watching it does not reload.
    """
    discovery = discover(root)
    if discovery.packages:
        target = root / CONFIG
        text = render(discovery.packages)
        if not target.is_file() or target.read_text(encoding="utf-8") != text:
            target.write_text(text, encoding="utf-8")
    return discovery


def _interpreter(pyvenv: Path) -> str | None:
    """``major.minor`` from a venv's ``pyvenv.cfg``, or None with no usable venv."""
    if not pyvenv.is_file():
        return None
    found = _VERSION.search(pyvenv.read_text(encoding="utf-8"))
    return f"{found[1]}.{found[2]}" if found else None


def _own_version(config: Path) -> str | None:
    """Return the ``pythonVersion`` a package's own config states, if it has one.

    The file is JSON with comments, as pyright reads it; the comments are
    dropped before the version is looked for, so a commented-out line
    never counts.
    """
    if not config.is_file():
        return None
    found = _OWN_VERSION.search(_COMMENTS.sub("", config.read_text(encoding="utf-8")))
    return f"{found[1]}.{found[2]}" if found else None


def _configures_a_checker(pyproject: _Pyproject) -> bool:
    """Say whether ``pyproject.toml`` holds a table the root config would override."""
    return "basedpyright" in pyproject["tool"] or "pyright" in pyproject["tool"]


def _read(pyproject: Path) -> _Pyproject:
    """Read the two tables of a ``pyproject.toml`` this module looks at."""
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return {"project": data.get("project", {}), "tool": data.get("tool", {})}


def _python_version(pyproject: _Pyproject) -> str | None:
    """Say which version the package is checked against, as its own config states it."""
    tool = pyproject["tool"]
    for checker in (tool.get("basedpyright", {}), tool.get("pyright", {})):
        if "pythonVersion" in checker:
            return checker["pythonVersion"]
    floor = _FLOOR.search(pyproject["project"].get("requires-python", ""))
    return f"{floor[1]}.{floor[2]}" if floor else None


def _sources(root: Path, directory: Path, *, with_tests: bool) -> tuple[str, ...]:
    """List a directory's source roots, relative to ``root``: ``src`` or itself, then ``tests``."""
    found = [directory / "src" if (directory / "src").is_dir() else directory]
    if with_tests and (directory / "tests").is_dir():
        found.append(directory / "tests")
    return tuple(_relative(root, path) for path in found)


def _path_dependencies(root: Path, directory: Path, pyproject: _Pyproject) -> tuple[str, ...]:
    """List the source roots of the directories ``[tool.uv.sources]`` names by path.

    An entry may be one source or a list of them, each under its own marker;
    every one with a ``path`` to a directory counts.
    """
    found: list[str] = []
    for entry in pyproject["tool"].get("uv", {}).get("sources", {}).values():
        for source in entry if isinstance(entry, list) else [entry]:
            if "path" in source and (directory / source["path"]).is_dir():
                found.extend(_sources(root, directory / source["path"], with_tests=False))
    return tuple(found)


def _as_numbers(version: str) -> tuple[int, ...]:
    """``"3.12"`` as ``(3, 12)``, so 3.12 sorts after 3.9."""
    return tuple(int(part) for part in version.split("."))


def _relative(root: Path, path: Path) -> str:
    """``path`` relative to ``root``, POSIX separators."""
    return os.path.relpath(path.resolve(), root.resolve()).replace(os.sep, "/")
