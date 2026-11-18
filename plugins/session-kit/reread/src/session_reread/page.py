"""Write the page the owner reads: each section's verdict, then each changed section rendered.

An edited section shows its rendered text with the words taken out struck and the words put in
marked. The two versions are rendered first and compared tag by tag and word by word, so a mark
never breaks the Markdown it sits in. A rewritten or new section shows whole, a removed one folded.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from markdown_it import MarkdownIt

from session_reread.sections import READ_WHOLE, Change, Section, Verdict

TOKEN = re.compile(r"<[^>]+>|[^<\s]+|\s+")
TAG = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9]*)[^>]*>")
ROW = re.compile(r"<tr>.*?</tr>", re.DOTALL)
VOID = frozenset({"br", "hr", "img", "input", "ins", "del"})

ADVICE = {
    Verdict.UNCHANGED: "skip",
    Verdict.MOVED: "skip, it moved",
    Verdict.RENAMED: "skip, its heading changed",
    Verdict.EDITED: "read the marked changes",
    Verdict.REWRITTEN: "read it whole",
    Verdict.NEW: "read it whole",
    Verdict.REMOVED: "check nothing you wanted went",
}

STYLE = """
body { font: 15px/1.55 -apple-system, system-ui, sans-serif; max-width: 52rem;
  margin: 2rem auto; padding: 0 1rem; color: #1f2328; background: #fff; }
@media (prefers-color-scheme: dark) { body { color: #e6edf3; background: #0d1117; }
  table td, table th { border-color: #30363d; } section { border-color: #30363d; } }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
td, th { border-bottom: 1px solid #d0d7de; padding: .25rem .5rem; text-align: left;
  vertical-align: top; }
.quiet { opacity: .55; }
.tag { font-size: 12px; font-weight: 600; padding: .05rem .4rem; border-radius: 1rem;
  white-space: nowrap; }
.rewritten, .new { background: #ffd8b5; color: #5c2d00; }
.edited { background: #fff3b0; color: #4d3b00; }
.removed { background: #ffd1d1; color: #5c0000; }
.moved, .renamed, .unchanged { background: #e1e4e8; color: #333; }
section { border-left: 3px solid #d0d7de; padding-left: 1rem; margin: 2rem 0; }
ins { background: #c9f2d0; color: #0b3d16; text-decoration: none; }
del { background: #ffd1d1; color: #5c0000; }
details > summary { cursor: pointer; }
a { color: inherit; }
"""


@dataclass(frozen=True)
class FileReport:
    """One file's changes, and whether the file is gone."""

    path: str
    changes: list[Change]
    gone: bool = False


def render(section: Section) -> str:
    """Return the section's body as HTML."""
    return MarkdownIt("commonmark").enable("table").render(section.body)


def marked(old: str, new: str) -> str:
    """Return the new rendering with the old words it lacks struck and its own new words marked."""
    a = TOKEN.findall(old)
    b = TOKEN.findall(new)
    out: list[str] = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            out.extend(b[j1:j2])
            continue
        if op in {"delete", "replace"}:
            words = "".join(t for t in a[i1:i2] if not t.startswith("<")).strip()
            if words:
                out.append(f"<del>{words}</del> ")
        if op in {"insert", "replace"}:
            out.extend(
                t if t.startswith("<") or not t.strip() else f"<ins>{t}</ins>" for t in b[j1:j2]
            )
    return "".join(out)


def title(section: Section) -> str:
    """Return the section's heading as HTML, its inline Markdown rendered."""
    return MarkdownIt("commonmark").renderInline(section.title)


def heading(change: Change) -> str:
    """Return the section's heading, one level below the file's."""
    level = min(max(change.section.level, 1) + 1, 6)
    return f"<h{level}>{title(change.section)}</h{level}>"


def blocks(rendered: str) -> list[str]:
    """Split rendered HTML into its top-level elements, a table's rows each counted as one."""
    found: list[str] = []
    depth = 0
    start = 0
    for m in TAG.finditer(rendered):
        closing, name = m.group(1) == "/", m.group(2).lower()
        if name in VOID:
            continue
        if not closing:
            if depth == 0:
                start = m.start()
            depth += 1
            continue
        depth -= 1
        if depth == 0:
            found.append(rendered[start : m.end()])
    return found


def changed_only(rendered: str) -> str:
    """Keep the blocks that hold a mark, and of a table its head and its marked rows."""
    kept: list[str] = []
    for block in blocks(rendered):
        if "<ins>" not in block and "<del>" not in block:
            continue
        if block.startswith("<table"):
            rows = ROW.findall(block)
            marked_rows = [r for r in rows[1:] if "<ins>" in r or "<del>" in r]
            kept.append("<table>" + "".join(rows[:1] + marked_rows) + "</table>")
        else:
            kept.append(block)
    return "\n".join(kept)


def body(change: Change) -> str:
    """Return what the page shows of a section, empty for one that needs no reading."""
    old, new = change.old, change.new
    if change.verdict is Verdict.EDITED and old and new:
        whole = marked(render(old), render(new))
        return (
            f"{changed_only(whole)}<details><summary>the whole section</summary>{whole}</details>"
        )
    if change.verdict is Verdict.REMOVED and old:
        return f"<details><summary>the removed text</summary>{render(old)}</details>"
    if change.verdict in READ_WHOLE and new:
        was = f"<details><summary>the old version</summary>{render(old)}</details>" if old else ""
        return render(new) + was
    return ""


def row(anchor: str, change: Change) -> str:
    """Return the section's row in the file's table."""
    s = change.section
    indent = "&nbsp;" * 3 * max(s.level - 1, 0)
    name = title(s)
    if body(change):
        name = f'<a href="#{anchor}">{name}</a>'
    share = ""
    if change.verdict in {Verdict.EDITED, Verdict.REWRITTEN}:
        share = f" {round(change.changed * 100)}%"
    notes = html.escape(", ".join(change.notes))
    quiet = ' class="quiet"' if change.verdict is Verdict.UNCHANGED else ""
    tag = f'<span class="tag {change.verdict}">{change.verdict}{share}</span>'
    cells = [f"{indent}{name}", tag, ADVICE[change.verdict], notes]
    return f"<tr{quiet}>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


def page(reports: list[FileReport], why: str, threshold: float) -> str:
    """Return the whole page: per file, the table of verdicts, then the sections to read."""
    parts = [
        "<!doctype html><meta charset='utf-8'><title>What to read again</title>",
        f"<style>{STYLE}</style>",
        "<h1>What to read again</h1>",
        f"<p>Compared with {html.escape(why)}.</p>",
        f"<p class='quiet'>Rewritten: over {round(threshold * 100)}% of the words changed.</p>",
    ]
    for f, report in enumerate(reports):
        parts.append(f"<h2>{html.escape(report.path)}{' (deleted)' if report.gone else ''}</h2>")
        parts.append(
            "<table><tr><th>Section</th><th>Verdict</th><th>What to do</th><th>Notes</th></tr>"
        )
        parts.extend(row(f"s{f}-{c}", change) for c, change in enumerate(report.changes))
        parts.append("</table>")
        for c, change in enumerate(report.changes):
            shown = body(change)
            if shown:
                parts.append(f'<section id="s{f}-{c}">{heading(change)}{shown}</section>')
    return "\n".join(parts)


def summary(reports: list[FileReport]) -> str:
    """Return one line per file with its counts, then one per section to read."""
    lines: list[str] = []
    for report in reports:
        counts: dict[Verdict, int] = {}
        for change in report.changes:
            counts[change.verdict] = counts.get(change.verdict, 0) + 1
        said = ", ".join(f"{n} {v}" for v, n in counts.items())
        lines.append(f"{report.path}{' (deleted)' if report.gone else ''}: {said}")
        for change in report.changes:
            if change.verdict not in {Verdict.UNCHANGED, Verdict.MOVED, Verdict.RENAMED}:
                where = " / ".join(change.section.path) or change.section.title
                lines.append(f"  {change.verdict:<9} {where}")
    return "\n".join(lines)
