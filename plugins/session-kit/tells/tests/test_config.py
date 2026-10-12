"""What a project's ``.claude/claude-kit.json`` says about its prose, and what it refuses."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from session_tells import ruleset
from session_tells.config import Command, Config, ConfigError, load
from session_tells.find import hits
from session_tells.units import Unit

if TYPE_CHECKING:
    from pathlib import Path


def _write(root: Path, document: object) -> None:
    folder = root / ".claude"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "claude-kit.json").write_text(json.dumps(document), encoding="utf-8")


def _comment(words: str) -> Unit:
    return Unit("src/a.py", "comment", "text", ((1, words),))


def test_a_project_without_the_file_reads_markdown_alone(tmp_path: Path) -> None:
    """A missing config file is the default: no readers past Markdown, no guide, English."""
    assert load(tmp_path) == Config()


def test_a_file_without_the_tells_key_is_the_default(tmp_path: Path) -> None:
    """A config file that holds other keys and no ``tells`` reads as the default."""
    _write(tmp_path, {"test_commands": ["scripts/test"]})
    assert load(tmp_path) == Config()


def test_every_key_is_read(tmp_path: Path) -> None:
    """Readers, guide, languages, history codes and commands all come through, typed."""
    _write(
        tmp_path,
        {
            "tells": {
                "readers": ["python", "rust"],
                "guide": ["docs/guide/"],
                "languages": {"es-419": "es", "pt-BR": "pt"},
                "history_codes": r"\bJIRA-\d+\b",
                "commands": [
                    {"under": "web/", "run": ["node", "prose.ts"], "suffixes": [".ts", ".tsx"]}
                ],
            }
        },
    )
    config = load(tmp_path)
    assert config.readers == frozenset({"python", "rust"})
    assert config.guide == ("docs/guide/",)
    assert config.languages == {"es-419": "es", "pt-BR": "pt"}
    assert config.history_codes == r"\bJIRA-\d+\b"
    assert config.commands == (Command("web/", ("node", "prose.ts"), frozenset({".ts", ".tsx"})),)


def test_an_under_without_its_slash_is_given_one(tmp_path: Path) -> None:
    """A command's ``under`` written without the trailing slash is read with one."""
    _write(
        tmp_path,
        {"tells": {"commands": [{"under": "web", "run": ["prose"], "suffixes": [".ts"]}]}},
    )
    assert load(tmp_path).commands[0].under == "web/"


@pytest.mark.parametrize(
    "raw",
    [
        "{not json",
        json.dumps({"tells": {"readers": ["go"]}}),
        json.dumps({"tells": {"languages": {"fr": "fr"}}}),
        json.dumps({"tells": {"history_codes": "(unclosed"}}),
        json.dumps({"tells": {"readers": "python"}}),
        json.dumps({"tells": {"commands": [{"under": "web/", "run": "prose", "suffixes": []}]}}),
    ],
    ids=[
        "not-json",
        "unknown-reader",
        "unknown-language",
        "bad-regex",
        "readers-shape",
        "run-shape",
    ],
)
def test_a_config_it_cannot_use_is_said(tmp_path: Path, raw: str) -> None:
    """A typo in the config raises ConfigError rather than reading as the default."""
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "claude-kit.json").write_text(raw, encoding="utf-8")
    with pytest.raises(ConfigError):
        load(tmp_path)


def test_the_default_reads_with_every_table() -> None:
    """Without history codes, a project reads with the English and the translated tables."""
    assert sorted(rule.name for rule in Config().rules()) == sorted(
        rule.name for rule in ruleset.RULES
    )


def test_history_codes_reach_the_rules() -> None:
    """A project's history codes are found in a comment; without them the same code is not."""
    unit = _comment("Fixed under JIRA-412 last week.")
    with_codes = Config(history_codes=r"\bJIRA-\d+\b").rules()
    assert [hit.rule for hit in hits([unit], with_codes)] == ["history-code"]
    assert hits([unit], Config().rules()) == []
