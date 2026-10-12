"""The readers past Markdown, the project's own command, and the door that picks among them."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

import pytest

from session_tells.config import Command, Config
from session_tells.readers import read, reader_for
from session_tells.readers.command import CommandError, run
from session_tells.readers.rust import rust
from session_tells.readers.typescript import typescript

if TYPE_CHECKING:
    from pathlib import Path

    from session_tells.units import Unit


def _words(unit: Unit) -> str:
    return " ".join(text.strip() for _, text in unit.pieces if text.strip())


def _lines(unit: Unit) -> list[int]:
    return [line for line, text in unit.pieces if text.strip()]


# TypeScript.


def test_typescript_joins_a_run_of_line_comments() -> None:
    """Consecutive ``//`` lines, each alone on its line, are one comment unit."""
    source = "const a = 1;\n// First line of the note\n// and its second line.\nconst b = 2;\n"
    (unit,) = typescript("src/a.ts", source)
    assert unit.path == "src/a.ts"
    assert unit.text == "comment"
    assert _lines(unit) == [2, 3]
    assert _words(unit) == "First line of the note and its second line."


def test_typescript_strips_a_block_comment_of_its_markers() -> None:
    """A ``/** */`` block is one unit, without its opener, closer or leading stars."""
    source = "/**\n * Parses the header.\n * Returns the rest.\n */\nexport function f() {}\n"
    (unit,) = typescript("src/a.ts", source)
    assert _words(unit) == "Parses the header. Returns the rest."
    assert _lines(unit) == [2, 3]
    assert not any("*" in text for _, text in unit.pieces)


def test_typescript_reads_a_trailing_comment_alone() -> None:
    """A comment after code is its own unit, not joined to the comments around it."""
    source = "// Above the code.\nconst a = 1; // Beside the code.\n// Below the code.\n"
    units = typescript("src/a.ts", source)
    assert [_words(unit) for unit in units] == [
        "Above the code.",
        "Beside the code.",
        "Below the code.",
    ]


def test_typescript_leaves_out_pragmas_strings_and_shebangs() -> None:
    """Lint and type pragmas, a shebang, a triple-slash reference and strings carry no prose."""
    source = (
        "#!/usr/bin/env node\n"
        '/// <reference types="vite/client" />\n'
        "const a = 1;\n"
        "// eslint-disable-next-line no-console\n"
        "const b = 2;\n"
        "// @ts-expect-error the types lag behind\n"
        "const c = 3;\n"
        "// biome-ignore lint/style: the order is the protocol's\n"
        "const d = 4;\n"
        "// #region helpers\n"
        "const s = 'This is truly the way, in order to win.';\n"
        "// #endregion\n"
    )
    assert typescript("src/a.ts", source) == []


def test_typescript_reads_inline_code_as_a_word() -> None:
    """Backticked code reads as the word ``code``."""
    (unit,) = typescript("src/a.ts", "// Call `parse()` before the rest.\nconst a = 1;\n")
    assert _words(unit) == "Call code before the rest."


def test_typescript_parses_tsx() -> None:
    """A comment inside JSX in a ``.tsx`` file is read."""
    source = (
        "export function Page() {\n"
        "  return (\n"
        "    <div>\n"
        "      {/* The empty state goes here. */}\n"
        "    </div>\n"
        "  );\n"
        "}\n"
    )
    units = typescript("src/Page.tsx", source)
    assert [_words(unit) for unit in units] == ["The empty state goes here."]
    assert _lines(units[0]) == [4]


def test_typescript_reads_what_it_can_of_a_broken_file() -> None:
    """A file that does not parse whole still gives the comments tree-sitter found."""
    source = "// Before the break.\nconst = = ;\nfunction (\n"
    assert "Before the break." in [_words(unit) for unit in typescript("src/a.ts", source)]


# Rust.


def test_rust_keeps_comment_kinds_apart() -> None:
    """A ``///`` run and a ``//`` run on adjacent lines are two units, markers left out."""
    source = (
        "/// Opens the store.\n"
        "/// Fails when locked.\n"
        "// A note for the maintainer.\n"
        "fn open() {}\n"
    )
    units = rust("src/lib.rs", source)
    assert [_words(unit) for unit in units] == [
        "Opens the store. Fails when locked.",
        "A note for the maintainer.",
    ]
    assert [_lines(unit) for unit in units] == [[1, 2], [3]]
    assert all(unit.text == "comment" for unit in units)


def test_rust_strips_a_block_comment_of_its_markers() -> None:
    """A ``/*! */`` block is one unit, without its markers or leading stars."""
    source = "/*!\n * The crate's entry.\n * It holds the store.\n */\nfn main() {}\n"
    (unit,) = rust("src/main.rs", source)
    assert _words(unit) == "The crate's entry. It holds the store."
    assert not any("*" in text or "!" in text for _, text in unit.pieces)


def test_rust_leaves_out_fenced_code_in_a_doc_comment() -> None:
    """The lines inside a fenced block in a doc comment are not prose."""
    source = (
        "/// Adds two numbers.\n"
        "///\n"
        "/// ```\n"
        "/// let truly = add(1, 2); // in order to test\n"
        "/// ```\n"
        "fn add(a: i32, b: i32) -> i32 { a + b }\n"
    )
    (unit,) = rust("src/lib.rs", source)
    assert _lines(unit) == [1]
    assert "truly" not in _words(unit)


def test_rust_reads_trailing_comments_alone_and_not_strings() -> None:
    """A comment after code is its own unit, and a string literal is not read."""
    source = (
        'fn f() {\n    // Above.\n    let s = "This is truly odd"; // Beside.\n    // Below.\n}\n'
    )
    units = rust("src/lib.rs", source)
    assert [_words(unit) for unit in units] == ["Above.", "Beside.", "Below."]


def test_rust_reads_inline_code_as_a_word() -> None:
    """Backticked code reads as the word ``code``."""
    (unit,) = rust("src/lib.rs", "/// Returns `None` when empty.\nfn f() {}\n")
    assert _words(unit) == "Returns code when empty."


# A project's own command.


def _reader_script(folder: Path, body: str) -> Path:
    """Write a command that turns each file it is handed into one ``copy`` unit."""
    script = folder / "reader.py"
    script.write_text(
        f"import json, os, sys\nfiles = sys.argv[1:]\n{body}\n",
        encoding="utf-8",
    )
    return script


ECHO = (
    "units = [{'path': f, 'text': 'copy', 'pieces': [[1, open(f).read().strip()]]}"
    " for f in files]\n"
    "print(json.dumps({'units': units}))"
)


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "web" / "src").mkdir(parents=True)
    return root


def _command(script: Path) -> Command:
    return Command("web/", (sys.executable, str(script)), frozenset({".ts"}))


def test_a_command_runs_from_its_directory_and_paths_come_back_from_the_root(
    tmp_path: Path,
) -> None:
    """The command opens its files relative to ``under``; units return root-relative, ``text``."""
    root = _project(tmp_path)
    (root / "web" / "src" / "app.ts").write_text("Save the draft.", encoding="utf-8")
    script = _reader_script(tmp_path, ECHO)
    (unit,) = run(root, _command(script), ["web/src/app.ts"])
    assert unit.path == "web/src/app.ts"
    assert unit.text == "copy"
    assert unit.role == "text"
    assert unit.pieces == ((1, "Save the draft."),)


def test_a_command_unit_without_words_is_left_out(tmp_path: Path) -> None:
    """A unit holding only a dash or a number is dropped, as every reader drops it."""
    root = _project(tmp_path)
    (root / "web" / "src" / "a.ts").write_text("42", encoding="utf-8")
    (root / "web" / "src" / "b.ts").write_text("Open the file.", encoding="utf-8")
    script = _reader_script(tmp_path, ECHO)
    units = run(root, _command(script), ["web/src/a.ts", "web/src/b.ts"])
    assert [unit.path for unit in units] == ["web/src/b.ts"]


def test_a_command_that_fails_says_its_stderr_and_not_its_files(tmp_path: Path) -> None:
    """A non-zero exit raises CommandError naming the stderr, never the files."""
    root = _project(tmp_path)
    (root / "web" / "src" / "secret-name.ts").write_text("x", encoding="utf-8")
    script = _reader_script(tmp_path, "sys.stderr.write('parser broke here')\nsys.exit(3)")
    with pytest.raises(CommandError) as raised:
        run(root, _command(script), ["web/src/secret-name.ts"])
    assert "parser broke here" in str(raised.value)
    assert "secret-name" not in str(raised.value)


def test_a_command_that_prints_something_else_is_an_error(tmp_path: Path) -> None:
    """Output that is not the units object raises CommandError."""
    root = _project(tmp_path)
    (root / "web" / "src" / "a.ts").write_text("x", encoding="utf-8")
    script = _reader_script(tmp_path, "print('hello')")
    with pytest.raises(CommandError):
        run(root, _command(script), ["web/src/a.ts"])


def test_a_command_that_cannot_start_is_an_error(tmp_path: Path) -> None:
    """A program that does not exist raises CommandError."""
    root = _project(tmp_path)
    (root / "web" / "src" / "a.ts").write_text("x", encoding="utf-8")
    command = Command("web/", (str(tmp_path / "no-such-program"),), frozenset({".ts"}))
    with pytest.raises(CommandError):
        run(root, command, ["web/src/a.ts"])


# Picking the reader.


def test_markdown_is_always_read_and_the_rest_only_when_turned_on() -> None:
    """Markdown needs no config; Python, TypeScript and Rust wait for theirs."""
    default = Config()
    assert reader_for("docs/a.md", default) == "markdown"
    assert reader_for("docs/a.markdown", default) == "markdown"
    assert reader_for("src/a.py", default) is None
    assert reader_for("src/a.ts", default) is None
    assert reader_for("src/a.rs", default) is None
    assert reader_for("notes.txt", default) is None
    on = Config(readers=frozenset({"python", "typescript", "rust"}))
    assert reader_for("src/a.pyi", on) == "python"
    assert reader_for("src/a.tsx", on) == "typescript"
    assert reader_for("src/a.mjs", on) == "typescript"
    assert reader_for("src/a.rs", on) == "rust"


def test_a_command_wins_under_its_prefix_for_its_suffixes() -> None:
    """The command takes its own files; the same suffix elsewhere and other suffixes are not its."""
    config = Config(
        readers=frozenset({"typescript"}),
        commands=(Command("web/", ("prose",), frozenset({".ts", ".md"})),),
    )
    assert reader_for("web/src/a.ts", config) == "command"
    assert reader_for("web/README.md", config) == "command"
    assert reader_for("api/a.ts", config) == "typescript"
    assert reader_for("web/src/a.tsx", config) == "typescript"


def test_read_keeps_the_given_order_and_skips_what_it_cannot_read(tmp_path: Path) -> None:
    """Files read in the order given; a missing file and an unread suffix are skipped."""
    (tmp_path / "b.md").write_text("Second file here.\n", encoding="utf-8")
    (tmp_path / "a.md").write_text("First file here.\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("Plain words.\n", encoding="utf-8")
    units = read(tmp_path, ["b.md", "missing.md", "notes.txt", "a.md"], Config())
    assert [unit.path for unit in units] == ["b.md", "a.md"]


def test_read_marks_the_guide(tmp_path: Path) -> None:
    """Markdown under a guide prefix reads as ``guide``; elsewhere as ``doc``."""
    (tmp_path / "docs" / "guide").mkdir(parents=True)
    (tmp_path / "docs" / "guide" / "start.md").write_text("Open the app.\n", encoding="utf-8")
    (tmp_path / "docs" / "plan.md").write_text("Build the app.\n", encoding="utf-8")
    config = Config(guide=("docs/guide/",))
    units = read(tmp_path, ["docs/guide/start.md", "docs/plan.md"], config)
    assert [(unit.path, unit.text) for unit in units] == [
        ("docs/guide/start.md", "guide"),
        ("docs/plan.md", "doc"),
    ]


def test_read_reaches_the_readers_the_config_turns_on(tmp_path: Path) -> None:
    """A Python file is read once the config turns Python on, and not before."""
    (tmp_path / "a.py").write_text("# Opens the store.\nx = 1\n", encoding="utf-8")
    assert read(tmp_path, ["a.py"], Config()) == []
    (unit,) = read(tmp_path, ["a.py"], Config(readers=frozenset({"python"})))
    assert unit.text == "comment"


def test_read_hands_one_command_its_files_in_one_run(tmp_path: Path) -> None:
    """Every file of one command goes to it in a single run, and its units come back."""
    root = _project(tmp_path)
    (root / "web" / "src" / "a.ts").write_text("Save it.", encoding="utf-8")
    (root / "web" / "src" / "b.ts").write_text("Close it.", encoding="utf-8")
    runs = tmp_path / "runs.log"
    script = _reader_script(
        tmp_path, f"open({json.dumps(str(runs))}, 'a').write(' '.join(files) + '\\n')\n{ECHO}"
    )
    config = Config(commands=(_command(script),))
    units = read(root, ["web/src/a.ts", "web/src/b.ts"], config)
    assert [unit.path for unit in units] == ["web/src/a.ts", "web/src/b.ts"]
    assert len(runs.read_text(encoding="utf-8").splitlines()) == 1
