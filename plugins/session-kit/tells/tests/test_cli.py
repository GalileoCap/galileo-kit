"""``session-tells``: show, check and hook, from the command line."""

from __future__ import annotations

import io
import json
from typing import TYPE_CHECKING

from session_tells import rules
from session_tells.cli import main

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _plant(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _fix(name: str) -> str:
    (rule,) = [rule for rule in rules.RULES if rule.name == name]
    return rule.fix


def test_check_fails_on_a_banned_tell_and_names_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``check`` exits 1 when a file holds a banned tell, and prints where."""
    _plant(tmp_path, "docs/a.md", "This is truly odd.\n")
    assert main(["check", "--root", str(tmp_path), "docs/a.md"]) == 1
    assert "docs/a.md:1" in capsys.readouterr().out


def test_check_passes_on_rationed_tells_alone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``check`` exits 0 when the only tells are rationed, and does not list them."""
    _plant(tmp_path, "docs/a.md", "Stop; wait.\n")
    assert main(["check", "--root", str(tmp_path), "docs/a.md"]) == 0
    assert "semicolon" not in capsys.readouterr().out


def test_show_lists_banned_and_rationed_with_their_fixes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``show`` lists every tell with its fix and exits 0 whatever it finds."""
    _plant(tmp_path, "docs/a.md", "Stop; wait.\n\nWe stop in order to wait.\n")
    assert main(["show", "--root", str(tmp_path), "docs/a.md"]) == 0
    out = capsys.readouterr().out
    assert "semicolon" in out
    assert _fix("semicolon") in out
    assert "filler-phrase" in out
    assert _fix("filler-phrase") in out


def test_a_file_may_be_given_absolute_inside_the_root(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An absolute path inside the root reads as its root-relative path."""
    path = _plant(tmp_path, "docs/a.md", "A — dash.\n")
    assert main(["check", "--root", str(tmp_path), str(path)]) == 1
    assert "docs/a.md:1" in capsys.readouterr().out


def test_the_root_defaults_to_the_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without ``--root``, files are read relative to the current directory."""
    _plant(tmp_path, "docs/a.md", "A — dash.\n")
    monkeypatch.chdir(tmp_path)
    assert main(["check", "docs/a.md"]) == 1
    assert "docs/a.md:1" in capsys.readouterr().out


def test_the_root_config_decides_what_is_read(tmp_path: Path) -> None:
    """A Python file is checked only once the root's config turns Python on."""
    _plant(tmp_path, "src/a.py", "# This is truly odd.\nx = 1\n")
    assert main(["check", "--root", str(tmp_path), "src/a.py"]) == 0
    _plant(tmp_path, ".claude/claude-kit.json", json.dumps({"tells": {"readers": ["python"]}}))
    assert main(["check", "--root", str(tmp_path), "src/a.py"]) == 1


def test_hook_answers_a_payload_on_stdin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``hook`` reads the payload on stdin and prints the hook's JSON answer."""
    path = _plant(tmp_path, "notes.md", "This is truly odd.\n")
    payload: dict[str, object] = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": "This is truly odd.\n"},
        "tool_response": {
            "type": "create",
            "filePath": str(path),
            "content": "This is truly odd.\n",
            "originalFile": None,
            "structuredPatch": [],
        },
        "cwd": str(tmp_path),
        "session_id": "case",
    }
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert main(["hook"]) == 0
    answer = json.loads(capsys.readouterr().out)
    assert "notes.md:1  intensifier" in answer["hookSpecificOutput"]["additionalContext"]


def test_hook_on_garbage_prints_nothing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A payload that is not JSON prints nothing and still exits 0."""
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert main(["hook"]) == 0
    assert capsys.readouterr().out == ""
