r"""What a project says about its prose, in the ``tells`` key of ``.claude/claude-kit.json``.

Every key is optional, and a project without the file reads Markdown alone::

    {
      "tells": {
        "readers": ["python", "typescript", "rust"],
        "guide": ["docs/guide/"],
        "languages": {"es-419": "es", "pt-BR": "pt"},
        "history_codes": "\\bJIRA-\\d+\\b",
        "commands": [
          {"under": "web/", "run": ["node", "scripts/prose.ts"], "suffixes": [".ts", ".tsx"]}
        ]
      }
    }

``readers`` turns on the readers past Markdown, which is always read. ``guide``
names the path prefixes whose Markdown is a guide a product's users read, where
the guide's own rules apply. ``languages`` maps a directory name, anywhere in a
path, to the language of the files under it; everything else is English.
``history_codes`` is a regular expression for the codes a project's records use,
which read as history in a comment (:func:`session_tells.rules.with_history_codes`).
``commands`` hands the files under a prefix, with those suffixes, to a command of
the project's own (:mod:`session_tells.readers.command`), which wins over a reader.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast, get_args

from session_tells import ruleset
from session_tells.rules import Language, with_history_codes

if TYPE_CHECKING:
    from pathlib import Path

    from session_tells.rules import Rule

CONFIG_FILE = ".claude/claude-kit.json"
READERS: frozenset[str] = frozenset({"python", "typescript", "rust"})
"""The readers a project may turn on. Markdown is always on and is not named."""


class ConfigError(Exception):
    """The config file exists and says something this module cannot use; the message names it."""


@dataclass(frozen=True)
class Command:
    """A project's own reader: the files under a prefix, with these suffixes, go to ``run``."""

    under: str
    """A path prefix relative to the project root, ending in ``/``. The command runs
    from that directory and is handed paths relative to it."""
    run: tuple[str, ...]
    suffixes: frozenset[str]


@dataclass(frozen=True)
class Config:
    """A project's prose settings. The default is Markdown alone, in English, with no guide."""

    readers: frozenset[str] = frozenset()
    guide: tuple[str, ...] = ()
    languages: dict[str, Language] = field(default_factory=dict[str, "Language"])
    history_codes: str | None = None
    commands: tuple[Command, ...] = ()

    def rules(self) -> tuple[Rule, ...]:
        """Every rule this project reads its prose with: the tables, its history codes added."""
        if self.history_codes is None:
            return ruleset.RULES
        return with_history_codes(ruleset.RULES, self.history_codes)


def load(root: Path) -> Config:
    """Read the ``tells`` key of ``root/.claude/claude-kit.json``.

    A missing file, or a file without the key, is the default :class:`Config`.
    A file that is not JSON, a reader that is not in :data:`READERS`, a language
    that is not ``en``, ``es`` or ``pt``, a ``history_codes`` that does not
    compile, or a key of the wrong shape raises :class:`ConfigError`, so a typo
    is said rather than read as the default. An ``under`` without its trailing
    ``/`` is given one.
    """
    path = root / CONFIG_FILE
    if not path.is_file():
        return Config()
    try:
        whole: object = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        msg = f"{CONFIG_FILE} is not JSON: {error}"
        raise ConfigError(msg) from error
    if not isinstance(whole, dict):
        msg = f"{CONFIG_FILE} is not an object"
        raise ConfigError(msg)
    tells = cast("dict[str, object]", whole).get("tells")
    if tells is None:
        return Config()
    if not isinstance(tells, dict):
        msg = f"{CONFIG_FILE}: tells is not an object"
        raise ConfigError(msg)
    given = cast("dict[str, object]", tells)
    unknown = sorted(set(given) - {"readers", "guide", "languages", "history_codes", "commands"})
    if unknown:
        msg = f"{CONFIG_FILE}: tells has unknown keys {', '.join(unknown)}"
        raise ConfigError(msg)
    readers = _strings(given.get("readers", []), "readers")
    wrong = sorted(set(readers) - READERS)
    if wrong:
        known = ", ".join(sorted(READERS))
        msg = f"{CONFIG_FILE}: unknown readers {', '.join(wrong)} (known: {known})"
        raise ConfigError(msg)
    return Config(
        readers=frozenset(readers),
        guide=tuple(_strings(given.get("guide", []), "guide")),
        languages=_languages(given.get("languages", {})),
        history_codes=_codes(given.get("history_codes")),
        commands=tuple(_command(one) for one in _list(given.get("commands", []), "commands")),
    )


def _list(value: object, key: str) -> list[object]:
    if not isinstance(value, list):
        msg = f"{CONFIG_FILE}: tells.{key} is not a list"
        raise ConfigError(msg)
    return cast("list[object]", value)


def _strings(value: object, key: str) -> list[str]:
    items = _list(value, key)
    if not all(isinstance(one, str) and one for one in items):
        msg = f"{CONFIG_FILE}: tells.{key} holds something other than non-empty strings"
        raise ConfigError(msg)
    return cast("list[str]", items)


def _languages(value: object) -> dict[str, Language]:
    known = get_args(Language.__value__)
    if not isinstance(value, dict):
        msg = f"{CONFIG_FILE}: tells.languages is not an object"
        raise ConfigError(msg)
    pairs = cast("dict[object, object]", value)
    for name, language in pairs.items():
        if not isinstance(name, str) or language not in known:
            msg = (
                f"{CONFIG_FILE}: tells.languages maps {name!r} to {language!r}, "
                f"not one of {', '.join(known)}"
            )
            raise ConfigError(msg)
    return cast("dict[str, Language]", dict(pairs))


def _codes(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        msg = f"{CONFIG_FILE}: tells.history_codes is not a non-empty string"
        raise ConfigError(msg)
    try:
        re.compile(value)
    except re.error as error:
        msg = f"{CONFIG_FILE}: tells.history_codes does not compile: {error}"
        raise ConfigError(msg) from error
    return value


def _command(value: object) -> Command:
    if not isinstance(value, dict):
        msg = f"{CONFIG_FILE}: a tells.commands entry is not an object"
        raise ConfigError(msg)
    entry = cast("dict[str, object]", value)
    under = entry.get("under")
    if not isinstance(under, str) or not under:
        msg = f"{CONFIG_FILE}: a tells.commands entry has no under"
        raise ConfigError(msg)
    run = _strings(entry.get("run"), "commands[].run")
    suffixes = _strings(entry.get("suffixes"), "commands[].suffixes")
    if not run or not suffixes:
        msg = f"{CONFIG_FILE}: a tells.commands entry needs run and suffixes"
        raise ConfigError(msg)
    return Command(under if under.endswith("/") else f"{under}/", tuple(run), frozenset(suffixes))
