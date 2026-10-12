"""The tells: one rule per habit of machine-written prose, each with its plain fix.

A rule names one tell and the kinds of text it reads. There is no score: a
banned rule is a tell to remove wherever it is found, and a rationed rule is
fine once and a habit in bulk, so it is counted and reported per ten thousand
words.

Every rule carries text it must fire on and a near miss it must leave alone,
and the tests run both: a rule narrowed until it went blind fails there.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Literal

type Text = Literal["guide", "copy", "doc", "comment"]
"""The four kinds of prose: the pages a product's users read (the paths a project
names as its guide), the copy a program shows (read by a command a project
names), every other Markdown page, and the comments and docstrings in code."""

type Role = Literal["text", "item", "heading"]
"""Where a stretch of prose sits: running text, a list item, a heading."""

type Kind = Literal["banned", "rationed"]

type Language = Literal["en", "es", "pt"]
"""The language a stretch of prose is written in, from the tree it sits in
(``es-419`` is ``es``, ``pt-BR`` is ``pt``); everything else is English."""

ENGLISH: frozenset[Language] = frozenset({"en"})
EVERY: frozenset[Language] = frozenset({"en", "es", "pt"})

TEXTS: frozenset[Text] = frozenset({"guide", "copy", "doc", "comment"})
ROLES: frozenset[Role] = frozenset({"text", "item", "heading"})
RUNNING: frozenset[Role] = frozenset({"text", "item"})
PAGES: frozenset[Text] = frozenset({"guide", "doc"})
HISTORY: frozenset[Text] = frozenset({"guide", "copy", "comment"})
"""Where a code or a date is history: the text a user reads, and comments, which
describe the code as it stands. Plans and records cite them as part of what they
record."""


@dataclass(frozen=True)
class Rule:
    """One tell: what it matches, in which text, and what to write instead."""

    name: str
    kind: Kind
    pattern: re.Pattern[str]
    fix: str
    fires: tuple[str, ...]
    """Text the rule must find at least once."""
    misses: tuple[str, ...]
    """Near misses the rule must leave alone."""
    texts: frozenset[Text] = TEXTS
    roles: frozenset[Role] = ROLES
    languages: frozenset[Language] = ENGLISH
    """The languages the rule reads. A rule is written in one language's words, so
    the default is English; the marks that need no words (a dash, an emoji, a
    history code) name every language."""


def rx(pattern: str, *, case: bool = False) -> re.Pattern[str]:
    """Compile a rule's pattern, ignoring case unless the rule is about case."""
    return re.compile(pattern, 0 if case else re.IGNORECASE)


_VOCABULARY = (
    r"delve\w*|tapestry|landscape|robust|seamless(?:ly)?|leverag\w*|crucial|pivotal|vital|"
    r"ensur\w*|empower\w*|unlock\w*|elevat\w*|foster\w*|holistic|transformative|"
    r"game[- ]chang\w*|cutting[- ]edge|state[- ]of[- ]the[- ]art|journey|testament|"
    r"underscor(?:ed|ing)|underscores (?:the|that|how|why)|streamlin\w*|synerg\w*|paradigm|"
    r"comprehensive|meticulous\w*|intricate|"
    r"nuanced|boasts?|vibrant|groundbreaking|revolutioni\w*|bolster\w*|garner\w*|enhanc\w*|"
    r"interplay|enduring|commendable|noteworthy|myriad|plethora|multifaceted|"
    r"ever[- ]evolving|innovative|impactful|supercharg\w*|turbocharg\w*|"
    r"next[- ]level|world[- ]class|best[- ]in[- ]class|mission[- ]critical"
)
"""Words a model leans on, less the ones code uses as terms: a test *harness*, a
*showcase*, a router's *navigate*, a *dynamic* import, a *highlighted* row, an
*actionable* error, an identity provider's *realm*, and the *underscore* in a name
(the verb stays)."""

ISSUE_REFERENCE = r"(?<![\w&/#])#\d{2,4}\b"
"""An issue or pull request cited by number. A project adds its own codes (ticket
keys, chunk or ruling numbers) with :func:`with_history_codes`."""

_USED_TO = "".join(
    f"(?<!\\b{word} )"
    for word in ("is", "are", "was", "were", "be", "been", "being", "get", "gets")
)

BANNED: tuple[Rule, ...] = (
    Rule(
        "dash",
        "banned",
        rx(r"\u2014|(?<=\s)\u2013(?=\s)"),
        "use a comma, a colon, a period or parentheses",
        fires=("The run stops — and waits.", "ten \u2013 twenty"),
        misses=("pages 10\u201320", "L1\u2013L8"),
        languages=EVERY,
    ),
    Rule(
        "negative-parallelism",
        "banned",
        rx(
            r"\bnot (?:just|only|merely|simply)\b"
            r"|\bnot\b[^.;:?!]{1,50}?\bbut\b"
            r"|\b(?:it|this|that)(?:['\u2019]s| is) not\b[^.;:?!]{1,40}[,;]\s*"
            r"(?:it|this|that)(?:['\u2019]s| is)\b"
        ),
        "say what it is; drop what it is not",
        fires=(
            "It's not a cache, it's a ledger.",
            "not just a list but a record",
            "This is not a retry but a new run.",
        ),
        misses=(
            "It is not unique.",
            "What a run spends on it is not counted.",
            "Nothing but the key is kept.",
        ),
    ),
    Rule(
        "negative-parallelism-split",
        "banned",
        rx(
            r"(?<!\bthat )(?<!\bwhich )(?<!\bwho )\b(?:is|are|was|were) not\b[^.;!?]{0,60}[.;]\s+"
            r"(?:it|they|this|that) (?:is|are|was|were)\b(?!\s+(?:not|what|why|how)\b)"
            r"|\bdid not\b[^.;!?]{0,60}[.;]\s+we\b"
        ),
        "say what it is; drop the sentence about what it is not",
        fires=(
            "We did not make the agents smarter; we made every run provable.",
            "It is not a cache. It is a ledger.",
            "They are not found here; they are rows a person writes.",
        ),
        misses=(
            "It is not unique. Two agents may share it.",
            "A package whose modules are not Python names one (here); this module runs it.",
            "Revoking does not cancel the runs it started. It does stop the polling.",
            "It is not a marker. It is not enough after an answer.",
            "The field is not sent. That is what keeps it short.",
            "a heading that is not a page; it is gone",
        ),
    ),
    Rule(
        "x-not-y",
        "banned",
        rx(r"\b\w+, (?:not|never) \w+\b|\b\w+ed,? not \w+ed\b"),
        "state the one that holds; the contrast is rarely needed",
        fires=("Proof, not promises", "refused, not corrected", "recorded not deleted"),
        misses=("It does not retry.", "If not, the run stops."),
    ),
    Rule(
        "rhetorical-question",
        "banned",
        rx(
            r"(?:^|(?<=[.!]\s))(?:who|what|why|how|can|is|are|does)\b[^.?!\"”*()]{0,60}\?(?![\"”*)])"
        ),
        "state the point",
        fires=("Agents fix faults. Who proves it?", "Why does it stop? The budget ran out."),
        misses=(
            'It asks "Is this the right agent?"',
            "The run stops when the budget is spent.",
            "It asks *Pause this run?* before it acts.",
            "the real question (does it resolve somewhere private?) is asked later",
            "They ask the same question: what did a caller send?",
        ),
        # The guide only. In a comment a question is how a predicate's doc reads
        # ("Does this instant fall inside the window?"), and in a brief or a plan
        # it is an open question put to the owner, which the record exists to carry.
        texts=frozenset({"guide"}),
        roles=RUNNING,
    ),
    Rule(
        "colon-reveal",
        "banned",
        rx(
            r"\b(?:the (?:risk|truth|catch|point|problem|twist)"
            r"|here['\u2019]s (?:the|what|why))\b[^:.!?]{0,40}:"
        ),
        "say it in one sentence",
        fires=(
            "The risk is plain: we hit it in the first hour.",
            "that is the point: a crash loses it",
        ),
        misses=(
            "The key field holds 32 bytes: base64.",
            "what the answer should have said: low",
            "The result, for a run: its output.",
            "which is the truth. Handled here: the rejection",
        ),
    ),
    Rule(
        "inflated-vocabulary",
        "banned",
        rx(rf"\b(?:{_VOCABULARY})\b"),
        "use the plain word",
        fires=("We delve into the tapestry.", "a seamless, robust flow"),
        misses=(
            "the test harness",
            "the demo's showcases",
            "navigate to the page",
            "a dynamic import",
        ),
    ),
    Rule(
        "copula-avoidance",
        "banned",
        rx(
            r"\b(?:serves? as|stands? as|functions? as|represents? an?"
            r"|plays? an? (?:(?:key|crucial|vital|pivotal) )?role)\b"
        ),
        "say *is*",
        fires=("The table serves as the ledger.", "Each row represents a run."),
        misses=(
            "It serves the page.",
            "The reader marks a site dead.",
            "A key with no narrowing acts as its owner.",
        ),
    ),
    Rule(
        "intensifier",
        "banned",
        rx(
            r"\b(?:truly|genuinely|really|actually|deeply|incredibly|undeniably|fundamentally"
            r"|ultimately|notably|importantly|crucially|essentially|simply put)\b"
        ),
        "drop it",
        fires=("This is truly important.",),
        misses=("The truth table",),
    ),
    Rule(
        "realness",
        "banned",
        rx(
            r"\b(?:not (?:hypothetical|theoretical|academic)|real[- ]world"
            r"|the real (?:risk|problem|question))\b"
        ),
        "say what happened, and when",
        fires=("The risk is not hypothetical.", "a real-world case"),
        misses=("a real provider call",),
    ),
    Rule(
        "signposting",
        "banned",
        rx(
            r"\b(?:it['\u2019]s worth noting|it is worth noting|let['\u2019]s"
            r"|in conclusion|in summary"
            r"|overall,|to sum up|the bottom line|at its core|at the heart of|when it comes to"
            r"|in today['\u2019]s|in an era|make no mistake|the takeaway"
            r"|here['\u2019]s the thing|what this means)"
        ),
        "start with the point",
        fires=("It's worth noting that runs stop.", "In summary, the gate holds."),
        misses=("Let the run stop.", "the overall count"),
    ),
    Rule(
        "hollow-closer",
        "banned",
        rx(
            r"\b(?:speaks? for itself|matters? most|that['\u2019]s the point|and that['\u2019]s"
            r"|nothing more, nothing less|from day one)\b"
        ),
        "stop at the last fact",
        fires=("It speaks for itself.", "and that's the point"),
        misses=("the design review", "a blank canvas by design"),
    ),
    Rule(
        "vague-attribution",
        "banned",
        rx(
            r"\b(?:experts (?:say|argue|agree)|studies show|industry reports"
            r"|many believe|it is widely)\b"
        ),
        "name the source",
        fires=("Experts agree it works.",),
        misses=("an expert reviewer",),
    ),
    Rule(
        "filler-phrase",
        "banned",
        rx(
            r"\b(?:in order to|due to the fact that|at this point in time"
            r"|a wide (?:range|array|variety) of|each and every)\b"
        ),
        "cut it to the verb",
        fires=("in order to stop",),
        misses=("a number of seconds", "in the order given"),
    ),
    Rule(
        "assistant-voice",
        "banned",
        rx(
            r"\b(?:great question|i hope this helps|happy to help|let me know if|feel free to)\b"
            r"|\bcertainly!"
        ),
        "delete it",
        fires=("I hope this helps.", "Certainly!"),
        misses=("certainly not",),
    ),
    Rule(
        "emoji",
        "banned",
        rx("[\U0001f300-\U0001faff✅❌✨]"),
        "use words",
        fires=("Done ✅",),
        misses=("Done ✓",),
        languages=EVERY,
    ),
    Rule(
        "guide-word",
        "banned",
        rx(
            r"\b(?:powerful|flexible|intuitive|effortless(?:ly)?|simply|just|easily|utili[sz](?:e|es|ed|ing))\b"
        ),
        "a word a user guide does without: cut it or say what happens",
        fires=("Simply click Save.", "It just works."),
        misses=("justify the column",),
        texts=frozenset({"guide"}),
    ),
    Rule(
        "chat-leakage",
        "banned",
        rx(
            r"\b(?:rest of the (?:code|file|function)"
            r" (?:unchanged|stays|remains|goes here|as before)"
            r"|(?:the|existing|other) code (?:here )?(?:stays |remains |is )?unchanged"
            r"|here['\u2019]s the (?:updated|new|fixed|full))\b"
        ),
        "delete it: it was addressed to a chat",
        fires=(
            "... rest of the code unchanged",
            "Here's the updated function",
            "existing code unchanged",
        ),
        misses=(
            "the rest of the run",
            "would lose the rest of the file to a typo",
            "Lifted out of code unchanged",
            "each left code unchanged",
        ),
        texts=frozenset({"comment"}),
    ),
    Rule(
        "step-narration",
        "banned",
        rx(r"(?:^|[.:]\s+)(?:first|now|next|then|finally),? we\b"),
        "say what the code holds; the order is in the code",
        fires=("First, we parse it.", "Read the file. Now we split it."),
        # A numbered step is the structure of an example walkthrough and of the
        # wizard, so "Step 2:" is left alone.
        misses=("the first step", "Step 2: identity and purpose."),
        texts=frozenset({"comment"}),
    ),
    Rule(
        "history-code",
        "banned",
        rx(ISSUE_REFERENCE, case=True),
        "describe the code as it stands; the history is in git and the tracker",
        fires=("See #381.", "fixed in #42"),
        misses=("color #fff", "step #1", "a&#123;"),
        texts=HISTORY,
        languages=EVERY,
    ),
    Rule(
        "history-date",
        "banned",
        rx(r"\b20\d\d-[01]\d-[0-3]\d\b"),
        "describe the code as it stands; the date is in git",
        fires=("(owner, 2026-09-03)",),
        misses=("version 2026.10",),
        texts=HISTORY,
        languages=EVERY,
    ),
    Rule(
        "history-phrase",
        "banned",
        rx(rf"{_USED_TO}\b(?-i:used to)\b|\b(?:found|seen|caught) in the browser\b"),
        "describe the code as it stands",
        fires=("This used to fail.", "found in the browser: the pager"),
        # "Used to gate the note" opens a sentence in the passive, its "is" left out.
        misses=(
            "The key is used to sign.",
            "It was used to seed the world.",
            "Used to gate the note.",
        ),
        texts=HISTORY,
    ),
)

RATIONED: tuple[Rule, ...] = (
    Rule(
        "rather-than",
        "rationed",
        rx(r"\brather than\b"),
        "keep the one that holds",
        fires=("refuses rather than guesses",),
        misses=("would rather",),
    ),
    Rule(
        "exactly",
        "rationed",
        rx(r"\bexactly\b"),
        "drop it",
        fires=("exactly once",),
        misses=("exact",),
    ),
    Rule(
        "the-one",
        "rationed",
        rx(
            r"\bthe one (?!(?:that|who|which|whose|with|in|on|at|for|of|from|to|it|you|we|they"
            r"|before|after|above|below|named|called|shown|listed|here|there|is|was|are|and|or)\b)[a-z]"
        ),
        "say *the*",
        fires=("the one place", "the one thing"),
        misses=("the one that failed", "the one in the list"),
    ),
    Rule(
        "the-whole",
        "rationed",
        rx(r"\bthe whole\b"),
        "say *the*, or *all*",
        fires=("the whole page",),
        misses=("a whole",),
    ),
    Rule(
        "says-so",
        "rationed",
        rx(r"\b(?:says?|said) so\b"),
        "say what it says",
        fires=("it says so",),
        misses=("says the",),
    ),
    Rule(
        "silently",
        "rationed",
        rx(r"\b(?:silently|quietly)\b"),
        "say what nobody sees",
        fires=("silently dropped",),
        misses=("silent",),
    ),
    Rule(
        "deliberately",
        "rationed",
        rx(r"\b(?:deliberately|on purpose)\b"),
        "give the reason, or nothing",
        fires=("deliberately left out",),
        misses=("purpose",),
    ),
    Rule(
        "honest",
        "rationed",
        rx(r"\bhonest(?:ly|y)?\b"),
        "drop it",
        fires=("the honest half",),
        misses=("hone",),
    ),
    Rule(
        "load-bearing",
        "rationed",
        rx(r"\b(?:load-bearing|by construction)\b"),
        "say what depends on it",
        fires=("a load-bearing line", "true by construction"),
        misses=("the construction",),
    ),
    Rule(
        "which-is-why",
        "rationed",
        rx(r"\b(?:which|that) is (?:why|what|how)\b"),
        "state the cause first",
        fires=("which is why it stops",),
        misses=("which is the key",),
    ),
    Rule(
        "semicolon",
        "rationed",
        rx(";"),
        "make it two sentences",
        fires=("Stop; wait.",),
        misses=("Stop. Wait.",),
    ),
    Rule(
        "bold-lead-in",
        "rationed",
        rx(r"^\*\*"),
        "drop the bold, or make it a heading",
        fires=("**Lead** text",),
        misses=("text **bold**",),
        texts=PAGES,
        roles=frozenset({"item"}),
    ),
)

RULES: tuple[Rule, ...] = BANNED + RATIONED


def with_history_codes(rules: tuple[Rule, ...], codes: str) -> tuple[Rule, ...]:
    r"""Return the rules with a project's own history codes added to ``history-code``.

    ``codes`` is a regular expression, matched case-sensitively, for the codes a
    project's records use (``JIRA-\d+``, a chunk number), which a comment or a
    user's page cites as history. The rule keeps its own plants: it still finds
    an issue number and still leaves a colour alone.
    """
    pattern = re.compile(f"{ISSUE_REFERENCE}|(?:{codes})")
    return tuple(
        replace(rule, pattern=pattern) if rule.name == "history-code" else rule for rule in rules
    )
