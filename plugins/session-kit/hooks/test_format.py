"""Cases for format.py. Run it: python3 hooks/test_format.py

Each case builds a project layout in its own temporary directory, with stub
executables standing in for uv, ruff, oxlint and biome, and PATH narrowed to a
directory of the case's choosing, then reads which tool runs format a file,
from where. Nothing outside the temporary directories is run or written.
"""

from __future__ import annotations

import contextlib
import io
import os
import stat
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

import format as fmt  # the module under test, beside this script

ORIGINAL_PATH = os.environ.get("PATH", "")


def stub(path: Path, body: str = "exit 0") -> Path:
    """An executable shell script at ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def plant(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def on_path(folder: Path, *tools: str) -> None:
    """PATH holds only ``folder``, with a stub for each tool named."""
    folder.mkdir(parents=True, exist_ok=True)
    for tool in tools:
        stub(folder / tool)
    os.environ["PATH"] = str(folder)


def real(path: str | Path) -> str:
    return os.path.realpath(path)


def tool(step: fmt.Step) -> str:
    return os.path.basename(step.argv[0])


def names(step: fmt.Step, path: Path) -> bool:
    """Whether the step's argv names the file, absolute or relative to its cwd."""
    return any(real(os.path.join(step.cwd, arg)) == real(path) for arg in step.argv[1:])


def ruff_pair(steps: list[fmt.Step], path: Path, cwd: Path, runner: str) -> bool:
    """Two steps: ``ruff check --fix`` then ``ruff format``, by ``runner``, from ``cwd``."""
    if len(steps) != 2:
        return False
    check, form = steps
    prefix = ("run", "ruff") if runner == "uv" else ()
    return (
        tool(check) == runner
        and tool(form) == runner
        and check.argv[1 : 1 + len(prefix)] == prefix
        and form.argv[1 : 1 + len(prefix)] == prefix
        and "check" in check.argv
        and "--fix" in check.argv
        and "format" in form.argv
        and "check" not in form.argv
        and names(check, path)
        and names(form, path)
        and real(check.cwd) == real(cwd)
        and real(form.cwd) == real(cwd)
    )


CASES: list[tuple[str, bool]] = []


def case(name: str, run: Callable[[Path], object]) -> None:
    with tempfile.TemporaryDirectory() as folder:
        base = Path(real(folder))
        try:
            ok = bool(run(base))
        except Exception as error:  # noqa: BLE001  (decisions.md, 2)
            print(f"      {name}: {type(error).__name__}: {error}")
            ok = False
        finally:
            os.environ["PATH"] = ORIGINAL_PATH
    CASES.append((name, ok))


RUFF_PYPROJECT = '[project]\nname = "p"\n\n[tool.ruff]\nline-length = 100\n'
PLAIN_PYPROJECT = '[project]\nname = "p"\n'


# Python.


def uv_project(base: Path) -> bool:
    root = base / "proj"
    plant(root, {"pyproject.toml": RUFF_PYPROJECT, "uv.lock": "", "src/a.py": "x = 1\n"})
    on_path(base / "bin", "uv", "ruff")
    path = root / "src" / "a.py"
    return ruff_pair(fmt.steps_for(str(path)), path, root, "uv")


case("a pyproject with [tool.ruff], a uv.lock and uv on PATH runs uv run ruff", uv_project)


def ruff_without_lock(base: Path) -> bool:
    root = base / "proj"
    plant(root, {"pyproject.toml": RUFF_PYPROJECT, "a.py": "x = 1\n"})
    on_path(base / "bin", "uv", "ruff")
    path = root / "a.py"
    return ruff_pair(fmt.steps_for(str(path)), path, root, "ruff")


case("without a uv.lock, ruff runs from PATH", ruff_without_lock)


def ruff_without_uv(base: Path) -> bool:
    root = base / "proj"
    plant(root, {"pyproject.toml": RUFF_PYPROJECT, "uv.lock": "", "a.py": "x = 1\n"})
    on_path(base / "bin", "ruff")
    path = root / "a.py"
    return ruff_pair(fmt.steps_for(str(path)), path, root, "ruff")


case("a uv.lock with no uv on PATH falls back to ruff from PATH", ruff_without_uv)


def no_ruff_anywhere(base: Path) -> bool:
    root = base / "proj"
    plant(root, {"pyproject.toml": RUFF_PYPROJECT, "a.py": "x = 1\n"})
    on_path(base / "bin")
    return fmt.steps_for(str(root / "a.py")) == []


case("with neither uv nor ruff on PATH, nothing runs", no_ruff_anywhere)


def pyproject_without_ruff(base: Path) -> bool:
    root = base / "proj"
    plant(root, {"pyproject.toml": PLAIN_PYPROJECT, "uv.lock": "", "a.py": "x = 1\n"})
    on_path(base / "bin", "uv", "ruff")
    return fmt.steps_for(str(root / "a.py")) == []


case("a pyproject without [tool.ruff] and no ruff.toml runs nothing", pyproject_without_ruff)


def ruff_toml(base: Path) -> bool:
    root = base / "proj"
    plant(root, {"pyproject.toml": PLAIN_PYPROJECT, "ruff.toml": "", "a.py": "x = 1\n"})
    on_path(base / "bin", "ruff")
    path = root / "a.py"
    return ruff_pair(fmt.steps_for(str(path)), path, root, "ruff")


case("a ruff.toml beside a plain pyproject turns ruff on", ruff_toml)


def dot_ruff_toml_alone(base: Path) -> bool:
    root = base / "proj"
    plant(root, {".ruff.toml": "", "pkg/a.pyi": "x: int\n"})
    on_path(base / "bin", "ruff")
    path = root / "pkg" / "a.pyi"
    return ruff_pair(fmt.steps_for(str(path)), path, root, "ruff")


case("a .ruff.toml alone turns ruff on, for a .pyi too, from its directory", dot_ruff_toml_alone)


def nearest_pyproject_wins(base: Path) -> bool:
    root = base / "proj"
    plant(
        root,
        {
            "pyproject.toml": RUFF_PYPROJECT,
            "vendor/pkg/pyproject.toml": PLAIN_PYPROJECT,
            "vendor/pkg/src/a.py": "x = 1\n",
        },
    )
    on_path(base / "bin", "ruff")
    return fmt.steps_for(str(root / "vendor" / "pkg" / "src" / "a.py")) == []


case(
    "the nearest pyproject decides: a plain one below a ruff one runs nothing",
    nearest_pyproject_wins,
)


def nested_package_runs_from_itself(base: Path) -> bool:
    root = base / "proj"
    plant(
        root,
        {
            "pyproject.toml": PLAIN_PYPROJECT,
            "packages/core/pyproject.toml": RUFF_PYPROJECT,
            "packages/core/uv.lock": "",
            "packages/core/src/deep/a.py": "x = 1\n",
        },
    )
    on_path(base / "bin", "uv")
    path = root / "packages" / "core" / "src" / "deep" / "a.py"
    return ruff_pair(fmt.steps_for(str(path)), path, root / "packages" / "core", "uv")


case("ruff runs from the package directory that holds the config", nested_package_runs_from_itself)


def excluded_file_stays_excluded(base: Path) -> bool:
    """Ruff applies the project's ``exclude`` to a file named on its command line only with
    ``--force-exclude``, and the hook always names the file, so a generated file the project
    keeps out of ruff would be reformatted without it."""
    root = base / "proj"
    plant(root, {"pyproject.toml": RUFF_PYPROJECT, "uv.lock": "", "src/models.py": "x = 1\n"})
    on_path(base / "bin", "uv", "ruff")
    steps = fmt.steps_for(str(root / "src" / "models.py"))
    return len(steps) == 2 and all("--force-exclude" in step.argv for step in steps)


case("both ruff steps keep a file the project excludes excluded", excluded_file_stays_excluded)


# TypeScript and JavaScript.


def node_bin(root: Path, *tools: str) -> None:
    for name in tools:
        stub(root / "node_modules" / ".bin" / name)


def binary(step: fmt.Step) -> str:
    return real(os.path.join(step.cwd, step.argv[0]))


def oxlint_then_biome(base: Path) -> bool:
    root = base / "web"
    plant(
        root,
        {
            "package.json": "{}",
            ".oxlintrc.json": "{}",
            "biome.json": "{}",
            "src/app/a.ts": "export const a = 1;\n",
        },
    )
    node_bin(root, "oxlint", "biome")
    on_path(base / "bin")
    path = root / "src" / "app" / "a.ts"
    steps = fmt.steps_for(str(path))
    bin_dir = root / "node_modules" / ".bin"
    return (
        len(steps) == 2
        and binary(steps[0]) == real(bin_dir / "oxlint")
        and "--fix" in steps[0].argv
        and binary(steps[1]) == real(bin_dir / "biome")
        and steps[1].argv[1:3] == ("check", "--write")
        and all(names(step, path) for step in steps)
        and all(real(step.cwd) == real(root) for step in steps)
    )


case("oxlint --fix then biome check --write, from node_modules/.bin, from its parent", oxlint_then_biome)


def config_variants(base: Path) -> bool:
    root = base / "web"
    plant(root, {"oxlint.json": "{}", "biome.jsonc": "{}", "a.jsx": "export {};\n"})
    node_bin(root, "oxlint", "biome")
    on_path(base / "bin")
    steps = fmt.steps_for(str(root / "a.jsx"))
    return [tool(step) for step in steps] == ["oxlint", "biome"]


case("oxlint.json and biome.jsonc count, for a .jsx", config_variants)


def config_without_binary(base: Path) -> bool:
    root = base / "web"
    plant(root, {".oxlintrc.json": "{}", "biome.json": "{}", "a.mts": "export {};\n"})
    node_bin(root, "oxlint")
    on_path(base / "bin", "biome")
    steps = fmt.steps_for(str(root / "a.mts"))
    return [tool(step) for step in steps] == ["oxlint"]


case("a tool with a config and no node_modules binary is skipped, PATH or not", config_without_binary)


def binary_without_config(base: Path) -> bool:
    root = base / "web"
    plant(root, {"package.json": "{}", "a.ts": "export {};\n"})
    node_bin(root, "oxlint", "biome")
    on_path(base / "bin")
    return fmt.steps_for(str(root / "a.ts")) == []


case("binaries with no config run nothing", binary_without_config)


def monorepo(base: Path) -> bool:
    root = base / "repo"
    plant(
        root,
        {
            "biome.json": "{}",
            "apps/web/package.json": "{}",
            "apps/web/src/a.tsx": "export {};\n",
        },
    )
    node_bin(root / "apps" / "web", "biome")
    node_bin(root, "biome")
    on_path(base / "bin")
    steps = fmt.steps_for(str(root / "apps" / "web" / "src" / "a.tsx"))
    web = root / "apps" / "web"
    return (
        len(steps) == 1
        and binary(steps[0]) == real(web / "node_modules" / ".bin" / "biome")
        and real(steps[0].cwd) == real(web)
    )


case("the config is found upward and the nearest node_modules runs it", monorepo)


def other_suffix(base: Path) -> bool:
    root = base / "proj"
    plant(root, {"pyproject.toml": RUFF_PYPROJECT, "biome.json": "{}", "notes.md": "# x\n"})
    node_bin(root, "biome")
    on_path(base / "bin", "ruff")
    return fmt.steps_for(str(root / "notes.md")) == []


case("a suffix neither language owns runs nothing", other_suffix)


# Which files an edit wrote.


def edit_payload(path: Path) -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(path), "old_string": "x = 1", "new_string": "x = 2"},
        "tool_response": {
            "filePath": str(path),
            "oldString": "x = 1",
            "newString": "x = 2",
            "originalFile": "x = 1\n",
            "replaceAll": False,
            "structuredPatch": [
                {"oldStart": 1, "oldLines": 1, "newStart": 1, "newLines": 1,
                 "lines": ["-x = 1", "+x = 2"]}
            ],
            "userModified": False,
        },
        "cwd": str(path.parent),
        "session_id": "case",
    }


def write_payload(path: Path) -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": "x = 1\n"},
        "tool_response": {
            "type": "create",
            "filePath": str(path),
            "content": "x = 1\n",
            "originalFile": None,
            "structuredPatch": [],
        },
        "cwd": str(path.parent),
        "session_id": "case",
    }


def bash_payload(cwd: Path, files: list[Path] | None) -> dict:
    response: dict = {
        "stdout": "",
        "stderr": "",
        "interrupted": False,
        "isImage": False,
        "noOutputExpected": False,
    }
    if files is not None:
        response["bashEditDiff"] = {
            "files": [
                {"filePath": str(path),
                 "hunks": [{"oldStart": 1, "oldLines": 1, "newStart": 1, "newLines": 1,
                            "lines": ["-a", "+b"]}]}
                for path in files
            ]
        }
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "sed -i s/a/b/ *.py", "description": "edit"},
        "tool_response": response,
        "cwd": str(cwd),
        "session_id": "case",
    }


def edit_and_write(base: Path) -> bool:
    path = base / "a.py"
    path.write_text("x = 2\n", encoding="utf-8")
    return fmt.written_files(edit_payload(path)) == [str(path)] and fmt.written_files(
        write_payload(path)
    ) == [str(path)]


case("an Edit and a Write each name their file", edit_and_write)


def bash_files_in_order_once(base: Path) -> bool:
    first, second = base / "b.py", base / "a.ts"
    for path in (first, second):
        path.write_text("b\n", encoding="utf-8")
    payload = bash_payload(base, [first, second, first])
    return fmt.written_files(payload) == [str(first), str(second)]


case("a Bash call's edited files come in order, each once", bash_files_in_order_once)


def bash_deleted_file(base: Path) -> bool:
    kept, gone = base / "kept.py", base / "gone.py"
    kept.write_text("b\n", encoding="utf-8")
    return fmt.written_files(bash_payload(base, [gone, kept])) == [str(kept)]


case("a file the Bash call left missing is not named", bash_deleted_file)


def nothing_written(base: Path) -> bool:
    read = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Read",
        "tool_input": {"file_path": str(base / "a.py")},
        "tool_response": {"type": "text"},
        "cwd": str(base),
        "session_id": "case",
    }
    return fmt.written_files(bash_payload(base, None)) == [] and fmt.written_files(read) == []


case("a Bash call that edited nothing, and a Read, name no files", nothing_written)


# The whole answer.


def logging_ruff(base: Path, check_body: str) -> Path:
    """A ruff on PATH that logs ``<cwd> <args>`` and runs ``check_body`` for ``check``."""
    log = base / "ruff.log"
    folder = base / "bin"
    stub(
        folder / "ruff",
        f'echo "$(pwd -P) $*" >> "{log}"\n'
        'case "$1" in check) ' + check_body + " ;; esac\nexit 0",
    )
    os.environ["PATH"] = str(folder)
    return log


def respond_runs_in_order(base: Path) -> bool:
    root = base / "proj"
    plant(root, {"pyproject.toml": RUFF_PYPROJECT, "a.py": "x = 2\n"})
    log = logging_ruff(base, "exit 0")
    answer = fmt.respond(edit_payload(root / "a.py"))
    lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return (
        answer is None
        and len(lines) == 2
        and lines[0].startswith(real(root) + " check")
        and lines[1].startswith(real(root) + " format")
    )


case("a clean run checks then formats, from the project, and says nothing", respond_runs_in_order)


def respond_names_what_is_left(base: Path) -> bool:
    root = base / "proj"
    plant(root, {"pyproject.toml": RUFF_PYPROJECT, "a.py": "import os\n"})
    logging_ruff(base, 'echo "a.py:1:8: F401 [*] os imported but unused"; exit 1')
    answer = fmt.respond(edit_payload(root / "a.py"))
    if answer is None:
        return False
    context = answer["hookSpecificOutput"]["additionalContext"]
    return "F401" in context


case("a lint finding the fix left reaches the session", respond_names_what_is_left)


def respond_without_tools(base: Path) -> bool:
    plant(base, {"notes.txt": "x\n"})
    on_path(base / "bin")
    return fmt.respond(write_payload(base / "notes.txt")) is None


case("a file with no formatter says nothing", respond_without_tools)


def main_on_garbage(base: Path) -> bool:
    out = io.StringIO()
    stdin = sys.stdin
    sys.stdin = io.StringIO("not json")
    try:
        with contextlib.redirect_stdout(out):
            fmt.main()
    finally:
        sys.stdin = stdin
    return out.getvalue() == ""


case("main on a payload that is not JSON prints nothing and does not raise", main_on_garbage)


failed = [name for name, ok in CASES if not ok]
for name, ok in CASES:
    print(("ok    " if ok else "FAIL  ") + name)
print(f"{len(CASES) - len(failed)} passed, {len(failed)} failed")
sys.exit(1 if failed else 0)
