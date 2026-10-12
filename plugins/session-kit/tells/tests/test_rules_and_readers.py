"""The rules against their plants, the Markdown and Python readers, and what a hit is held to."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

import pytest

from session_tells import find
from session_tells.readers.markdown import markdown
from session_tells.readers.python import python
from session_tells.ruleset import RULES
from session_tells.units import Unit

if TYPE_CHECKING:
    from session_tells.rules import Language, Rule, Text

LANGUAGES: dict[str, Language] = {"es-419": "es", "pt-BR": "pt"}


@pytest.mark.parametrize("rule", RULES, ids=lambda rule: rule.name)
def test_each_rule_finds_its_plants_and_leaves_its_near_misses(rule: Rule) -> None:
    """A rule narrowed until it went blind, or widened onto a plain sentence, fails here."""
    assert [text for text in rule.fires if not rule.pattern.search(text)] == []
    assert [text for text in rule.misses if rule.pattern.search(text)] == []


def test_markdown_reads_prose_and_leaves_code_out() -> None:
    """Front matter, fences and HTML are not prose; inline code keeps the sentence's shape."""
    source = dedent("""\
        ---
        title: A — page
        ---
        # The run — a heading

        A run `stops — here` and
        waits — there.

        - **Lead** in an item

        | a | b |
        | --- | --- |
        | — | x |

        ```
        x = 1 — 2
        ```
        <!-- a — comment -->
        """)
    units = markdown("docs/guide/10-runs.md", source, guide=True)
    assert [(unit.role, unit.pieces) for unit in units] == [
        ("heading", ((4, "The run — a heading"),)),
        ("text", ((6, "A run code and"), (7, "waits — there."))),
        ("item", ((9, "**Lead** in an item"),)),
        ("text", ((11, "a"),)),
        ("text", ((11, "b"),)),
        ("text", ((13, "x"),)),
    ]
    assert {unit.text for unit in units} == {"guide"}
    assert {unit.text for unit in markdown("docs/a.md", source)} == {"doc"}


def test_python_reads_comment_blocks_and_docstrings_and_skips_pragmas() -> None:
    """Adjacent comment lines are one unit; a pragma and a doctest line are not prose."""
    source = dedent('''\
        #!/usr/bin/env python
        """The module — its docstring.

        >>> run()
        """

        x = 1  # noqa: E501
        # One line,
        # and the next.

        # Apart.
        ''')
    units = python("pkg/mod.py", source)
    assert [unit.pieces for unit in units] == [
        ((8, "One line,"), (9, "and the next.")),
        ((11, "Apart."),),
        ((2, "The module — its docstring."), (3, "")),
    ]


def _unit(text: str, kind: Text = "comment", path: str = "f.py") -> Unit:
    return Unit(path, kind, "text", ((1, text),))


def test_a_rule_reads_only_its_kinds_of_text() -> None:
    """History is a tell in a comment and a record in a plan; the guide's words bind the guide."""
    found = find.hits(
        [
            _unit("Since #381 it simply waits.", "doc"),
            _unit("Since #381 it simply waits.", "guide"),
        ],
        RULES,
    )
    assert {(hit.text, hit.rule) for hit in found} == {
        ("guide", "history-code"),
        ("guide", "guide-word"),
    }


def test_a_rule_reads_only_the_languages_it_is_written_in() -> None:
    """A translated tree is read by its own table and the marks that need no words."""
    sentence = "Un flujo sin fisuras y sem costura, the run is truly vital — #381!"
    found = {
        language: {
            hit.rule
            for hit in find.hits([_unit(sentence, "guide", path)], RULES, languages=LANGUAGES)
        }
        for language, path in {
            "en": "docs/guide/en/a.md",
            "es": "docs/guide/es-419/a.md",
            "pt": "web/src/locales/pt-BR/a.ts",
        }.items()
    }
    shared = {"dash", "history-code"}
    assert find.language_of("docs/guide/es-419/a.md", LANGUAGES) == "es"
    assert find.language_of("docs/guide/en/a.md", LANGUAGES) == "en"
    assert found["en"] == shared | {"intensifier", "inflated-vocabulary"}
    assert found["es"] == shared | {"exclamation", "inflated-vocabulary-es"}
    assert found["pt"] == shared | {"exclamation", "inflated-vocabulary-pt"}


def test_a_marker_allows_its_rule_on_its_line_and_nothing_else() -> None:
    """The door for a false hit names the rule, and holds for one line."""
    text = "# Kept, not lost — here.  tells: allow x-not-y\n# Kept, not lost.\n"
    unit = Unit("f.py", "comment", "text", ((1, "Kept, not lost — here."), (2, "Kept, not lost.")))
    found = find.hits([unit], RULES, allowed={"f.py": find.markers(text)})
    assert [(hit.line, hit.rule) for hit in found] == [(1, "dash"), (2, "x-not-y")]


def test_a_document_is_held_to_the_banned_rules_outside_what_it_quotes() -> None:
    """A dash in the document's own words is a hit; quoted or in emphasis, it is not."""
    source = dedent("""\
        # A brief

        The lane reads it — plainly.

        > The owner said it — like this.

        As the owner put it, "the run stops — then waits", and #12 says
        *never the model — never the cost*. Rather than wait, it acts.
        """)
    found = find.in_document("brief.md", source, RULES)
    assert [(hit.line, hit.rule) for hit in found] == [(3, "dash")]
