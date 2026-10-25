"""Cases for pyright_env.py. Run it: python3 hooks/test_pyright_env.py

Each case builds a project in its own temporary directory, with a stub `uv`
that records its argv, its working directory and UV_PROJECT_ENVIRONMENT, and
PATH narrowed to a directory of the case's choosing. The hook runs as a
subprocess with a JSON payload on stdin, the way Claude Code runs it at
SessionStart. Nothing outside the temporary directories is run or written.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
HOOK = PLUGIN / "hooks" / "pyright_env.py"
UNSET = "<unset>"
CLEARED = (
    "CLAUDE_PROJECT_DIR",
    "CLAUDE_PLUGIN_ROOT",
    "CLAUDE_PLUGIN_DATA",
    "UV_PROJECT_ENVIRONMENT",
)


def real(path: str | Path) -> str:
    return os.path.realpath(path)


def stub(path: Path, body: str) -> Path:
    """An executable shell script at ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def project(root: Path, config: str | None) -> Path:
    """A project root, with ``config`` as its .claude/claude-kit.json when given."""
    root.mkdir(parents=True, exist_ok=True)
    if config is not None:
        (root / ".claude").mkdir(exist_ok=True)
        (root / ".claude" / "claude-kit.json").write_text(config, encoding="utf-8")
    return root


ON = json.dumps({"pyright_env": True})


@dataclass
class Uv:
    """A stub uv in ``folder``, recording into ``record``. Builtins only: PATH holds nothing else."""

    folder: Path
    record: Path

    def ran(self) -> bool:
        return (self.record / "argv").exists()

    def argv(self) -> list[str]:
        return (self.record / "argv").read_text(encoding="utf-8").splitlines()

    def cwd(self) -> str:
        return (self.record / "cwd").read_text(encoding="utf-8").strip()

    def venv(self) -> str:
        return (self.record / "env").read_text(encoding="utf-8")


def fake_uv(base: Path, *, stdout: str = "", stderr: str = "", code: int = 0) -> Uv:
    folder, record = base / "bin", base / "record"
    record.mkdir(parents=True, exist_ok=True)
    out = base / "uv.stdout"
    err = base / "uv.stderr"
    out.write_text(stdout, encoding="utf-8")
    err.write_text(stderr, encoding="utf-8")
    body = "\n".join(
        [
            f"printf '%s\\n' \"$@\" > '{record}/argv'",
            f"pwd -P > '{record}/cwd'",
            f"printf '%s' \"${{UV_PROJECT_ENVIRONMENT-{UNSET}}}\" > '{record}/env'",
            # read builtins only: cat is not on PATH
            f"while IFS= read -r line || [ -n \"$line\" ]; do printf '%s\\n' \"$line\"; done < '{out}'",
            f"while IFS= read -r line || [ -n \"$line\" ]; do printf '%s\\n' \"$line\" >&2; done < '{err}'",
            f"exit {code}",
        ]
    )
    stub(folder / "uv", body)
    return Uv(folder, record)


@dataclass
class Result:
    code: int
    stdout: str
    stderr: str


def run_hook(
    stdin: str,
    *,
    path: Path,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> Result:
    environment = {key: value for key, value in os.environ.items() if key not in CLEARED}
    environment["PATH"] = str(path)
    environment.update(env or {})
    path.mkdir(parents=True, exist_ok=True)
    done = subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
        cwd=str(cwd),
        check=False,
    )
    return Result(done.returncode, done.stdout, done.stderr)


def silent(result: Result) -> bool:
    return result.code == 0 and result.stdout.strip() == ""


def expected_message(detail: str) -> dict:
    return {
        "systemMessage": f"Navigation is partial: {detail}",
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                f"pyrightconfig.json (the language server's view of the packages): {detail}"
            ),
        },
    }


def argv_is(uv: Uv, plugin_root: Path, root: Path) -> bool:
    argv = uv.argv()
    return (
        len(argv) == 8
        and argv[0:4] == ["run", "--quiet", "--frozen", "--project"]
        and real(argv[4]) == real(plugin_root / "codeintel")
        and argv[5] == "session-codeintel"
        and argv[6] == "pyright-env"
        and real(argv[7]) == real(root)
    )


CASES: list[tuple[str, bool]] = []


def case(name: str, run: Callable[[Path], object]) -> None:
    with tempfile.TemporaryDirectory() as folder:
        base = Path(real(folder))
        try:
            ok = bool(run(base))
        except Exception as error:  # noqa: BLE001  the runner reports a case that raises as a failed case instead of stopping the run
            print(f"      {name}: {type(error).__name__}: {error}")
            ok = False
    CASES.append((name, ok))


# Off unless the project says so.


def off_case(config: str | None) -> Callable[[Path], bool]:
    def run(base: Path) -> bool:
        root = project(base / "proj", config)
        uv = fake_uv(base, stdout="out\n", stderr="err\n", code=1)
        result = run_hook("{}", path=uv.folder, cwd=root, env={"CLAUDE_PROJECT_DIR": str(root)})
        return silent(result) and not uv.ran()

    return run


case("off by default: no .claude/claude-kit.json, uv never runs", off_case(None))
case("off for a missing key", off_case(json.dumps({"tells": {}})))
case('off for "pyright_env": "yes"', off_case(json.dumps({"pyright_env": "yes"})))
case('off for "pyright_env": false', off_case(json.dumps({"pyright_env": False})))
case('off for "pyright_env": 1', off_case(json.dumps({"pyright_env": 1})))
case("off for a config that is not valid JSON", off_case('{"pyright_env": true'))
case(
    "off for a config whose top level is not an object",
    off_case(json.dumps([{"pyright_env": True}])),
)


case(
    "off when the key is nested rather than top-level",
    off_case(json.dumps({"tells": {"pyright_env": True}})),
)


def on_without_uv(base: Path) -> bool:
    root = project(base / "proj", ON)
    empty = base / "empty"
    result = run_hook("{}", path=empty, cwd=root, env={"CLAUDE_PROJECT_DIR": str(root)})
    return silent(result)


case("on with no uv on PATH: no output, exit 0", on_without_uv)


# The command it runs.


def argv_default_plugin_root(base: Path) -> bool:
    root = project(base / "proj", ON)
    uv = fake_uv(base)
    elsewhere = base / "elsewhere"
    elsewhere.mkdir()
    result = run_hook(
        json.dumps({"cwd": str(root)}),
        path=uv.folder,
        cwd=elsewhere,
        env={"CLAUDE_PROJECT_DIR": str(root)},
    )
    return (
        silent(result)
        and uv.ran()
        and argv_is(uv, PLUGIN, root)
        and real(uv.cwd()) == real(root)
        and uv.venv() == str(PLUGIN / "venv-codeintel")
    )


case(
    "without CLAUDE_PLUGIN_ROOT or _DATA: the hook's plugin, cwd the root, venv beside the plugin",
    argv_default_plugin_root,
)


def argv_plugin_root_and_data(base: Path) -> bool:
    root = project(base / "proj", ON)
    plugin_root = base / "plugin"
    data = base / "data"
    plugin_root.mkdir()
    data.mkdir()
    uv = fake_uv(base)
    result = run_hook(
        "{}",
        path=uv.folder,
        cwd=base,
        env={
            "CLAUDE_PROJECT_DIR": str(root),
            "CLAUDE_PLUGIN_ROOT": str(plugin_root),
            "CLAUDE_PLUGIN_DATA": str(data),
        },
    )
    return (
        silent(result)
        and uv.ran()
        and argv_is(uv, plugin_root, root)
        and real(uv.cwd()) == real(root)
        and uv.venv() == str(data / "venv-codeintel")
    )


case(
    "CLAUDE_PLUGIN_ROOT names the codeintel project, CLAUDE_PLUGIN_DATA holds the venv",
    argv_plugin_root_and_data,
)


def plugin_root_without_data(base: Path) -> bool:
    root = project(base / "proj", ON)
    plugin_root = base / "plugin"
    plugin_root.mkdir()
    uv = fake_uv(base)
    result = run_hook(
        "{}",
        path=uv.folder,
        cwd=base,
        env={"CLAUDE_PROJECT_DIR": str(root), "CLAUDE_PLUGIN_ROOT": str(plugin_root)},
    )
    return (
        silent(result)
        and uv.ran()
        and argv_is(uv, plugin_root, root)
        and uv.venv() == str(plugin_root / "venv-codeintel")
    )


case("CLAUDE_PLUGIN_ROOT without _DATA: the venv sits in the plugin root", plugin_root_without_data)


# Which root.


def env_over_stdin(base: Path) -> bool:
    chosen = project(base / "chosen", ON)
    other = project(base / "other", ON)
    uv = fake_uv(base)
    result = run_hook(
        json.dumps({"cwd": str(other)}),
        path=uv.folder,
        cwd=other,
        env={"CLAUDE_PROJECT_DIR": str(chosen)},
    )
    return (
        silent(result)
        and uv.ran()
        and real(uv.argv()[-1]) == real(chosen)
        and real(uv.cwd()) == real(chosen)
    )


case("CLAUDE_PROJECT_DIR wins over the payload's cwd and the process's", env_over_stdin)


def env_root_off_wins(base: Path) -> bool:
    chosen = project(base / "chosen", None)
    other = project(base / "other", ON)
    uv = fake_uv(base)
    result = run_hook(
        json.dumps({"cwd": str(other)}),
        path=uv.folder,
        cwd=other,
        env={"CLAUDE_PROJECT_DIR": str(chosen)},
    )
    return silent(result) and not uv.ran()


case("the config is read from CLAUDE_PROJECT_DIR's root, not the payload's cwd", env_root_off_wins)


def stdin_cwd_over_process(base: Path) -> bool:
    chosen = project(base / "chosen", ON)
    other = project(base / "other", ON)
    uv = fake_uv(base)
    result = run_hook(json.dumps({"cwd": str(chosen)}), path=uv.folder, cwd=other)
    return (
        silent(result)
        and uv.ran()
        and real(uv.argv()[-1]) == real(chosen)
        and real(uv.cwd()) == real(chosen)
    )


case("without CLAUDE_PROJECT_DIR the payload's cwd is the root", stdin_cwd_over_process)


def process_cwd_last(base: Path) -> bool:
    root = project(base / "proj", ON)
    uv = fake_uv(base)
    result = run_hook("{}", path=uv.folder, cwd=root)
    return (
        silent(result)
        and uv.ran()
        and real(uv.argv()[-1]) == real(root)
        and real(uv.cwd()) == real(root)
    )


case("with neither, the process's working directory is the root", process_cwd_last)


def bad_stdin(text: str) -> Callable[[Path], bool]:
    def run(base: Path) -> bool:
        root = project(base / "proj", ON)
        uv = fake_uv(base)
        result = run_hook(text, path=uv.folder, cwd=base, env={"CLAUDE_PROJECT_DIR": str(root)})
        return silent(result) and uv.ran() and real(uv.argv()[-1]) == real(root)

    return run


case("empty stdin is read as {} and the hook still runs", bad_stdin(""))
case("stdin that is not JSON is read as {} and the hook still runs", bad_stdin("not json"))


# What it says.


def success_is_silent(base: Path) -> bool:
    root = project(base / "proj", ON)
    uv = fake_uv(base, stdout="wrote pyrightconfig.json\n3 packages\n", code=0)
    result = run_hook("{}", path=uv.folder, cwd=root, env={"CLAUDE_PROJECT_DIR": str(root)})
    return uv.ran() and result.code == 0 and result.stdout == ""


case("a command that exits 0 leaves no output, its stdout not echoed", success_is_silent)


def failure_message(base: Path) -> bool:
    root = project(base / "proj", ON)
    uv = fake_uv(
        base,
        stdout="this is not echoed\n",
        stderr="  left out: tagents-demo (no venv)  \n\n\tleft out: abstract-http\n   \n",
        code=2,
    )
    result = run_hook("{}", path=uv.folder, cwd=root, env={"CLAUDE_PROJECT_DIR": str(root)})
    if result.code != 0 or not uv.ran():
        return False
    detail = "left out: tagents-demo (no venv); left out: abstract-http"
    return json.loads(result.stdout) == expected_message(detail)


case(
    "a failure's stderr lines, stripped and joined by '; ', make the exact message", failure_message
)


def failure_without_stderr(base: Path) -> bool:
    root = project(base / "proj", ON)
    uv = fake_uv(base, code=3)
    result = run_hook("{}", path=uv.folder, cwd=root, env={"CLAUDE_PROJECT_DIR": str(root)})
    if result.code != 0 or not uv.ran():
        return False
    return json.loads(result.stdout) == expected_message("pyright-env exited 3")


case("a failure with empty stderr names the exit code", failure_without_stderr)


def one_line_failure(base: Path) -> bool:
    root = project(base / "proj", ON)
    uv = fake_uv(base, stderr="no packages found\n", code=1)
    result = run_hook("{}", path=uv.folder, cwd=root, env={"CLAUDE_PROJECT_DIR": str(root)})
    return result.code == 0 and json.loads(result.stdout) == expected_message("no packages found")


case("a one-line stderr is the detail as it stands", one_line_failure)


if not HOOK.exists():
    print(f"note: {HOOK} does not exist yet; every case below fails for that reason")

failed = [name for name, ok in CASES if not ok]
for name, ok in CASES:
    print(("ok    " if ok else "FAIL  ") + name)
print(f"{len(CASES) - len(failed)} passed, {len(failed)} failed")
sys.exit(1 if failed else 0)
