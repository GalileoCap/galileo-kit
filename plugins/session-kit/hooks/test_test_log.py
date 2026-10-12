"""Cases for test_log.py. Run it: python3 hooks/test_test_log.py

Each case hands the hook the payload Claude Code sends after a Bash call and
reads the log it keeps. TMPDIR points at a directory of this script's own, so
no log lands in the real temporary directory, and CLAUDE_PROJECT_DIR points at
a project of the case's choosing, so the runners of the project this script is
run from do not leak in.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

ORIGINAL_ENV = dict(os.environ)
TEMP = Path(os.path.realpath(tempfile.mkdtemp(prefix="claude-kit-test-log-")))
os.environ["TMPDIR"] = str(TEMP)
tempfile.tempdir = None  # read TMPDIR again

import test_log  # noqa: E402 - the module under test, beside this script, after TMPDIR is set


def project(base: Path, runners: list[str] | None) -> Path:
    """A project directory, with ``test_commands`` in its config when ``runners`` is given."""
    root = base / "project"
    root.mkdir(parents=True, exist_ok=True)
    if runners is not None:
        (root / ".claude").mkdir(exist_ok=True)
        (root / ".claude" / "claude-kit.json").write_text(
            json.dumps({"test_commands": runners}), encoding="utf-8"
        )
    return root


def passed(command: str, cwd: Path, session: str, stdout: str, stderr: str = "") -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command, "description": "run the tests"},
        "tool_response": {
            "stdout": stdout,
            "stderr": stderr,
            "interrupted": False,
            "isImage": False,
            "noOutputExpected": False,
        },
        "cwd": str(cwd),
        "session_id": session,
    }


def failed(command: str, cwd: Path, session: str, output: str) -> dict:
    return {
        "hook_event_name": "PostToolUseFailure",
        "tool_name": "Bash",
        "tool_input": {"command": command, "description": "run the tests"},
        "tool_use_id": "toolu_case",
        "error": output,
        "is_interrupt": False,
        "cwd": str(cwd),
        "session_id": session,
    }


def log_of(session: str) -> str:
    path = Path(test_log.log_path(session))
    return path.read_text(encoding="utf-8") if path.exists() else ""


def context(answer: dict | None, event: str) -> str:
    if answer is None:
        return ""
    output = answer.get("hookSpecificOutput", {})
    if output.get("hookEventName") != event:
        return ""
    return output.get("additionalContext", "")


CASES: list[tuple[str, bool]] = []


def case(name: str, run: Callable[[Path], object]) -> None:
    base = Path(tempfile.mkdtemp(dir=TEMP))
    os.environ["CLAUDE_PROJECT_DIR"] = str(project(base / "empty", None))
    try:
        ok = bool(run(base))
    except Exception as error:  # noqa: BLE001 - a case that raises is a failed case
        print(f"      {name}: {type(error).__name__}: {error}")
        ok = False
    CASES.append((name, ok))


# Where the log goes.


def log_in_tempdir(base: Path) -> bool:
    path = Path(test_log.log_path("s-path"))
    return (
        os.path.realpath(path.parent) == str(TEMP)
        and path.name == "claude-kit-last-test-s-path.log"
    )


case("the log is <tempdir>/claude-kit-last-test-<session_id>.log", log_in_tempdir)


# What a test run is.


def builtin_runners(base: Path) -> bool:
    cwd = str(base)
    return (
        test_log.is_test_run("uv run pytest -q tests", cwd)
        and test_log.is_test_run("pnpm test", cwd)
        and test_log.is_test_run("cd crate && cargo test --all", cwd)
    )


case("the guard's own runners are test runs", builtin_runners)


def ordinary_commands(base: Path) -> bool:
    cwd = str(base)
    return not test_log.is_test_run("ls -la && git status", cwd) and not test_log.is_test_run(
        "scripts/test changed", cwd
    )


case("an ordinary command, or a project runner nobody configured, is not", ordinary_commands)


def project_runner(base: Path) -> bool:
    root = project(base, ["scripts/test"])
    os.environ["CLAUDE_PROJECT_DIR"] = str(root)
    return test_log.is_test_run("scripts/test changed", str(root))


case("a test_commands entry of the project's config is a test run", project_runner)


def project_runner_from_cwd(base: Path) -> bool:
    root = project(base, ["scripts/test"])
    os.environ.pop("CLAUDE_PROJECT_DIR", None)
    return test_log.is_test_run("scripts/test changed", str(root))


case("without CLAUDE_PROJECT_DIR the project's config is read from the cwd", project_runner_from_cwd)


# A run that passed.


def pass_is_logged_quietly(base: Path) -> bool:
    cwd = project(base, None)
    answer = test_log.respond(
        passed("uv run pytest -q", cwd, "s-pass", "12 passed in 0.4s", "a warning on stderr")
    )
    log = log_of("s-pass")
    return (
        answer is None
        and "uv run pytest -q" in log
        and str(cwd) in log
        and "12 passed in 0.4s" in log
        and "a warning on stderr" in log
    )


case("a passing run writes the command, cwd, stdout and stderr, and says nothing", pass_is_logged_quietly)


# A run that failed.


def failure_is_logged_and_said(base: Path) -> bool:
    cwd = project(base, None)
    output = "Exit code 1\nFAILED tests/test_a.py::test_b - assert 1 == 2\n1 failed"
    answer = test_log.respond(failed("uv run pytest", cwd, "s-fail", output))
    said = context(answer, "PostToolUseFailure")
    return (
        "FAILED tests/test_a.py::test_b" in log_of("s-fail")
        and test_log.log_path("s-fail") in said
        and len(said.strip().splitlines()) == 1
    )


case("a failing run writes its error output and says where, in one line", failure_is_logged_and_said)


def project_runner_failure(base: Path) -> bool:
    root = project(base, ["scripts/test"])
    os.environ["CLAUDE_PROJECT_DIR"] = str(root)
    answer = test_log.respond(failed("scripts/test unit", root, "s-proj", "3 failed"))
    return "3 failed" in log_of("s-proj") and test_log.log_path("s-proj") in context(
        answer, "PostToolUseFailure"
    )


case("a project runner's failure is logged and said like a builtin's", project_runner_failure)


# What is not logged, and what is replaced.


def not_a_test_run(base: Path) -> bool:
    cwd = project(base, None)
    answers = [
        test_log.respond(passed("ls -la", cwd, "s-none", "a b c")),
        test_log.respond(failed("false", cwd, "s-none", "Exit code 1")),
    ]
    return answers == [None, None] and not Path(test_log.log_path("s-none")).exists()


case("a command that runs no tests writes no log and says nothing", not_a_test_run)


def written_whole(base: Path) -> bool:
    cwd = project(base, None)
    test_log.respond(failed("uv run pytest", cwd, "s-whole", "FAILED the-old-failure"))
    test_log.respond(passed("uv run pytest", cwd, "s-whole", "5 passed"))
    log = log_of("s-whole")
    return "5 passed" in log and "the-old-failure" not in log


case("each run replaces the session's log whole", written_whole)


def sessions_apart(base: Path) -> bool:
    cwd = project(base, None)
    test_log.respond(passed("pytest", cwd, "s-one", "output-of-one"))
    test_log.respond(passed("pytest", cwd, "s-two", "output-of-two"))
    return "output-of-two" not in log_of("s-one") and "output-of-one" in log_of("s-one")


case("two sessions keep two logs", sessions_apart)


os.environ.clear()
os.environ.update(ORIGINAL_ENV)
shutil.rmtree(TEMP, ignore_errors=True)

failures = [name for name, ok in CASES if not ok]
for name, ok in CASES:
    print(("ok    " if ok else "FAIL  ") + name)
print(f"{len(CASES) - len(failures)} passed, {len(failures)} failed")
sys.exit(1 if failures else 0)
