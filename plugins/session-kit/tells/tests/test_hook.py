"""The PostToolUse hook: which lines an edit wrote, and what it says about their banned tells."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from session_tells.find import Hit
from session_tells.hook import edited, message, respond

if TYPE_CHECKING:
    from pathlib import Path


def _edit(path: Path, patch: list[dict[str, Any]] | None, new: str = "") -> dict[str, Any]:
    response: dict[str, Any] = {
        "filePath": str(path),
        "oldString": "old",
        "newString": new,
        "originalFile": "",
        "replaceAll": False,
        "userModified": False,
    }
    if patch is not None:
        response["structuredPatch"] = patch
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(path), "old_string": "old", "new_string": new},
        "tool_response": response,
        "cwd": str(path.parent),
        "session_id": "case",
    }


def _write(
    path: Path, content: str, kind: str, patch: list[dict[str, Any]] | None
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "type": kind,
        "filePath": str(path),
        "content": content,
        "originalFile": None if kind == "create" else "",
    }
    if patch is not None:
        response["structuredPatch"] = patch
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": content},
        "tool_response": response,
        "cwd": str(path.parent),
        "session_id": "case",
    }


def _bash(files: list[dict[str, Any]] | None) -> dict[str, Any]:
    response: dict[str, Any] = {
        "stdout": "",
        "stderr": "",
        "interrupted": False,
        "isImage": False,
        "noOutputExpected": False,
    }
    if files is not None:
        response["bashEditDiff"] = {"files": files}
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "sed -i s/a/b/ x", "description": "edit"},
        "tool_response": response,
        "cwd": "/",
        "session_id": "case",
    }


def _hunk(new_start: int, lines: list[str]) -> dict[str, Any]:
    old = sum(1 for line in lines if not line.startswith("+"))
    new = sum(1 for line in lines if not line.startswith("-"))
    return {
        "oldStart": new_start,
        "oldLines": old,
        "newStart": new_start,
        "newLines": new,
        "lines": lines,
    }


# Which lines an edit wrote.


def test_an_edit_writes_its_added_lines_counted_past_context_and_over_removals(
    tmp_path: Path,
) -> None:
    """Added lines are placed from ``newStart``, counting context and skipping removed lines."""
    path = tmp_path / "a.md"
    patch = [
        _hunk(10, [" kept", "-gone", "+first", "+second", " kept"]),
        _hunk(30, ["-gone", "-gone too", " kept", "+third"]),
    ]
    assert edited(_edit(path, patch)) == {str(path): frozenset({11, 12, 31})}


def test_a_write_that_created_the_file_is_the_whole_file(tmp_path: Path) -> None:
    """A created file, with no patch or an empty one, is ``None``: every line was written."""
    path = tmp_path / "a.md"
    assert edited(_write(path, "x\n", "create", None)) == {str(path): None}
    assert edited(_write(path, "x\n", "create", [])) == {str(path): None}


def test_a_write_that_updated_the_file_is_its_patch(tmp_path: Path) -> None:
    """An update is placed by its patch like an Edit."""
    path = tmp_path / "a.md"
    patch = [_hunk(1, ["-old", "+new", " same"])]
    assert edited(_write(path, "new\nsame\n", "update", patch)) == {str(path): frozenset({1})}


def test_an_edit_without_a_patch_is_placed_by_its_new_string(tmp_path: Path) -> None:
    """With no patch, the new string is found in the file to name its lines."""
    path = tmp_path / "a.md"
    path.write_text("one\ntwo\nthree\nfour\nfive\n", encoding="utf-8")
    assert edited(_edit(path, None, new="three\nfour")) == {str(path): frozenset({3, 4})}


def test_an_edit_that_cannot_be_placed_is_the_whole_file(tmp_path: Path) -> None:
    """A new string the file does not hold leaves the edit unplaced: ``None``."""
    path = tmp_path / "a.md"
    path.write_text("one\ntwo\n", encoding="utf-8")
    assert edited(_edit(path, None, new="absent")) == {str(path): None}


def test_a_bash_call_names_each_file_it_edited(tmp_path: Path) -> None:
    """Each file in ``bashEditDiff`` comes back with the lines its hunks added."""
    first, second = tmp_path / "a.md", tmp_path / "b.md"
    files = [
        {"filePath": str(first), "hunks": [_hunk(4, [" kept", "+new"])]},
        {"filePath": str(second), "hunks": [_hunk(1, ["+top", " kept"])]},
    ]
    assert edited(_bash(files)) == {
        str(first): frozenset({5}),
        str(second): frozenset({1}),
    }


def test_nothing_edited_is_empty() -> None:
    """A Bash call that edited nothing, and any other tool, give ``{}``."""
    assert edited(_bash(None)) == {}
    read = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Read",
        "tool_input": {"file_path": "/x/a.md"},
        "tool_response": {"type": "text"},
        "cwd": "/x",
        "session_id": "case",
    }
    assert edited(read) == {}


# What the session is told.


def _hit(line: int, rule: str, found: str) -> Hit:
    return Hit("docs/a.md", line, rule, found, "doc")


def test_the_hits_on_written_lines_are_listed_and_the_rest_counted() -> None:
    """Hits on written lines appear as ``<rel>:<line>  <rule>``; the others close in one line."""
    found = [_hit(3, "dash", "—"), _hit(5, "intensifier", "truly"), _hit(9, "dash", "—")]
    said = message("docs/a.md", found, frozenset({5}))
    assert said is not None
    lines = said.strip().splitlines()
    assert any(line.startswith("docs/a.md:5  intensifier") for line in lines)
    assert not any(line.startswith(("docs/a.md:3 ", "docs/a.md:9 ")) for line in lines)
    assert "session-tells show docs/a.md" in lines[-1]


def test_every_line_counts_when_the_whole_file_was_written() -> None:
    """With ``lines`` ``None`` every hit is listed."""
    found = [_hit(3, "dash", "—"), _hit(9, "filler-phrase", "in order to")]
    said = message("docs/a.md", found, None)
    assert said is not None
    assert "docs/a.md:3  dash" in said
    assert "docs/a.md:9  filler-phrase" in said


def test_nothing_on_a_written_line_is_nothing_to_say() -> None:
    """Hits elsewhere in the file alone say nothing, and so does a file with none."""
    assert message("docs/a.md", [_hit(3, "dash", "—")], frozenset({4})) is None
    assert message("docs/a.md", [], None) is None


# The whole answer.

PAGE = "# Notes\n\nPlain words here.\n\nThis is truly odd.\n\nAnother — dash, left from before.\n"


def _context(answer: dict[str, Any] | None) -> str:
    assert answer is not None
    output = answer["hookSpecificOutput"]
    assert output["hookEventName"] == "PostToolUse"
    return output["additionalContext"]


def test_an_edit_is_told_its_own_tells_and_pointed_at_the_rest(tmp_path: Path) -> None:
    """The banned tell on the edited line is listed; the one elsewhere is left to ``show``."""
    path = tmp_path / "docs" / "notes.md"
    path.parent.mkdir()
    path.write_text(PAGE, encoding="utf-8")
    patch = [_hunk(3, [" Plain words here.", " ", "-This was odd.", "+This is truly odd.", " "])]
    context = _context(respond(_edit(path, patch, new="This is truly odd."), tmp_path))
    assert "docs/notes.md:5  intensifier" in context
    assert "docs/notes.md:7 " not in context
    assert "session-tells show docs/notes.md" in context


def test_a_created_file_is_read_whole(tmp_path: Path) -> None:
    """A Write that created a file lists every banned tell in it."""
    path = tmp_path / "notes.md"
    content = "We stop in order to wait.\n\nA — dash.\n"
    path.write_text(content, encoding="utf-8")
    context = _context(respond(_write(path, content, "create", None), tmp_path))
    assert "notes.md:1  filler-phrase" in context
    assert "notes.md:3  dash" in context


def test_a_bash_edit_is_read_by_the_config_readers(tmp_path: Path) -> None:
    """A Python file a Bash call edited is read when the project turns Python on."""
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "claude-kit.json").write_text(
        json.dumps({"tells": {"readers": ["python"]}}), encoding="utf-8"
    )
    path = tmp_path / "src" / "a.py"
    path.parent.mkdir()
    path.write_text("x = 1\n# Done in order to stop.\ny = 2\n", encoding="utf-8")
    files = [{"filePath": str(path), "hunks": [_hunk(1, [" x = 1", "+# Done in order to stop."])]}]
    context = _context(respond(_bash(files), tmp_path))
    assert "src/a.py:2  filler-phrase" in context


def test_rationed_tells_are_not_mentioned(tmp_path: Path) -> None:
    """A semicolon or a ``rather than`` on the edited line says nothing."""
    path = tmp_path / "notes.md"
    content = "Stop; wait.\n\n- Read it rather than guess.\n"
    path.write_text(content, encoding="utf-8")
    assert respond(_write(path, content, "create", None), tmp_path) is None


def test_files_it_does_not_read_say_nothing(tmp_path: Path) -> None:
    """A file outside the project and a file no reader reads both say nothing."""
    outside = tmp_path / "elsewhere" / "notes.md"
    outside.parent.mkdir()
    outside.write_text("This is truly odd.\n", encoding="utf-8")
    root = tmp_path / "project"
    root.mkdir()
    assert respond(_write(outside, "This is truly odd.\n", "create", None), root) is None
    text = root / "notes.txt"
    text.write_text("This is truly odd.\n", encoding="utf-8")
    assert respond(_write(text, "This is truly odd.\n", "create", None), root) is None
    code = root / "a.py"
    code.write_text("# This is truly odd.\n", encoding="utf-8")
    assert respond(_write(code, "# This is truly odd.\n", "create", None), root) is None


def test_a_broken_config_is_said_in_one_line(tmp_path: Path) -> None:
    """A config the project got wrong reaches the session as one line."""
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "claude-kit.json").write_text("{not json", encoding="utf-8")
    path = tmp_path / "notes.md"
    path.write_text("This is truly odd.\n", encoding="utf-8")
    context = _context(respond(_write(path, "This is truly odd.\n", "create", None), tmp_path))
    assert len(context.strip().splitlines()) == 1


def test_an_unexpected_payload_says_nothing(tmp_path: Path) -> None:
    """A payload missing what the hook reads gives ``None`` without raising."""
    assert respond({"hook_event_name": "PostToolUse", "tool_name": "Edit"}, tmp_path) is None
