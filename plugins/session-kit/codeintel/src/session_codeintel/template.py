"""The project template: the quality bar as base files a project's own configs extend.

A family of projects shares its bar by copying, and every copy drifts.
Here the bar is stated once, in three base files the template owns
(``ruff.base.toml``, ``pyright.base.json``, ``scripts/check.base.sh``),
and a project's own ``pyproject.toml``, ``pyrightconfig.json`` and
``scripts/check`` extend them with the project's exceptions, each with
its reason. ``new`` writes the base files and the project's starting
files, leaving every file the project already has alone. ``refresh``
writes the base files back. ``check`` fails on a base file that differs
or is missing, on a project file that no longer extends its base, and on
a ruff setting that would discard the base's. The Python kind only, until
a project of another kind takes the bar.
"""

from __future__ import annotations

import json
import re
import shutil
import tomllib
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING, Literal

from session_codeintel import settings

if TYPE_CHECKING:
    from collections.abc import Iterator

DIRECTORY = Path(__file__).resolve().parent / "template" / "python"
"""Where the kind's files live. A ``.base.`` name is the template's, the rest the project's."""
BASE_MARK = ".base."
RENDERED = ".tmpl"
MODULE_DIR = "MODULE"
DOCS = "docs/"
PACKAGE = "session-codeintel"
COMMAND = "session-codeintel template"
DISCARDING = ("select", "per-file-ignores")
JSONC = re.compile(r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/', re.DOTALL)
COMMENTED = re.compile(r"^\s*(#|//|/\*|\*)")


@dataclass(frozen=True, slots=True)
class Delta:
    """The project's file that extends one base, and how its link to the base is read."""

    path: str
    form: Literal["toml", "jsonc", "line"]
    link: str
    """What ``check`` tells a project whose file has lost the link."""


DELTAS = {
    "ruff.base.toml": Delta("pyproject.toml", "toml", 'set [tool.ruff] extend = "ruff.base.toml"'),
    "pyright.base.json": Delta(
        "pyrightconfig.json", "jsonc", 'set "extends": "./pyright.base.json"'
    ),
    "scripts/check.base.sh": Delta(
        "scripts/check", "line", "run `bash scripts/check.base.sh` from it"
    ),
}


@dataclass(frozen=True, slots=True)
class Answers:
    """What ``new`` is told: the distribution name, the Python floor, whether to write the pages."""

    name: str
    python: str
    docs: bool = True

    @property
    def module(self) -> str:
        """The import name: the distribution name with its dashes as underscores."""
        return self.name.replace("-", "_")


@dataclass(frozen=True, slots=True)
class Written:
    """One file ``new`` or ``refresh`` dealt with."""

    path: str
    action: Literal["created", "skipped", "refreshed"]


@dataclass(frozen=True, slots=True)
class Finding:
    """One way a project has left the bar."""

    path: str
    problem: Literal["differs", "missing", "unlinked", "discards-base"]
    detail: str


def is_base(path: str) -> bool:
    """Whether a file is the template's (``.base.`` in its name) and not the project's."""
    return BASE_MARK in path.rsplit("/", 1)[-1]


def base_files() -> list[str]:
    """Return the base files the template writes, as POSIX paths, sorted."""
    return sorted(path for path, _ in _sources() if is_base(path))


def _sources() -> Iterator[tuple[str, Path]]:
    for source in sorted(DIRECTORY.rglob("*")):
        if source.is_file():
            yield source.relative_to(DIRECTORY).as_posix(), source


def _target(path: str, answers: Answers) -> str | None:
    if path.startswith(DOCS) and not answers.docs:
        return None
    path = path.removesuffix(RENDERED)
    return "/".join(answers.module if part == MODULE_DIR else part for part in path.split("/"))


def _render(source: Path, answers: Answers) -> bytes:
    if source.suffix != RENDERED:
        return source.read_bytes()
    raw = source.read_text(encoding="utf-8")
    if not answers.docs:
        raw = raw.replace("\n$readme", "")
    values = {
        "name": answers.name,
        "module": answers.module,
        "python": answers.python,
        "readme": 'readme = "docs/README.md"',
    }
    return Template(raw).substitute(values).encode("utf-8")


def _put(source: Path, content: bytes, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    shutil.copymode(source, target)


def new(project: Path, answers: Answers) -> list[Written]:
    """Write the template into the project: every base file, a project file only when absent."""
    written: list[Written] = []
    files = [(path, source) for path, source in _sources()]
    for path, source in sorted(files, key=lambda item: (not is_base(item[0]), item[0])):
        target_path = _target(path, answers)
        if target_path is None:
            continue
        target = project / target_path
        if target.exists() and not is_base(path):
            written.append(Written(target_path, "skipped"))
            continue
        action: Literal["created", "refreshed"] = "refreshed" if target.exists() else "created"
        _put(source, _render(source, answers), target)
        written.append(Written(target_path, action))
    return written


def refresh(project: Path) -> list[Written]:
    """Write back every base file whose bytes differ; the project's files are never touched."""
    written: list[Written] = []
    for path, source in _sources():
        if not is_base(path):
            continue
        target = project / path
        if target.is_file() and target.read_bytes() == source.read_bytes():
            continue
        _put(source, source.read_bytes(), target)
        written.append(Written(path, "refreshed"))
    return written


def check(project: Path) -> list[Finding]:
    """Compare each base file byte for byte, then each project file's link, then ruff's merge."""
    fix = f"run `{COMMAND} refresh {project}`"
    findings: list[Finding] = []
    for path, source in _sources():
        if not is_base(path):
            continue
        target = project / path
        if not target.is_file():
            findings.append(Finding(path, "missing", f"{path} is missing: {fix}"))
        elif target.read_bytes() != source.read_bytes():
            detail = (
                f"{path} differs from {COMMAND} {version(PACKAGE)}: {fix}, "
                f"or move the change into {DELTAS[path].path}"
            )
            findings.append(Finding(path, "differs", detail))
        findings.extend(_unlinked(project, path))
    findings.extend(_discarding(project / "pyproject.toml"))
    return findings


def _unlinked(project: Path, base: str) -> list[Finding]:
    delta = DELTAS[base]
    target = project / delta.path
    if target.is_file() and _links(target.read_text(encoding="utf-8"), delta.form, base):
        return []
    detail = (
        f"{delta.path} does not extend {base}, so the bar does not apply to this project: "
        f"{delta.link}"
    )
    return [Finding(delta.path, "unlinked", detail)]


def _links(text: str, form: Literal["toml", "jsonc", "line"], base: str) -> bool:
    named = (base, f"./{base}")
    if form == "line":
        return any(base in line for line in text.splitlines() if not COMMENTED.match(line))
    if form == "toml":
        return _ruff_table(text).get("extend") in named
    try:
        loaded: object = json.loads(without_comments(text))
    except ValueError:
        return False
    extends = loaded.get("extends") if settings.is_record(loaded) else None
    if isinstance(extends, str):
        return extends in named
    return any(one in named for one in settings.strings(extends))


def without_comments(text: str) -> str:
    """Strip the ``//`` and ``/* */`` comments of a JSONC text, keeping its strings whole."""
    return JSONC.sub(lambda found: found.group(1) or "", text)


def _ruff_table(text: str) -> dict[str, object]:
    try:
        parsed: dict[str, object] = tomllib.loads(text)
    except ValueError:
        return {}
    tool = parsed.get("tool")
    ruff = tool.get("ruff") if settings.is_record(tool) else None
    return ruff if settings.is_record(ruff) else {}


def _discarding(pyproject: Path) -> list[Finding]:
    if not pyproject.is_file():
        return []
    ruff = _ruff_table(pyproject.read_text(encoding="utf-8"))
    lint = ruff.get("lint")
    tables = {"[tool.ruff]": ruff, "[tool.ruff.lint]": lint if settings.is_record(lint) else {}}
    return [
        Finding(
            "pyproject.toml",
            "discards-base",
            f"pyproject.toml sets {table} {key}, which discards ruff.base.toml's: use extend-{key}",
        )
        for table, held in tables.items()
        for key in DISCARDING
        if key in held
    ]
