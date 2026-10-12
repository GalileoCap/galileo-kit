"""A project's own history codes, added to the ``history-code`` rule."""

from __future__ import annotations

from session_tells import rules
from session_tells.rules import Rule, with_history_codes

CODES = r"\bJIRA-\d+\b"


def _history(table: tuple[Rule, ...]) -> Rule:
    (rule,) = [rule for rule in table if rule.name == "history-code"]
    return rule


def test_the_project_codes_are_found() -> None:
    """The rule finds a project's code once its pattern is added."""
    assert _history(rules.RULES).pattern.search("see JIRA-77") is None
    assert _history(with_history_codes(rules.RULES, CODES)).pattern.search("see JIRA-77")


def test_the_codes_are_matched_with_case() -> None:
    """The project's codes match case-sensitively, so a lower-case word is left alone."""
    rule = _history(with_history_codes(rules.RULES, CODES))
    assert rule.pattern.search("the jira-77 label") is None


def test_the_rule_keeps_its_own_plants() -> None:
    """The widened rule still finds an issue number and still leaves a colour alone."""
    rule = _history(with_history_codes(rules.RULES, CODES))
    for text in rule.fires:
        assert rule.pattern.search(text), text
    for text in rule.misses:
        assert rule.pattern.search(text) is None, text
    assert rule.pattern.search("See #381.")
    assert rule.pattern.search("color #fff") is None


def test_only_the_history_rule_changes() -> None:
    """Every other rule comes back as it was, in the same order, and none is added."""
    widened = with_history_codes(rules.RULES, CODES)
    assert [rule.name for rule in widened] == [rule.name for rule in rules.RULES]
    for before, after in zip(rules.RULES, widened, strict=True):
        if before.name != "history-code":
            assert after == before
    assert _history(widened).kind == "banned"
    assert _history(widened).texts == _history(rules.RULES).texts
