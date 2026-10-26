"""A review's mechanical third: what a program can read off a candidate plugin.

``review`` runs the engine's validator and ``plugin details`` over a plugin
cloned for review, reads its manifest, its git commit and its size, and
lists the strings in its source that hold a control character. It grades
each ``$`` call by a table of the 85 members Claude Code 2.1.308 declares,
and names each hook with what it sees and whether it gates without a
``.catch``. None of the plugin's code runs: the engine's two commands read
it, git and ast-grep run from an empty directory outside it, and every
string the clone supplies is shown with its control characters spelled out
and the section's markers broken, so a terminal printing the review runs
nothing and the next run finds the section whole. The result is a section
between its own markers, replaced where it stands in the review, so the
reviewer's text around it is never changed.
"""

from __future__ import annotations

import json
import os
import re
import stat
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from session_codeintel import footprint, looks, reach
from session_codeintel.settings import is_list, is_record

START = "<!-- session-codeintel review -->"
END = "<!-- end of session-codeintel review -->"
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
"""A plugin name safe to pass to the engine: no option, no path."""


ESCAPES = (
    r"^\\(x([01][0-9A-Fa-f]|7[Ff]|[89][0-9A-Fa-f])|u(00[01][0-9A-Fa-f]|007[Ff]|00[89][0-9A-Fa-f])"
    r"|u\{0*([01]?[0-9A-Fa-f]|7[Ff]|[89][0-9A-Fa-f])\}|[0-7]{1,3}|[bfvr])$"
)
"""The escapes that can stand for a control character; tab and newline among them fall out later."""
RULES = "\n---\n".join(
    f"id: {kind}-{language}\nlanguage: {language}\nrule:\n  kind: {kind}\n{extra}"
    for language in ("typescript", "tsx", "javascript")
    for kind, extra in (
        ("escape_sequence", f"  regex: '{ESCAPES}'\n"),
        ("string_fragment", "  regex: '[\\x00-\\x08\\x0B-\\x1F\\x7F-\\x9F]'\n"),
    )
)
"""Each escape of a control in a string or template literal, and each raw control in one."""
ALL_FILES = ("hidden", "dot", "vcs", "parent", "global", "exclude")
"""ast-grep's ignore sources, each turned off: a file the clone commits is read, ignored or not."""
SOURCES = ("ts", "tsx", "mts", "cts", "js", "jsx", "mjs", "cjs")
"""The files a hooks module can import; a page the plugin serves is no module."""
SIMPLE = {"b": "\b", "f": "\f", "v": "\v", "r": "\r", "t": "\t", "n": "\n", "0": "\0"}
CONTROLS = frozenset(range(0x20)) - {ord("\t"), ord("\n")} | frozenset(range(0x7F, 0xA0))
"""C0 but tab and newline, delete, and C1: what a terminal takes as a command."""
KIB = 1024


@dataclass(frozen=True, slots=True)
class Clone:
    """Where the plugin sits in git: the repository, its commit and where it came from."""

    root: Path | None
    commit: str
    date: str
    origin: str
    changed: int


@dataclass(frozen=True, slots=True)
class Size:
    """The files and bytes under a directory, its symbolic links apart."""

    files: int
    size: int
    links: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class Read:
    """Everything the review read, before it is written out."""

    plugin: Path
    name: str
    version: str
    engine: str
    report: dict[str, object]
    details: str
    clone: Clone
    folder: Size
    repository: Size | None
    controls: tuple[tuple[str, str], ...]


def read(engine: str, plugin: Path) -> Read:
    """Read the plugin through the engine, git, ast-grep and the file system.

    Raises:
        footprint.FootprintError: the engine cannot run, or printed no report.

    """
    with tempfile.TemporaryDirectory() as empty:
        away = Path(empty)
        version = footprint.run([engine, "--version"], away).stdout.split()
        if not version:
            msg = f"{engine} --version printed nothing"
            raise footprint.FootprintError(msg)
        done = footprint.run([engine, "plugin", "validate", "--json", str(plugin)], away)
        try:
            report: object = json.loads(done.stdout)
        except json.JSONDecodeError as broken:
            msg = f"the validator printed no report: {(done.stdout + done.stderr).strip()[:200]}"
            raise footprint.FootprintError(msg) from broken
        if not is_record(report):
            msg = "the validator's report is not an object"
            raise footprint.FootprintError(msg)
        name, version_of = manifest(plugin)
        clone = clone_of(plugin, away)
        return Read(
            plugin,
            name,
            version_of,
            version[0],
            report,
            details(engine, plugin, name, away),
            clone,
            size(plugin),
            None if clone.root in (None, plugin) else size(clone.root),
            controls(plugin, away),
        )


def manifest(plugin: Path) -> tuple[str, str]:
    """Return the name and version plugin.json gives, each empty when it gives none."""
    try:
        held: object = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text("utf-8"))
    except (OSError, ValueError):
        return "", ""
    if not is_record(held):
        return "", ""
    name, version = held.get("name"), held.get("version")
    return (name if isinstance(name, str) else "", version if isinstance(version, str) else "")


def details(engine: str, plugin: Path, name: str, away: Path) -> str:
    """Return what ``plugin details`` prints, or why it was not run."""
    if not NAME.fullmatch(name):
        return "plugin.json gives no name the engine can be asked about, so it was not run."
    done = footprint.run([engine, "--plugin-dir", str(plugin), "plugin", "details", name], away)
    text = (done.stdout + done.stderr).rstrip()
    return text if done.returncode == 0 else f"{text}\n(exited {done.returncode})"


def clone_of(plugin: Path, away: Path) -> Clone:
    """Read the commit the plugin's repository stands at, with the repository's config inert."""

    def git(*argv: str) -> str:
        argv_ = ["git", "-c", "core.fsmonitor=false", "-C", str(plugin), *argv]
        done = footprint.run(argv_, away)
        return done.stdout.strip() if done.returncode == 0 else ""

    top = git("rev-parse", "--show-toplevel")
    if not top:
        return Clone(None, "", "", "", 0)
    changed = git("status", "--porcelain", "--", ".")
    return Clone(
        Path(top).resolve(),
        git("rev-parse", "HEAD"),
        git("log", "-1", "--format=%cs"),
        git("remote", "get-url", "origin"),
        len(changed.splitlines()),
    )


def size(top: Path) -> Size:
    """Count the files and bytes under a directory, never following a link, git's own left out."""
    files = 0
    total = 0
    links: list[tuple[str, str]] = []
    for here, dirs, names in os.walk(top, followlinks=False):
        dirs[:] = [d for d in dirs if d != ".git"]
        for entry in [*dirs, *names]:
            path = Path(here) / entry
            held = path.lstat()
            if stat.S_ISLNK(held.st_mode):
                links.append((str(path.relative_to(top)), str(path.readlink())))
            elif stat.S_ISREG(held.st_mode):
                files += 1
                total += held.st_size
    return Size(files, total, tuple(sorted(links)))


def controls(plugin: Path, away: Path) -> tuple[tuple[str, str], ...]:
    """List each source line whose strings hold a control character but tab and newline."""
    argv = [str(looks.AST_GREP), "scan", "--inline-rules", RULES, "--json=compact"]
    argv += [flag for source in ALL_FILES for flag in ("--no-ignore", source)]
    argv += [flag for ext in SOURCES for flag in ("--globs", f"**/*.{ext}")]
    done = footprint.run([*argv, str(plugin)], away)
    if done.returncode != 0:
        msg = f"ast-grep failed: {done.stderr.strip()}"
        raise footprint.FootprintError(msg)
    found: dict[tuple[str, int], list[str]] = {}
    matches: object = json.loads(done.stdout or "[]")
    for match in matches if is_list(matches) else []:
        if not is_record(match):
            continue
        text, file, at = match.get("text"), match.get("file"), match.get("range")
        start = at.get("start") if is_record(at) else None
        line = start.get("line") if is_record(start) else None
        if not isinstance(text, str) or not isinstance(file, str) or not isinstance(line, int):
            continue
        chars = text if not text.startswith("\\") else decoded(text)
        if any(control(c) for c in chars):
            where = (str(Path(file).resolve().relative_to(plugin.resolve())), line + 1)
            found.setdefault(where, []).append(text)
    return tuple(
        (f"{file}:{line}", " ".join(texts)) for (file, line), texts in sorted(found.items())
    )


def decoded(escape: str) -> str:
    """Return what an escape sequence stands for; empty for a quote, a backslash or a break."""
    body = escape[1:]
    try:
        if body.startswith("u{"):
            return chr(int(body[2:-1], 16))
        if body[:1] in ("x", "u"):
            return chr(int(body[1:], 16))
        if body.isdigit():
            return chr(int(body, 8))
    except ValueError:
        return ""
    return SIMPLE.get(body, "")


def control(char: str) -> bool:
    """Whether a character is a control character other than tab and newline."""
    return ord(char) in CONTROLS


def shown(text: str, *, lines: bool = False) -> str:
    """Spell out the control characters of the clone's text, and break the section's markers."""
    out = "".join(
        f"\\x{ord(c):02x}" if control(c) or (c == "\n" and not lines) or c == "\t" else c
        for c in text
    )
    return out.replace("<!--", "< !--").replace("-->", "-- >")


def code(text: str) -> str:
    """Show the clone's text as inline code in a table cell."""
    inner = shown(text).replace("|", "\\|")
    fence = "`" * (max((len(r) for r in re.findall("`+", inner)), default=0) + 1)
    pad = " " if inner.startswith("`") or inner.endswith("`") else ""
    return f"{fence}{pad}{inner}{pad}{fence}"


def fenced(text: str) -> str:
    """Show the clone's text as a block no backtick of its own can close."""
    inner = shown(text, lines=True)
    fence = "`" * max(3, max((len(r) for r in re.findall("`+", inner)), default=0) + 1)
    return f"{fence}text\n{inner}\n{fence}"


def human(size: int) -> str:
    """Write a byte count for a reader."""
    if size < KIB:
        return f"{size} bytes"
    if size < KIB * KIB:
        return f"{size / KIB:.1f} KiB"
    return f"{size / (KIB * KIB):.1f} MiB"


def counted(count: int, noun: str) -> str:
    """Write a count with its noun, plural but for one."""
    return f"{count} {noun}{'' if count == 1 else 's'}"


def problems(report: dict[str, object]) -> list[str]:
    """Return the validator's errors and warnings, one line each, in its order."""
    out: list[str] = []
    for part in parts(report):
        for severity in ("errors", "warnings"):
            found = part.get(severity)
            for problem in found if is_list(found) else []:
                if is_record(problem):
                    where, message = problem.get("path"), problem.get("message")
                    out.append(f"{severity[:-1]} {code(str(where))}: {shown(str(message))}")
    return out


def parts(report: dict[str, object]) -> list[dict[str, object]]:
    """Return the report's manifest and each file it checked."""
    found = [report.get("manifest")]
    contents = report.get("contents")
    found += contents if is_list(contents) else []
    return [part for part in found if is_record(part)]


def lines_of(report: dict[str, object]) -> dict[str, tuple[str, ...]]:
    """Read every note of the report as the footprint gate reads the validator's lines."""
    found: list[str] = []
    for part in parts(report):
        listed = part.get("notes")
        found += [n for n in listed if isinstance(n, str)] if is_list(listed) else []
    return footprint.notes(found)


def gating(report: dict[str, object]) -> Counter[tuple[str, str, bool]]:
    """Count the gating hooks by module, hook and whether a ``.catch`` follows."""
    found: Counter[tuple[str, str, bool]] = Counter()
    for part in parts(report):
        listed = part.get("gatingHooks")
        for hook in listed if is_list(listed) else []:
            if is_record(hook):
                key = (str(hook.get("module")), str(hook.get("hook")), hook.get("hasCatch") is True)
                found[key] += 1
    return found


def render(seen: Read, today: str) -> str:
    """Write the section: the clone, the validator, the reach, the hooks and the files."""
    found = lines_of(seen.report)
    shortened = footprint.cut(found)
    calls, unclassified = reach.graded(found)
    out = [
        START,
        "## What the program read",
        "",
        f"Written by `session-codeintel review` on {today} with Claude Code {seen.engine}, "
        "from the plugin at "
        f"{code(home(seen.plugin))}. It ran the engine's validator and `plugin details`, read "
        "the plugin's files and git, and ran none of the plugin's code. Nothing here is a "
        "verdict: the hooks and the calls below are where the reading starts. The next run "
        "replaces this section and nothing around it.",
        "",
        "| | |",
        "| --- | --- |",
        *header(seen, calls, unclassified, shortened),
        "",
        "### What the validator found",
        "",
        *(f"- {line}" for line in problems(seen.report) or ["Nothing: no error and no warning."]),
        *cuts(found, shortened),
        "",
        *call_table(calls, unclassified),
        "",
        *hook_table(found, gating(seen.report)),
        "",
        *surroundings(found, seen.name),
        "",
        "### `claude plugin details`",
        "",
        fenced(seen.details),
        "",
        *control_list(seen.controls, found),
        "",
        "### Symbolic links",
        "",
        *links(seen.repository or seen.folder),
        END,
    ]
    return "\n".join(out)


def links(widest: Size) -> list[str]:
    """Name each symbolic link of the widest walk, and where it leads."""
    if not widest.links:
        return ["None."]
    return [f"- {code(path)} leads to {code(target)}" for path, target in widest.links]


def home(path: Path) -> str:
    """Write a path under the home directory with a tilde."""
    text = str(path)
    mine = str(Path.home())
    return "~" + text[len(mine) :] if text.startswith(mine + os.sep) else text


def header(
    seen: Read,
    calls: list[tuple[str, str, int, str]],
    unclassified: list[str],
    shortened: tuple[str, ...],
) -> list[str]:
    """Return the header table's rows."""
    clone = seen.clone
    verdict = "passed" if seen.report.get("success") is True else "failed"
    tally = Counter(line.partition(" ")[0] for line in problems(seen.report))
    errors, warnings = tally["error"], tally["warning"]
    level = max((c[2] for c in calls), default=0)
    labels = sorted({c[3] for c in calls if c[3]}, key=reach.ORDER.index)
    partial = bool(unclassified) or any(h.endswith(" calls") for h in shortened)
    graded = f"{'at least ' if partial else ''}L{level}, {reach.LEVELS[level]}"
    graded += f": {', '.join(labels)}." if labels else "."
    if unclassified:
        graded += f" {counted(len(unclassified), 'call')} unclassified."
    if any(h.endswith(" calls") for h in shortened):
        graded += " The calls were cut short."
    folder = seen.folder
    tree = f"{counted(clone.changed, 'path')} differ from the commit" if clone.changed else "clean"
    rows = [
        f"| Plugin | {code(seen.name or '(no name)')} {shown(seen.version) or 'with no version'} |",
        f"| Commit | {code(clone.commit)}, committed {clone.date} |"
        if clone.commit
        else "| Commit | not in a git repository |",
        f"| Origin | {code(clone.origin)} |" if clone.origin else "| Origin | none |",
        f"| Working tree | {tree} |",
        f"| Engine | Claude Code {shown(seen.engine)} |",
        f"| Validator | {verdict}, {counted(errors, 'error')}, {counted(warnings, 'warning')} |",
        f"| Reach | {graded} |",
        f"| Install | {human(folder.size)} in {counted(folder.files, 'file')}, the plugin's "
        "folder, which an install copies |",
    ]
    if seen.repository is not None:
        rows.append(
            f"| Marketplace | {human(seen.repository.size)} in "
            f"{counted(seen.repository.files, 'file')}, the repository, which adding it as a "
            "marketplace clones |"
        )
    return rows


def cuts(found: dict[str, tuple[str, ...]], shortened: tuple[str, ...]) -> list[str]:
    """Name each line the engine cut short, with what it hides."""
    out: list[str] = []
    for head in shortened:
        marked = next(i for i in found[head] if footprint.CUT.search(i))
        out.append(
            f"- The engine cut {code(head)} short at {code(marked)}: what follows the cut is "
            "unseen, so read the source for it."
        )
    return out


def call_table(calls: list[tuple[str, str, int, str]], unclassified: list[str]) -> list[str]:
    """Return the table of the calls on ``$``, widest reach first."""
    out = ["### Calls on `$`, by reach", ""]
    if not calls and not unclassified:
        return [*out, "None."]
    out += ["| Member | Through | Level |", "| --- | --- | --- |"]
    out += [
        f"| {code(member)} | {shown(via) or 'the hook itself'} | L{level}{label and ', ' + label} |"
        for member, via, level, label in calls
    ]
    out += [
        f"| {code(member)} | | unclassified: not among the 85 members of 2.1.308 |"
        for member in unclassified
    ]
    return out


def hook_table(
    found: dict[str, tuple[str, ...]], gates: Counter[tuple[str, str, bool]]
) -> list[str]:
    """Return the table of the hooks, with what each sees and whether it gates."""
    out = ["### Hooks", ""]
    rows: list[str] = []
    left = Counter(gates)
    for head, listed in found.items():
        module, kind = reach.kind_of(head)
        if kind != "hooks":
            continue
        for item in listed:
            event, _, matcher = item.partition("{")
            matcher = matcher.removesuffix("}")
            gate = ""
            for catches, said in ((False, "without .catch"), (True, "with .catch")):
                if left[(module, item, catches)] > 0:
                    left[(module, item, catches)] -= 1
                    gate = said
                    break
            rows.append(
                f"| {code(event)} | {code(matcher) if matcher else 'none'} | {gate or 'no'} | "
                f"{'hot' if reach.hot(event, matcher) else ''} | {reach.note(event)} |"
            )
    if not rows:
        return [*out, "None."]
    return [
        *out,
        "| Event | Matcher | Gating | Hot | What to read |",
        "| --- | --- | --- | --- | --- |",
        *rows,
    ]


def surroundings(found: dict[str, tuple[str, ...]], name: str) -> list[str]:
    """Return the environment, the state and the validator's other lines."""
    out = ["### Environment and state", ""]
    by_kind: defaultdict[str, list[str]] = defaultdict(list)
    other: list[str] = []
    for head, listed in found.items():
        _, kind = reach.kind_of(head)
        if kind in {"hooks", "calls", "gating hook with .catch", "gating hook without .catch"}:
            continue
        if kind:
            by_kind[kind].extend(listed)
        else:
            other.append(f"- {code(head)}: {', '.join(code(i) for i in listed) or 'nothing'}")
    for kind, said in (
        ("env reads", "Environment read"),
        ("env writes", "Environment written"),
        ("hooks telemetry for", "Telemetry hooked for"),
        ("declares on $", "Declares on `$`"),
    ):
        listed = sorted(set(by_kind[kind]))
        out.append(f"- {said}: {', '.join(code(i) for i in listed) or 'nothing'}")
    counts = {
        k: len({key for key in by_kind[k] if not footprint.CUT.search(key)})
        for k in ("state writes", "state reads", "declares state")
    }
    out.append(
        f"- State: {counts['state writes']} keys written, {counts['state reads']} read, "
        f"{counts['declares state']} declared"
    )
    foreign = sorted(
        {
            k
            for k in by_kind["state reads"]
            if k.partition(".")[0] != name and not footprint.CUT.search(k)
        }
    )
    if foreign:
        out.append(f"- State of another plugin read: {', '.join(code(k) for k in foreign)}")
    return [*out, *other]


def control_list(
    found_controls: tuple[tuple[str, str], ...], found: dict[str, tuple[str, ...]]
) -> list[str]:
    """Return the list of source lines whose strings hold a control character."""
    draws = any(
        item.startswith("ui.render")
        for head, listed in found.items()
        if reach.kind_of(head)[1] == "hooks"
        for item in listed
    )
    out = [
        "### Control characters in source strings",
        "",
        "Each line of the plugin's TypeScript and JavaScript whose strings hold a control "
        "character other than tab and newline, comments and regular expressions left out. "
        "A string built at run time (`String.fromCharCode(27)`) is not seen. "
        + (
            "The plugin hooks `ui.render`, where such a string can rewrite what a terminal draws."
            if draws
            else "The plugin hooks no `ui.render`."
        ),
        "",
    ]
    if not found_controls:
        return [*out, "None."]
    return [*out, *(f"- {code(where)}: {code(texts)}" for where, texts in found_controls)]


def placed(existing: str | None, title: str, section: str) -> str:
    """Return the review with the section: replaced where it stands, else after the heading."""
    if existing is None:
        return f"# Review: {title}\n\n{section}\n"
    start = existing.rfind(START)
    end = existing.find(END, start) if start >= 0 else -1
    if end >= 0:
        return existing[:start] + section + existing[end + len(END) :]
    lines = existing.splitlines(keepends=True)
    for at, line in enumerate(lines):
        if line.startswith("# "):
            return "".join(lines[: at + 1]) + "\n" + section + "\n" + "".join(lines[at + 1 :])
    return f"{section}\n\n{existing}"
