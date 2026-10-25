"""The reader over the sessions' transcripts.

Each session leaves one JSONL file under ``~/.claude/projects/<project>/``.
This command reads them locally and prints tables: ``list`` (one row per
session), ``session <id>`` (the context at each request, the warnings, the
compactions), ``warnings`` (each context warning and what followed it),
``cache`` (the share of input read from the prompt cache and the cold
sends), ``compactions`` (by trigger, with the context each ran over), ``hooks`` (each settings hook's fires by name), and ``report``
(those tables written to a markdown file under ``docs/measurements/``).

It prints counts, sizes, names of hooks and tools, and the hooks' own text.
It prints no prompt and no answer, and writes nothing outside the file
``report`` is given.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

WARNING = re.compile(r"Context at ([\d,]+) tokens \((\d+)% of")
HANDOFF_PATH = re.compile(r"CLAUDE\.local\.md$")
COMMIT = re.compile(r"(^|[;&|]\s*)git\s+commit\b")
COLD_GAP_MINUTES = 5
COLD_SHARE = 0.5
HOOK_ATTACHMENTS = ("hook_success", "hook_additional_context", "hook_system_message")


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
class Session:
    id: str
    project: str
    path: Path
    started: datetime | None = None
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


def read_session(path: Path) -> Session:
    session = Session(id=path.stem, project=path.parent.name, path=path)
    seen_requests: set[str] = set()
    turn = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict):
                continue
            kind = r.get("type")
            at = when(r.get("timestamp"))
            if at is not None and session.started is None:
                session.started = at
            sidechain = r.get("isSidechain") is True
            message = r.get("message") if isinstance(r.get("message"), dict) else {}
            content = message.get("content")
            if kind == "user" and not sidechain:
                is_prompt = isinstance(content, str) or (
                    isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "text" for b in content)
                ) and not r.get("isMeta") and not r.get("isCompactSummary")
                if is_prompt and not r.get("toolUseResult"):
                    turn += 1
                    session.prompts += 1
                if isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "tool_result":
                            note_warnings(session, texts_of(b.get("content")), at, turn)
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
                for w in session.warnings:
                    if w.compaction_turns is None:
                        w.compaction_turns = turn - w.turn
            elif kind == "cost-state":
                session.cost_usd = float(r.get("totalCostUSD") or 0)
                session.lines_added = int(r.get("totalLinesAdded") or 0)
                session.lines_removed = int(r.get("totalLinesRemoved") or 0)
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


def read_all(root: Path, project: str | None, since: datetime | None) -> list[Session]:
    sessions: list[Session] = []
    for path in sorted(root.glob("*/*.jsonl")):
        if project and project not in path.parent.name:
            continue
        s = read_session(path)
        if since and (s.started is None or s.started < since):
            continue
        sessions.append(s)
    sessions.sort(key=lambda s: s.started or datetime.min.replace(tzinfo=timezone.utc))
    return sessions


def short(session_id: str) -> str:
    return session_id[:8]


def project_name(folder: str) -> str:
    return folder.rsplit("-", 2)[-2] + "-" + folder.rsplit("-", 1)[-1] if folder.count("-") > 2 else folder


def day(at: datetime | None) -> str:
    return at.date().isoformat() if at else "?"


def pct(share: float | None) -> str:
    return f"{share * 100:.0f}%" if share is not None else "?"


def table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    out += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(out)


def list_table(sessions: list[Session]) -> str:
    rows = [[
        short(s.id), project_name(s.project), day(s.started), str(s.prompts), str(len(s.requests)),
        f"{max((r.context for r in s.requests), default=0):,}", pct(s.cache_share), str(len(s.compactions)),
        f"{s.cost_usd:.2f}" if s.cost_usd is not None else "?",
    ] for s in sessions]
    return table(["Session", "Project", "Started", "Prompts", "Requests", "Largest context", "Cache share", "Compactions", "USD"], rows)


def followed(turns: int | None, what: str) -> str:
    return f"{what} {turns}" if turns is not None else f"{what} none"


def warnings_table(sessions: list[Session]) -> str:
    rows: list[list[str]] = []
    total = handoffs = 0
    for s in sessions:
        for w in s.warnings:
            total += 1
            handoffs += w.handoff_turns is not None
            rows.append([
                short(s.id), project_name(s.project), day(w.at), str(w.turn), f"{w.tokens:,}", f"{w.percent}%",
                followed(w.handoff_turns, "handoff"), followed(w.commit_turns, "commit"), followed(w.compaction_turns, "compaction"),
            ])
    body = table(["Session", "Project", "Day", "Turn", "Tokens", "Window", "Handoff (turns later)", "Commit", "Compaction"], rows)
    return f"{body}\n\n{handoffs} of {total} warnings were followed by a handoff in the same session."


def cache_table(sessions: list[Session]) -> str:
    rows: list[list[str]] = []
    by_project: dict[str, list[Session]] = {}
    for s in sessions:
        by_project.setdefault(s.project, []).append(s)
        cold = s.cold_sends()
        rows.append([
            short(s.id), project_name(s.project), day(s.started), str(len(s.requests)), pct(s.cache_share),
            f"{sum(r.created for r in s.requests):,}", str(len(cold)), f"{sum(r.created for r in cold):,}",
        ])
    per_session = table(["Session", "Project", "Started", "Requests", "Cache share", "Written to cache", "Cold sends", "Written cold"], rows)
    project_rows: list[list[str]] = []
    for project, group in by_project.items():
        requests = [r for s in group for r in s.requests]
        total = sum(r.context for r in requests)
        share = sum(r.read for r in requests) / total if total else None
        cold = [r for s in group for r in s.cold_sends()]
        project_rows.append([project_name(project), str(len(group)), str(len(requests)), pct(share), str(len(cold)), f"{sum(r.created for r in cold):,}"])
    per_project = table(["Project", "Sessions", "Requests", "Cache share", "Cold sends", "Written cold"], project_rows)
    return (
        f"{per_session}\n\nPer project:\n\n{per_project}\n\n"
        f"A cold send is a request more than {COLD_GAP_MINUTES} minutes after the previous one that wrote at least "
        f"{COLD_SHARE:.0%} of its context to the cache."
    )


def compactions_table(sessions: list[Session]) -> str:
    by_trigger: dict[str, list[Compaction]] = {}
    for s in sessions:
        for c in s.compactions:
            by_trigger.setdefault(c.trigger, []).append(c)
    rows: list[list[str]] = []
    for trigger, group in sorted(by_trigger.items()):
        sizes = sorted(c.pre_tokens for c in group)
        median = sizes[len(sizes) // 2]
        seconds = sorted(c.duration_ms for c in group)[len(group) // 2] / 1000
        rows.append([trigger, str(len(group)), f"{sizes[0]:,}", f"{median:,}", f"{sizes[-1]:,}", f"{seconds:.0f}"])
    largest = max((r.context for s in sessions for r in s.requests), default=0)
    return (
        table(["Trigger", "Compactions", "Smallest before", "Median before", "Largest before", "Median seconds"], rows)
        + f"\n\nThe largest context any request carried: {largest:,} tokens."
    )


def hooks_table(sessions: list[Session]) -> str:
    fires: dict[str, int] = {}
    chars: dict[str, int] = {}
    in_sessions: dict[str, int] = {}
    for s in sessions:
        for name, n in s.hooks.items():
            fires[name] = fires.get(name, 0) + n
            chars[name] = chars.get(name, 0) + s.hook_chars.get(name, 0)
            in_sessions[name] = in_sessions.get(name, 0) + 1
    rows = [[name, str(fires[name]), str(in_sessions[name]), f"{chars[name] // max(fires[name], 1):,}"] for name in sorted(fires)]
    return table(["Hook", "Fires", "Sessions", "Chars per fire"], rows)


def session_report(s: Session) -> str:
    out = [f"Session {s.id} in {project_name(s.project)}, started {day(s.started)}: {s.prompts} prompts, {len(s.requests)} requests, "
           f"{len(s.compactions)} compactions, cache share {pct(s.cache_share)}" + (f", {s.cost_usd:.2f} USD" if s.cost_usd is not None else "") + ".", ""]
    rows = [[str(r.turn), r.at.strftime("%H:%M"), f"{r.context:,}", f"{r.read:,}", f"{r.created:,}", f"{r.out:,}", r.model] for r in s.requests]
    out.append(table(["Turn", "Time", "Context", "Read from cache", "Written to cache", "Output", "Model"], rows))
    if s.compactions:
        out += ["", "Compactions:", "", table(["Turn", "Time", "Trigger", "Tokens before", "Seconds"],
                [[str(c.turn), c.at.strftime("%H:%M"), c.trigger, f"{c.pre_tokens:,}", f"{c.duration_ms / 1000:.0f}"] for c in s.compactions])]
    if s.warnings:
        out += ["", "Warnings:", "", table(["Turn", "Tokens", "Window", "Handoff", "Commit", "Compaction"],
                [[str(w.turn), f"{w.tokens:,}", f"{w.percent}%", followed(w.handoff_turns, "after"), followed(w.commit_turns, "after"), followed(w.compaction_turns, "after")] for w in s.warnings])]
    if s.tools:
        out += ["", "Tool calls: " + ", ".join(f"{name} {n}" for name, n in sorted(s.tools.items(), key=lambda kv: -kv[1]))]
    if s.hooks:
        out += ["", "Hooks: " + ", ".join(f"{name} {n}" for name, n in sorted(s.hooks.items()))]
    return "\n".join(out)


def full_report(sessions: list[Session], root: Path, since: datetime | None) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    scope = f"since {since.date().isoformat()}" if since else "all"
    return "\n".join([
        f"# Sessions read on {today}",
        "",
        f"Written by `session-transcripts report` over `{root}` ({scope}): {len(sessions)} sessions. Counts and sizes only, no prompt and no answer.",
        "",
        "## Sessions",
        "",
        list_table(sessions),
        "",
        "## Warnings",
        "",
        "Each context warning the kit gave the model, and how many turns later the handoff, a commit and a compaction came, in the same session.",
        "",
        warnings_table(sessions),
        "",
        "## Cache",
        "",
        cache_table(sessions),
        "",
        "## Compactions",
        "",
        "Every compaction, by what triggered it, with the context it ran over.",
        "",
        compactions_table(sessions),
        "",
        "## Hooks",
        "",
        hooks_table(sessions),
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="The reader over the sessions' transcripts.")
    parser.add_argument("command", choices=("list", "session", "warnings", "cache", "compactions", "hooks", "report"))
    parser.add_argument("id", nargs="?", help="the session id, for `session`")
    parser.add_argument("--root", default=os.path.expanduser("~/.claude/projects"))
    parser.add_argument("--project", help="keep the project folders whose name holds this text")
    parser.add_argument("--since", help="keep the sessions started on or after this date (YYYY-MM-DD)")
    parser.add_argument("--out", help="for `report`: the file to write; default docs/measurements/sessions-<date>.md")
    args = parser.parse_args()
    root = Path(args.root)
    if not root.is_dir():
        print(f"{root}: no such directory")
        return 2
    since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc) if args.since else None
    if args.command == "session":
        if not args.id:
            print("session takes the session id")
            return 2
        matches = [s for s in read_all(root, args.project, None) if s.id.startswith(args.id)]
        if len(matches) != 1:
            print(f"{len(matches)} sessions match {args.id}")
            return 1
        print(session_report(matches[0]))
        return 0
    sessions = read_all(root, args.project, since)
    if args.command == "list":
        print(list_table(sessions))
    elif args.command == "warnings":
        print(warnings_table(sessions))
    elif args.command == "cache":
        print(cache_table(sessions))
    elif args.command == "compactions":
        print(compactions_table(sessions))
    elif args.command == "hooks":
        print(hooks_table(sessions))
    else:
        out = Path(args.out) if args.out else Path("docs/measurements") / f"sessions-{datetime.now(timezone.utc).date().isoformat()}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(full_report(sessions, root, since), encoding="utf-8")
        print(f"{out}: {len(sessions)} sessions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
