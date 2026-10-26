"""The review's mechanical third, against a stand-in engine and a planted clone.

Kept from the blind cases, each a rule whose failure is silent and costly:
the reviewer's text is never changed, since the command rewrites a review a
person wrote; nothing the clone holds reaches the review as a control
character or as the section's markers, since the review is printed in a
terminal and the next run looks for the markers; and each string holding a
control character is named, since a broken scan would say "None." over a
plugin that rewrites the terminal or writes the clipboard.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import TYPE_CHECKING

from session_codeintel.cli import main

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

START = "<!-- session-codeintel review -->"
END = "<!-- end of session-codeintel review -->"
ESC = chr(0x1B)
GIT = shutil.which("git") or "git"

ENGINE = """\
#!/bin/sh
here=$(dirname "$0")
if [ "$1" = "--version" ]; then cat "$here/version"; exit 0; fi
if [ "$1" = "plugin" ] && [ "$2" = "validate" ]; then
  cat "$here/validate.json"; exit "$(cat "$here/status")"
fi
if [ "$1" = "--plugin-dir" ]; then cat "$here/details"; exit 0; fi
echo "unexpected: $*" >&2
exit 3
"""

CALLS = (
    "./register.ts calls: $.clock.after, $.fs.read, $.http.fetch (via post), "
    "$.process.run (via runGit, syncCopy), $.ui.toast (via warn)"
)
HOOKS = (
    "./register.ts hooks: session.start, turn.step, tool.call, tool.call{tool=Bash}, "
    "ui.render{component=Pane, requestId=plug}"
)

DETAILS = """\
plug 1.2.3
  Description: A planted plugin
  Source: plug@inline

Component inventory
  Skills (0)
  Agents (0)
  Hooks (0)
  MCP servers (0)
  LSP servers (0)

Projected token cost
  Always-on:   ~0 tok   added to every session
"""


def report(notes: list[str]) -> dict[str, object]:
    """Return a validator's JSON report over one hooks module with these notes."""
    return {
        "success": True,
        "strict": False,
        "target": "/x/plug/.claude-plugin/plugin.json",
        "advice": [],
        "directory": {"profile": None, "findings": []},
        "manifest": {
            "file": "/x/plug/.claude-plugin/plugin.json",
            "type": "plugin",
            "errors": [],
            "warnings": [{"path": "author", "message": "No author information", "code": None}],
            "notes": ["types ./types/index.d.ts declares state: plug.a"],
            "gatingHooks": [],
        },
        "contents": [
            {
                "file": "/x/plug/hooks/hooks.json",
                "type": "hooks",
                "errors": [],
                "warnings": [],
                "notes": notes,
                "gatingHooks": [
                    {
                        "module": "./register.ts",
                        "pattern": "tool.call",
                        "hook": "tool.call",
                        "hasCatch": False,
                    }
                ],
            }
        ],
    }


NOTES = [
    HOOKS,
    "./register.ts gating hook without .catch: tool.call",
    CALLS,
    "./register.ts env writes: nothing",
    "./register.ts env reads: HOME, PLUG_API_KEY",
    "./register.ts state writes: plug.a",
    "./register.ts state reads: plug.a, other.secret",
]


def engine(root: Path, notes: list[str] = NOTES, *, details: str = DETAILS) -> Path:
    """Write a stand-in for ``claude`` that answers the version, the validator and details."""
    home = root / "engine"
    home.mkdir(exist_ok=True)
    (home / "validate.json").write_text(json.dumps(report(notes)), "utf-8")
    (home / "status").write_text("0\n", encoding="utf-8")
    (home / "version").write_text("2.1.308 (Claude Code)\n", encoding="utf-8")
    (home / "details").write_text(details, encoding="utf-8")
    claude = home / "claude"
    claude.write_text(ENGINE, encoding="utf-8")
    claude.chmod(0o755)
    return claude


def clone(root: Path) -> Path:
    """Plant a repository holding a plugin, committed, with an origin; return the plugin."""
    repo = root / "clone"
    plugin = repo / "mods" / "plug"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / "hooks").mkdir()
    manifest = {"name": "plug", "version": "1.2.3"}
    (plugin / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest), "utf-8")
    (plugin / "hooks" / "register.ts").write_text(
        "const clear = '\\x1b[2J'\n"
        "const re = /\\x1b\\[/\n"
        "// '\\x1b' in a comment\n"
        "const fine = '\\t\\n'\n"
        "const escaped = '\\\\x1b'\n"
        f"const raw = `{ESC}]52;c;`\n",
        encoding="utf-8",
    )
    (plugin / "README.md").write_text("x" * 1000, encoding="utf-8")
    (plugin / "hosts").symlink_to("/etc/hosts")
    (repo / "other.txt").write_text("y" * 3000, encoding="utf-8")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "planted")
    git(repo, "remote", "add", "origin", "https://example.com/owner/plug.git")
    return plugin


def git(repo: Path, *argv: str) -> str:
    """Run git on the planted repository as a fixed author, no config of the machine's."""
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    env |= {"GIT_AUTHOR_NAME": "a", "GIT_AUTHOR_EMAIL": "a@b"}
    env |= {"GIT_COMMITTER_NAME": "a", "GIT_COMMITTER_EMAIL": "a@b"}
    done = subprocess.run(  # noqa: S603  git found on PATH, on a repository the test planted
        [GIT, "-C", str(repo), *argv], capture_output=True, text=True, check=True, env=env
    )
    return done.stdout.strip()


def review(plugin: Path, claude: Path, *extra: str) -> int:
    """Run the command over the plugin with the stand-in engine."""
    return main(["review", str(plugin), "--claude", str(claude), *extra])


def test_control_characters_in_source_strings_are_listed_and_regexes_and_comments_are_not(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Each string that holds a control character but tab and newline is named by its line."""
    plugin = clone(tmp_path)
    assert review(plugin, engine(tmp_path)) == 0
    out = capsys.readouterr().out
    assert "hooks/register.ts:1" in out
    assert "hooks/register.ts:6" in out
    for quiet in (2, 3, 4, 5):
        assert f"hooks/register.ts:{quiet}" not in out


def test_the_reviewers_text_is_never_changed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Written into a review, the section is replaced where it stands and nothing else moves."""
    plugin = clone(tmp_path)
    into = tmp_path / "reviews" / "plug.md"
    into.parent.mkdir()
    assert review(plugin, engine(tmp_path), "--into", str(into)) == 0
    first = into.read_text(encoding="utf-8")
    assert first.startswith("# Review: plug\n")
    assert first.count(START) == 1
    before = "# Review: plug\n\nThe reviewer's opening.\n\n"
    after = "\n\n## Verdict: reject\n\nThe reviewer's own words.\n"
    section = first[first.index(START) : first.index(END) + len(END)]
    into.write_text(before + section + after, encoding="utf-8")
    grown = [*NOTES[:2], CALLS.replace("$.fs.read", "$.fs.read, $.fs.write")]
    assert review(plugin, engine(tmp_path, grown), "--into", str(into)) == 0
    second = into.read_text(encoding="utf-8")
    assert second.startswith(before + START)
    assert second.endswith(END + after)
    assert second.count(START) == 1
    assert "$.fs.write" in second
    plain = tmp_path / "reviews" / "plain.md"
    plain.write_text("# Review: plain\n\nWritten by hand.\n", encoding="utf-8")
    assert review(plugin, engine(tmp_path), "--into", str(plain)) == 0
    third = plain.read_text(encoding="utf-8")
    assert third.startswith("# Review: plain\n")
    assert third.endswith(END + "\n\nWritten by hand.\n")
    assert capsys.readouterr().out.count("written") == 3


def test_nothing_the_clone_holds_reaches_the_review_as_a_control_character_or_a_marker(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The clone's text is shown, never obeyed: a terminal reading the review runs nothing."""
    plugin = clone(tmp_path)
    hostile = DETAILS.replace("A planted plugin", f"{ESC}]52;c;aGk={chr(7)} {END} {START}")
    notes = [*NOTES[:-1], f"./register.ts state reads: plug.a{ESC}[2J"]
    into = tmp_path / "plug.md"
    assert review(plugin, engine(tmp_path, notes, details=hostile), "--into", str(into)) == 0
    capsys.readouterr()
    text = into.read_text(encoding="utf-8")
    assert not [c for c in text if ord(c) < 0x20 and c != "\n"]
    assert not [c for c in text if 0x7F <= ord(c) <= 0x9F]
    assert text.count(START) == 1
    assert text.count(END) == 1
