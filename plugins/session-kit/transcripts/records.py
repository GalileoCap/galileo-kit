"""Reading the sessions' transcripts into sessions, for ``session_transcripts.py``.

Each session leaves one JSONL file under ``~/.claude/projects/<project>/``.
A file is read once, record by record, into a ``Session``: its requests,
its warnings, its compactions, the hooks that fired, the tools it called,
what it read or ran again (``Waste``), the person's own prompts (``Ask``),
and what it shows of where it came from. ``link`` then joins the sessions
whose cost runs on one from the other, and the timeline session-kit's module writes under
``~/.claude/session-kit/measure/`` names the session a clear started.

The engine writes some records more than once under the same uuid (after a
compaction, the messages it keeps), and a fork's file begins with a copy of
its parent's records under the parent's id: each is counted once, in its
own session.
"""

from __future__ import annotations

import hashlib
import json
import re
import tarfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

WARNING = re.compile(r"Context at ([\d,]+) tokens \((\d+)% of")
HANDOFF_PATH = re.compile(r"CLAUDE\.local\.md$")
COMMIT = re.compile(r"(^|[;&|]\s*)git\s+commit\b")
COLD_GAP_MINUTES = 5
COLD_SHARE = 0.5
HOOK_ATTACHMENTS = ("hook_success", "hook_additional_context", "hook_system_message")
EDITS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
# The origin kinds of the person's own prompts; a record before the engine wrote origins has none.
PERSON = (None, "human")
# How long after a session's first record the session whose cost it runs on from may still write.
COST_SLACK = timedelta(minutes=1)


@dataclass
class Request:
    at: datetime
    fresh: int
    read: int
    created: int
    out: int
    model: str
    turn: int

    @property
    def context(self) -> int:
        return self.fresh + self.read + self.created


@dataclass
class Warning:
    at: datetime
    tokens: int
    percent: int
    turn: int
    handoff_turns: int | None = None
    commit_turns: int | None = None
    compaction_turns: int | None = None


@dataclass
class Compaction:
    at: datetime
    trigger: str
    pre_tokens: int
    duration_ms: int
    turn: int


@dataclass
class Waste:
    """What a session read or ran again, counted by context: each compaction starts the next.

    A file read again after a compaction is one an earlier context of the
    session read, counted at its first read in the new context. An unchanged
    read is a read in one context whose result is the read's before it, or
    the engine's own answer that the file is unchanged. A repeated output is
    any other call made again in one context, to the same input and the same
    output once runs of whitespace are taken as one.
    """

    reads: int = 0
    read_chars: int = 0
    again: int = 0
    again_chars: int = 0
    again_edited: int = 0
    unchanged: int = 0
    unchanged_chars: int = 0
    repeated: int = 0
    repeated_chars: int = 0
    again_by_compaction: list[int] = field(default_factory=list)

    @property
    def any(self) -> bool:
        return self.again + self.unchanged + self.repeated > 0


@dataclass
class Ask:
    """One of the person's own prompts. Its words are printed only with ``--quote``."""

    at: datetime | None
    text: str


@dataclass
class Session:
    id: str
    project: str
    path: Path
    started: datetime | None = None
    ended: datetime | None = None
    prompts: int = 0
    requests: list[Request] = field(default_factory=list)
    warnings: list[Warning] = field(default_factory=list)
    compactions: list[Compaction] = field(default_factory=list)
    hooks: dict[str, int] = field(default_factory=dict)
    hook_chars: dict[str, int] = field(default_factory=dict)
    tools: dict[str, int] = field(default_factory=dict)
    cost_usd: float | None = None
    lines_added: int = 0
    lines_removed: int = 0
    waste: Waste = field(default_factory=Waste)
    asks: list[Ask] = field(default_factory=list)
    # Where it came from: the parent a fork's copied records name, the cost those records carry,
    # and the start its cost state carries, which sessions whose running cost goes on one from the other share.
    forked_from: str | None = None
    carried_usd: float | None = None
    cost_start: int | None = None
    # Set by ``link``: the session it came from, how ("clear" or "resume" by the timeline,
    # "fork", "cost"), and its own cost, the running total it carried taken out.
    came_from: str | None = None
    how: str | None = None
    own_usd: float | None = None

    @property
    def cache_share(self) -> float | None:
        total = sum(r.context for r in self.requests)
        return sum(r.read for r in self.requests) / total if total else None

    def cold_sends(self) -> list[Request]:
        cold: list[Request] = []
        previous: Request | None = None
        for r in sorted(self.requests, key=lambda r: r.at):
            if previous is not None and r.context:
                gap = (r.at - previous.at).total_seconds() / 60
                if gap > COLD_GAP_MINUTES and r.created / r.context >= COLD_SHARE:
                    cold.append(r)
            previous = r
        return cold


@dataclass
class Reading:
    """The waste count's state through one transcript."""

    context: int = 0
    uses: dict[str, tuple[str, dict[str, object]]] = field(default_factory=dict)
    answered: set[str] = field(default_factory=set)
    last: dict[tuple[int, str, str], str] = field(default_factory=dict)
    first_read: dict[str, int] = field(default_factory=dict)
    read_in: set[tuple[int, str]] = field(default_factory=set)
    edited: dict[str, int] = field(default_factory=dict)


def when(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def texts_of(value: object) -> list[str]:
    """Every string under a record's content, whatever its nesting."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [t for item in value for t in texts_of(item)]
    if isinstance(value, dict):
        return [t for item in value.values() for t in texts_of(item)]
    return []


def text_blocks(content: object) -> str:
    """The text a message or a tool result carries: a string, or its text blocks joined. An image counts nothing."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str))
    return ""


def session_id_of(path: Path) -> str:
    """The id a transcript's file name carries: `<id>.jsonl`, or an archive's `<id>.tar.xz`."""
    return path.name.split(".", 1)[0]


def lines_of(path: Path) -> Iterator[str]:
    """The transcript's lines. An archive (`.tar.xz`, as the owner's backup keeps a session with its
    subagents and file history) is read in a stream, its main `.jsonl` member alone."""
    if path.name.endswith(".tar.xz"):
        wanted = session_id_of(path) + ".jsonl"
        with tarfile.open(path, "r:xz") as archive:
            for member in archive:
                if member.isfile() and member.name.endswith("/" + wanted) and "/subagents/" not in member.name:
                    fh = archive.extractfile(member)
                    if fh is not None:
                        for raw in fh:
                            yield raw.decode("utf-8", errors="replace")
                    return
        return
    with path.open(encoding="utf-8") as fh:
        yield from fh


def read_session(path: Path) -> Session:
    session = Session(id=session_id_of(path), project=path.parent.name, path=path)
    seen_requests: set[str] = set()
    seen_records: set[str] = set()
    reading = Reading()
    turn = 0
    for line in lines_of(path):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if not isinstance(r, dict):
            continue
        kind = r.get("type")
        owner = r.get("sessionId")
        if isinstance(owner, str) and owner != session.id:
            if kind in ("user", "assistant") and session.forked_from is None:
                session.forked_from = owner
            if kind == "cost-state":
                session.carried_usd = float(r.get("totalCostUSD") or 0)
            continue
        uuid = r.get("uuid")
        if isinstance(uuid, str):
            if uuid in seen_records:
                continue
            seen_records.add(uuid)
        at = when(r.get("timestamp"))
        if at is not None and session.started is None:
            session.started = at
        if at is not None:
            session.ended = at
        sidechain = r.get("isSidechain") is True
        message = r.get("message") if isinstance(r.get("message"), dict) else {}
        content = message.get("content")
        if kind == "user" and not sidechain:
            is_prompt = (
                isinstance(content, str) or (isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "text" for b in content))
            ) and not r.get("isMeta") and not r.get("isCompactSummary")
            if is_prompt and not r.get("toolUseResult"):
                turn += 1
                session.prompts += 1
                note_ask(session, r, content, at)
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        note_warnings(session, texts_of(b.get("content")), at, turn)
                        note_result(session.waste, reading, b, r.get("toolUseResult"))
        elif kind == "assistant":
            usage = message.get("usage") if isinstance(message.get("usage"), dict) else None
            rid = str(r.get("requestId") or message.get("id") or r.get("uuid") or "")
            if usage and rid not in seen_requests and at is not None:
                seen_requests.add(rid)
                session.requests.append(Request(
                    at=at,
                    fresh=int(usage.get("input_tokens") or 0),
                    read=int(usage.get("cache_read_input_tokens") or 0),
                    created=int(usage.get("cache_creation_input_tokens") or 0),
                    out=int(usage.get("output_tokens") or 0),
                    model=str(message.get("model") or r.get("requestedModel") or ""),
                    turn=turn,
                ))
            if isinstance(content, list) and not sidechain:
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        note_tool(session, str(b.get("name") or ""), b.get("input"), turn)
                        note_use(reading, b)
        elif kind == "attachment":
            a = r.get("attachment") if isinstance(r.get("attachment"), dict) else {}
            if a.get("type") in HOOK_ATTACHMENTS:
                name = str(a.get("hookName") or a.get("type"))
                session.hooks[name] = session.hooks.get(name, 0) + 1
                text = "".join(texts_of([a.get("stdout"), a.get("content")]))
                session.hook_chars[name] = session.hook_chars.get(name, 0) + len(text)
                note_warnings(session, [text], at, turn)
        elif kind == "system" and r.get("subtype") == "compact_boundary":
            meta = r.get("compactMetadata") if isinstance(r.get("compactMetadata"), dict) else {}
            compaction = Compaction(
                at=at or session.started or datetime.now(timezone.utc),
                trigger=str(meta.get("trigger") or "?"),
                pre_tokens=int(meta.get("preTokens") or 0),
                duration_ms=int(meta.get("durationMs") or 0),
                turn=turn,
            )
            session.compactions.append(compaction)
            reading.context += 1
            session.waste.again_by_compaction.append(0)
            for w in session.warnings:
                if w.compaction_turns is None:
                    w.compaction_turns = turn - w.turn
        elif kind == "cost-state":
            session.cost_usd = float(r.get("totalCostUSD") or 0)
            session.lines_added = int(r.get("totalLinesAdded") or 0)
            session.lines_removed = int(r.get("totalLinesRemoved") or 0)
            start = r.get("startTime")
            if isinstance(start, int):
                session.cost_start = start
    return session


def note_warnings(session: Session, texts: list[str], at: datetime | None, turn: int) -> None:
    for text in texts:
        for m in WARNING.finditer(text):
            session.warnings.append(Warning(
                at=at or session.started or datetime.now(timezone.utc),
                tokens=int(m.group(1).replace(",", "")),
                percent=int(m.group(2)),
                turn=turn,
            ))


def note_tool(session: Session, name: str, inp: object, turn: int) -> None:
    session.tools[name] = session.tools.get(name, 0) + 1
    args = inp if isinstance(inp, dict) else {}
    is_handoff = (
        name in ("Write", "Edit") and HANDOFF_PATH.search(str(args.get("file_path") or "")) is not None
    ) or (name == "Skill" and "handoff" in str(args.get("skill") or ""))
    is_commit = name == "Bash" and COMMIT.search(str(args.get("command") or "")) is not None
    for w in session.warnings:
        if is_handoff and w.handoff_turns is None:
            w.handoff_turns = turn - w.turn
        if is_commit and w.commit_turns is None:
            w.commit_turns = turn - w.turn


def note_ask(session: Session, r: dict[str, object], content: object, at: datetime | None) -> None:
    """The prompt as one of the person's asks, unless a plugin, a notification or a peer sent it, or it is a command's markup."""
    origin = r.get("origin")
    kind = origin.get("kind") if isinstance(origin, dict) else None
    text = text_blocks(content).strip()
    if kind in PERSON and text and not text.startswith("<"):
        session.asks.append(Ask(at, text))


def note_use(reading: Reading, block: dict[str, object]) -> None:
    """A tool call, kept until its result, and the context in which a file was first edited."""
    name, inp, id_ = block.get("name"), block.get("input"), block.get("id")
    if not isinstance(name, str) or not isinstance(inp, dict) or not isinstance(id_, str):
        return
    reading.uses[id_] = (name, inp)
    path = inp.get("file_path") if "file_path" in inp else inp.get("notebook_path")
    if name in EDITS and isinstance(path, str) and path not in reading.edited:
        reading.edited[path] = reading.context


def note_result(waste: Waste, reading: Reading, block: dict[str, object], result: object) -> None:
    """A tool's result, against the results of the same call before it in the session."""
    id_ = block.get("tool_use_id")
    if not isinstance(id_, str) or id_ not in reading.uses or id_ in reading.answered:
        return
    reading.answered.add(id_)
    name, inp = reading.uses[id_]
    text = text_blocks(block.get("content"))
    digest = hashlib.sha1(" ".join(text.split()).encode("utf-8")).hexdigest()
    key = (reading.context, name, json.dumps(inp, sort_keys=True))
    same = text != "" and reading.last.get(key) == digest
    reading.last[key] = digest
    if name != "Read":
        if same:
            waste.repeated += 1
            waste.repeated_chars += len(text)
        return
    path = str(inp.get("file_path"))
    waste.reads += 1
    waste.read_chars += len(text)
    if same or (isinstance(result, dict) and result.get("type") == "file_unchanged"):
        waste.unchanged += 1
        waste.unchanged_chars += len(text)
    first = reading.first_read.setdefault(path, reading.context)
    if first < reading.context and (reading.context, path) not in reading.read_in:
        waste.again += 1
        waste.again_chars += len(text)
        waste.again_by_compaction[-1] += len(text)
        if path in reading.edited and reading.edited[path] < reading.context:
            waste.again_edited += 1
    reading.read_in.add((reading.context, path))


def transcript_paths(roots: list[Path]) -> list[Path]:
    """One path per session id over the roots, live transcripts first, then archives; a snapshot
    archive (`<id>.snapshot-<stamp>.tar.xz`) stands in only when no other file carries its id."""
    chosen: dict[str, Path] = {}
    for root in roots:
        for pattern in ("*/*.jsonl", "*/*.tar.xz"):
            for path in sorted(root.glob(pattern)):
                id_ = session_id_of(path)
                snapshot = ".snapshot-" in path.name
                if id_ not in chosen or (".snapshot-" in chosen[id_].name and not snapshot):
                    chosen[id_] = path
    return sorted(chosen.values())


def timeline_links(measure_dir: Path) -> dict[str, tuple[str, str]]:
    """The session a clear or a resume started, by the line session-kit's timeline opens its first file
    with: ``{session: (the session before it, "clear" or "resume")}``."""
    links: dict[str, tuple[str, str]] = {}
    if not measure_dir.is_dir():
        return links
    for folder in sorted(measure_dir.iterdir()):
        files = sorted(folder.glob("*.jsonl"), key=lambda p: p.name) if folder.is_dir() else []
        if not files:
            continue
        try:
            text = files[0].read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict) and record.get("ev") == "session" and isinstance(record.get("from"), str):
                links[folder.name] = (record["from"], str(record.get("reason")))
    return links


def link(sessions: list[Session], timeline: dict[str, tuple[str, str]]) -> None:
    """Each session's predecessor and how it came from it, then its own cost.

    The timeline names the session a clear or a resume started. A fork's file
    names its parent. Otherwise a session whose cost state shares its start
    with others came after the one of them that ended last before it began.
    The engine's cost is a running total that a fork carries on, and a clear
    too when the new session's cost state keeps the start, so a session's own
    cost is its total less what it carried in.
    """
    by_id = {s.id: s for s in sessions}
    for s in sessions:
        named = timeline.get(s.id)
        if named is not None and named[0] in by_id:
            s.came_from, s.how = named
        elif s.forked_from is not None:
            s.came_from, s.how = s.forked_from, "fork"
        elif s.cost_start is not None and s.started is not None:
            start = s.started
            before = [
                (o.ended, o.id) for o in sessions
                if o is not s and o.cost_start == s.cost_start and o.started is not None and o.started < start
                and o.ended is not None and o.ended <= start + COST_SLACK
            ]
            if before:
                s.came_from, s.how = max(before)[1], "cost"
    for s in sessions:
        if s.cost_usd is None:
            continue
        previous = by_id.get(s.came_from) if s.came_from is not None else None
        if s.forked_from is not None:
            s.own_usd = s.cost_usd - (s.carried_usd or 0.0)
        elif previous is not None and previous.cost_usd is not None and previous.cost_start == s.cost_start:
            s.own_usd = s.cost_usd - previous.cost_usd
        else:
            s.own_usd = s.cost_usd


def read_all(roots: list[Path], project: str | None, since: datetime | None, measure_dir: Path) -> list[Session]:
    """Every session over the roots, linked, then those of the project and the period asked for. A
    session's predecessor may lie outside them, so all are read before any is left out."""
    sessions = [read_session(path) for path in transcript_paths(roots)]
    link(sessions, timeline_links(measure_dir))
    kept = [
        s for s in sessions
        if (not project or project in s.path.parent.name) and not (since and (s.started is None or s.started < since))
    ]
    kept.sort(key=lambda s: s.started or datetime.min.replace(tzinfo=timezone.utc))
    return kept
