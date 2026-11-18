"""Write the page the owner reads: each section's verdict, then each changed section rendered.

An edited section shows its rendered text with the words taken out struck and the words put in
marked. The two versions are rendered first and compared tag by tag and word by word, so a mark
never breaks the Markdown it sits in. A rewritten or new section shows whole, a removed one folded.
Each file is a tab, and each section to read a fold, open unless it was removed.
"""

from __future__ import annotations

import html
import re
from collections import Counter
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
:root { --fg: #1f2328; --bg: #fff; --line: #d0d7de; color-scheme: light; }
:root[data-theme="dark"] { --fg: #e6edf3; --bg: #0d1117; --line: #30363d; color-scheme: dark; }
body { font: 15px/1.55 -apple-system, system-ui, sans-serif; max-width: 52rem;
  margin: 2rem auto; padding: 0 1rem; color: var(--fg); background: var(--bg); }
.theme { float: right; font: inherit; font-size: 13px; cursor: pointer; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
td, th { border-bottom: 1px solid var(--line); padding: .25rem .5rem; text-align: left;
  vertical-align: top; }
.quiet { opacity: .55; }
.tag { font-size: 12px; font-weight: 600; padding: .05rem .4rem; border-radius: 1rem;
  white-space: nowrap; }
.rewritten, .new { background: #ffd8b5; color: #5c2d00; }
.edited { background: #fff3b0; color: #4d3b00; }
.removed { background: #ffd1d1; color: #5c0000; }
.moved, .renamed, .unchanged { background: #e1e4e8; color: #333; }
.tabs > input { display: none; }
.panel { display: none; padding-top: 1rem; }
nav { display: flex; flex-wrap: wrap; gap: .25rem; border-bottom: 1px solid var(--line); }
.tab { cursor: pointer; padding: .35rem .75rem; border: 1px solid transparent;
  border-radius: .4rem .4rem 0 0; margin-bottom: -1px; }
.count { font-size: 12px; opacity: .7; }
.name { display: inline-block; max-width: 16rem; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; vertical-align: bottom; }
.link { cursor: pointer; text-decoration: underline; }
details.section { border: 1px solid var(--line); border-radius: .4rem; margin: .6rem 0; }
details.section > summary { padding: .4rem .6rem; }
details.section[open] > summary { border-bottom: 1px solid var(--line); }
.body { padding: 0 1rem; }
details.rest { margin: 1rem 0; }
details.rest li { margin: .2rem 0; list-style: none; }
.tools button { font: inherit; font-size: 13px; cursor: pointer; }
ins { background: #c9f2d0; color: #0b3d16; text-decoration: none; }
del { background: #ffd1d1; color: #5c0000; }
details > summary { cursor: pointer; }
a { color: inherit; }
"""

PICKED = "border-color: var(--line); border-bottom-color: transparent; font-weight: 600;"


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


NO_READING = frozenset({Verdict.UNCHANGED, Verdict.MOVED, Verdict.RENAMED})

THEME = """
const root = document.documentElement;
const dark = matchMedia('(prefers-color-scheme: dark)').matches;
root.dataset.theme = localStorage.getItem('reread-theme') || (dark ? 'dark' : 'light');
"""

SCRIPT = """
const toggle = document.querySelector('.theme');
const name = () => document.documentElement.dataset.theme === 'dark' ? 'Light' : 'Dark';
toggle.textContent = name();
toggle.addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('reread-theme', next);
  toggle.textContent = name();
});
document.querySelectorAll('[data-fold]').forEach(b => b.addEventListener('click', () => {
  const open = b.dataset.fold === 'open';
  b.closest('.panel').querySelectorAll('details').forEach(d => { d.open = open; });
}));
"""


def tag(change: Change) -> str:
    """Return the verdict as a coloured tag, with the share of words changed where it counts."""
    share = ""
    if change.verdict in {Verdict.EDITED, Verdict.REWRITTEN}:
        share = f" {round(change.changed * 100)}%"
    return f'<span class="tag {change.verdict}">{change.verdict}{share}</span>'


def where(change: Change) -> str:
    """Return the headings above the section, quiet, then its own in bold."""
    above = [MarkdownIt("commonmark").renderInline(p) for p in change.section.path[:-1]]
    lead = f'<span class="quiet">{" / ".join(above)} / </span>' if above else ""
    return f"{lead}<b>{title(change.section)}</b>"


def block(change: Change) -> str:
    """Return a section to read as a fold, open unless the section was removed."""
    opened = "" if change.verdict is Verdict.REMOVED else " open"
    said = f'<span class="quiet"> · {ADVICE[change.verdict]}</span>{noted(change)}'
    return (
        f'<details class="section"{opened}>\n<summary>{tag(change)} {where(change)}{said}'
        f'</summary><div class="body">{body(change)}</div></details>'
    )


def noted(change: Change) -> str:
    """Return the section's notes, quiet, or nothing."""
    if not change.notes:
        return ""
    return f' <span class="quiet">· {html.escape(", ".join(change.notes))}</span>'


def rest(changes: list[Change]) -> str:
    """Return the sections that need no reading, folded together."""
    if not changes:
        return ""
    items = "".join(f"<li>{tag(c)} {where(c)}{noted(c)}</li>" for c in changes)
    return (
        f'<details class="rest"><summary>{len(changes)} sections need no reading</summary>'
        f"<ul>{items}</ul></details>"
    )


def counts(report: FileReport) -> str:
    """Return the file's verdicts counted, as tags."""
    found = Counter(change.verdict for change in report.changes)
    return " ".join(f'<span class="tag {v}">{n} {v}</span>' for v, n in found.items())


def to_read(report: FileReport) -> list[Change]:
    """Return the file's sections that need reading, in document order."""
    return [c for c in report.changes if c.verdict not in NO_READING]


def panel(f: int, report: FileReport) -> str:
    """Return a file's tab: its sections to read, each a fold, then the rest folded together."""
    gone = " (deleted)" if report.gone else ""
    reading = to_read(report)
    tools = (
        '<p class="tools"><button data-fold="open">Expand all</button> '
        '<button data-fold="close">Collapse all</button></p>'
    )
    shown = "".join(block(c) for c in reading)
    if not reading:
        shown = "<p>Nothing to read again.</p>"
    rested = rest([c for c in report.changes if c.verdict in NO_READING])
    return (
        f'<div class="panel" id="p{f}"><h2>{html.escape(report.path)}{gone}</h2>'
        f"<p>{counts(report)}</p>{tools}{shown}{rested}</div>"
    )


def overview(reports: list[FileReport]) -> str:
    """Return the first tab: one row per file, its sections to read and its counts."""
    rows = "".join(
        f'<tr><td><label for="t{f}" class="link">{html.escape(r.path)}</label>'
        f"{' (deleted)' if r.gone else ''}</td><td>{len(to_read(r))}</td><td>{counts(r)}</td></tr>"
        for f, r in enumerate(reports)
    )
    return (
        '<div class="panel" id="pov"><table><tr><th>File</th><th>To read</th><th>Verdicts</th>'
        f"</tr>{rows}</table></div>"
    )


def page(reports: list[FileReport], why: str, threshold: float) -> str:
    """Return the whole page: an overview tab, then a tab per file with its sections as folds."""
    ids = ["ov", *(str(f) for f in range(len(reports)))]
    radios = "".join(
        f'<input type="radio" name="tab" id="t{i}"{" checked" if i == "ov" else ""}>' for i in ids
    )
    labels = '<label class="tab" for="tov">Overview</label>' + "".join(
        f'<label class="tab" for="t{f}" title="{html.escape(r.path)}">'
        f'<span class="name">{html.escape(r.path.rsplit("/", 1)[-1])}</span>'
        f' <span class="count">{len(to_read(r))}</span></label>'
        for f, r in enumerate(reports)
    )
    shows = ", ".join(f"#t{i}:checked ~ #p{i}" for i in ids)
    picked = ", ".join(f"#t{i}:checked ~ nav label[for=t{i}]" for i in ids)
    return "\n".join(
        [
            "<!doctype html><meta charset='utf-8'><title>What to read again</title>",
            f"<script>{THEME}</script>",
            f"<style>{STYLE}{shows} {{ display: block; }} {picked} {{ {PICKED} }}</style>",
            '<button class="theme">Dark</button><h1>What to read again</h1>',
            f"<p>Compared with {html.escape(why)}.</p>",
            f"<p class='quiet'>Rewritten: over {round(threshold * 100)}% of the words changed.</p>",
            f'<div class="tabs">{radios}<nav>{labels}</nav>',
            overview(reports),
            *(panel(f, r) for f, r in enumerate(reports)),
            f"</div><script>{SCRIPT}</script>",
        ]
    )


def summary(reports: list[FileReport]) -> str:
    """Return one line per file with its counts, then one per section to read."""
    lines: list[str] = []
    for report in reports:
        found = Counter(change.verdict for change in report.changes)
        said = ", ".join(f"{n} {v}" for v, n in found.items())
        lines.append(f"{report.path}{' (deleted)' if report.gone else ''}: {said}")
        for change in report.changes:
            if change.verdict not in {Verdict.UNCHANGED, Verdict.MOVED, Verdict.RENAMED}:
                where = " / ".join(change.section.path) or change.section.title
                lines.append(f"  {change.verdict:<9} {where}")
    return "\n".join(lines)
