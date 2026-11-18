"""What the owner relies on: every change shows in a section to read, and nothing else does."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from typing import TYPE_CHECKING

from session_reread.baseline import Prompt, find
from session_reread.page import FileReport, marked, page
from session_reread.sections import Verdict, compare

if TYPE_CHECKING:
    from pathlib import Path

OLD = """---
id: A1
status: proposed
---

# Spec

Intro text that stays.

## Goals

We want a fast tool,
that reads well.

## Risks

Many risks are listed in this section of the text, one after the other.

### Detail

Some detail words that stay put.

## Gone

This whole part goes away.
"""

NEW = """---
id: A1
status: decided
---

# Spec

Intro text that stays.

## Aims

We want a fast tool, that reads well.

## Risks

Many risks are listed in this part of the text, one after the other.

## Other

Fresh words about something else entirely.

### Detail

Some detail words that stay put.
"""


def _verdicts(old: str, new: str) -> dict[str, Verdict]:
    return {c.section.title: c.verdict for c in compare(old, new, 0.4)}


def test_each_change_lands_in_the_section_it_touched_and_nowhere_else() -> None:
    """Front matter, reflow, a rename, an edit, a new, a moved and a removed section."""
    assert _verdicts(OLD, NEW) == {
        "(front matter)": Verdict.EDITED,
        "Spec": Verdict.UNCHANGED,
        "Aims": Verdict.RENAMED,
        "Risks": Verdict.EDITED,
        "Other": Verdict.NEW,
        "Detail": Verdict.MOVED,
        "Gone": Verdict.REMOVED,
    }


def test_a_section_mostly_replaced_is_rewritten() -> None:
    """Past the threshold, the section is read whole."""
    new = OLD.replace("We want a fast tool,\nthat reads well.", "Speed matters less than clarity.")
    assert _verdicts(OLD, new)["Goals"] is Verdict.REWRITTEN


def test_a_changed_subsection_shows_though_its_parent_did_not_change() -> None:
    """A change at any depth is the subsection's own, and only it shows."""
    new = OLD.replace("Some detail words that stay put.", "Some detail words that moved on.")
    changed = {t: v for t, v in _verdicts(OLD, new).items() if v is not Verdict.UNCHANGED}
    assert changed == {"Detail": Verdict.EDITED}


def test_marks_never_wrap_a_tag() -> None:
    """Marks go around words only, so the rendered Markdown keeps its structure."""
    out = marked("<p>a <code>b</code> c</p>", "<p>a <em>b</em> d</p>")
    assert "<ins><" not in out
    assert "<del><" not in out
    assert "<ins>d</ins>" in out
    assert "<del>c</del>" in out


def _details(text: str) -> dict[str, bool]:
    """Each section block's own heading, and whether it opens unfolded."""
    found = re.findall(
        r'<details class="section"[^>]*?( open)?>\s*<summary>.*?<b>(.*?)</b>', text, re.DOTALL
    )
    return {name: bool(opened) for opened, name in found}


def test_a_section_to_read_opens_and_the_rest_fold() -> None:
    """Edited, rewritten and new sections open, a removed one folds, and the rest fold together."""
    text = page([FileReport("a.md", compare(OLD, NEW, 0.4))], "HEAD", 0.4)
    assert _details(text) == {"(front matter)": True, "Risks": True, "Other": True, "Gone": False}
    rest = re.search(r'<details class="rest">(.*?)</details>', text, re.DOTALL)
    assert rest is not None
    assert all(name in rest.group(1) for name in ("Spec", "Aims", "Detail"))


def _git(repo: Path, *args: str, at: int = 0) -> str:
    exe = shutil.which("git")
    assert exe is not None
    env = dict(os.environ)
    if at:
        env |= {"GIT_COMMITTER_DATE": f"@{at} +0000", "GIT_AUTHOR_DATE": f"@{at} +0000"}
    done = subprocess.run(  # noqa: S603  git on the test's own repository, no shell
        [exe, "-C", str(repo), *args], check=True, capture_output=True, text=True, env=env
    )
    return done.stdout.strip()


def _commit(repo: Path, at: int, text: str) -> None:
    (repo / "spec.md").write_text(text, encoding="utf-8")
    _git(repo, "add", ".", at=at)
    _git(repo, "commit", "-qm", text, at=at)


def test_the_baseline_is_the_version_before_the_turn_that_last_edited_the_files(
    tmp_path: Path,
) -> None:
    """A prompt after the editing turn, such as asking what changed, does not move the baseline."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "commit.gpgsign", "false")
    _commit(repo, 1000, "draft")
    read = _git(repo, "rev-parse", "HEAD")
    _commit(repo, 2100, "revised")
    _commit(repo, 2200, "revised again")
    said = [
        Prompt(900, "write the spec"),
        Prompt(2000, "my feedback"),
        Prompt(3000, "what changed?"),
    ]
    assert find(repo, ["spec.md"], said).ref == read
