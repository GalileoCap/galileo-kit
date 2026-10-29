"""The reader over the sessions' transcripts.

Each session leaves one JSONL file under ``~/.claude/projects/<project>/``,
read by ``records.py``. This command prints tables: ``list`` (one row per
session), ``session <id>`` (the context at each request, the warnings, the
compactions, where it came from), ``warnings`` (each context warning and
what followed it), ``cache`` (the share of input read from the prompt cache
and the cold sends), ``compactions`` (by trigger, with the context each ran
over), ``hooks`` (each settings hook's fires by name), ``chains`` (the
sessions a clear, a resume, a fork or one running cost joined), ``waste`` (what
a session read or ran again, a compaction's price in reads among it),
``asks`` (the person's asks that recur), ``report`` (those tables but
the asks written to a markdown file under ``docs/measurements/``), and
``week`` (the owner's week against their window, ``week.py``).

It prints counts, sizes, names of hooks and tools, and the hooks' own text.
It prints no prompt and no answer unless ``asks --quote`` is asked for, and
writes nothing outside the file ``report`` is given and the review ``week``
writes beside the hold's settings, of which it prints the path alone.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from fractions import Fraction
from pathlib import Path

import week
from records import COLD_GAP_MINUTES, COLD_SHARE, Ask, Compaction, Session, Waste, read_all

MEASURE_DIR = Path.home() / ".claude" / "session-kit" / "measure"
# Two prompts are one ask when this share of their words, against all the words of both, is the same.
ASK_LIKENESS = Fraction(7, 10)
ASK_QUOTE_CHARS = 80


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
        own_cost(s),
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


def warnings_summary(sessions: list[Session]) -> str:
    """One row per session that was warned, for the report: the per-warning rows are the `warnings` command's."""
    rows: list[list[str]] = []
    total = handoffs = compactions = 0
    all_tokens: list[int] = []
    for s in sessions:
        if not s.warnings:
            continue
        n = len(s.warnings)
        total += n
        with_handoff = sum(w.handoff_turns is not None for w in s.warnings)
        with_compaction = sum(w.compaction_turns is not None for w in s.warnings)
        handoffs += with_handoff
        compactions += with_compaction
        all_tokens += [w.tokens for w in s.warnings]
        later = sorted(w.compaction_turns for w in s.warnings if w.compaction_turns is not None)
        rows.append([
            short(s.id), project_name(s.project), day(s.started), str(n), f"{min(w.tokens for w in s.warnings):,}",
            str(with_handoff), str(sum(w.commit_turns is not None for w in s.warnings)), str(with_compaction),
            str(later[len(later) // 2]) if later else "none",
        ])
    body = table(["Session", "Project", "Started", "Warnings", "First at", "Followed by a handoff", "By a commit", "By a compaction", "Median turns to the compaction"], rows)
    if not all_tokens:
        return f"{body}\n\nNo warning fired."
    all_tokens.sort()
    return (
        f"{body}\n\n{total} warnings over {len(rows)} sessions, from {all_tokens[0]:,} tokens, median {all_tokens[len(all_tokens) // 2]:,}. "
        f"{handoffs} were followed by a handoff and {compactions} by a compaction in the same session."
    )


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




def own_cost(s: Session) -> str:
    return f"{s.own_usd:.2f}" if s.own_usd is not None else "?"


def chains(sessions: list[Session]) -> list[list[Session]]:
    """The sessions ``link`` joined, each chain its first session read, then the rest in the order they
    started. A session nothing came from or went on from is in none."""
    by_id = {s.id: s for s in sessions}
    order = {s.id: i for i, s in enumerate(sessions)}
    after: defaultdict[str, list[Session]] = defaultdict(list)
    for s in sessions:
        if s.came_from in by_id:
            after[str(s.came_from)].append(s)
    found: list[list[Session]] = []
    for s in sessions:
        if s.came_from in by_id or s.id not in after:
            continue
        members: list[Session] = []
        stack = [s]
        while stack:
            m = stack.pop()
            members.append(m)
            stack.extend(after[m.id])
        found.append([s] + sorted(members[1:], key=lambda m: order[m.id]))
    return found


def chains_table(sessions: list[Session]) -> str:
    rows: list[list[str]] = []
    for chain in chains(sessions):
        costs = [m.own_usd for m in chain]
        ends = [m.ended for m in chain if m.ended is not None]
        joined = Counter(str(m.how) for m in chain[1:])
        rows.append([
            short(chain[0].id), str(len(chain)), ", ".join(sorted({project_name(m.project) for m in chain})),
            day(chain[0].started), day(max(ends)) if ends else "?",
            str(sum(m.prompts for m in chain)), str(sum(len(m.requests) for m in chain)), str(sum(len(m.compactions) for m in chain)),
            f"{sum(c for c in costs if c is not None):.2f}" if None not in costs else "?",
            ", ".join(f"{how} {n}" for how, n in sorted(joined.items())),
        ])
    body = table(["Chain", "Sessions", "Project", "First day", "Last day", "Prompts", "Requests", "Compactions", "USD", "Joined by"], rows)
    return (
        f"{body}\n\nA chain is the sessions joined by a clear or a resume (session-kit's timeline names the session before), "
        "a fork (its file begins with a copy of its parent's records) or one running cost (their cost states share a start, each running on from the total of the one before). "
        "Its cost is the sum of each session's own."
    )


WASTE_HEADERS = ["Read again after a compaction", "Chars", "Of them edited before it", "Unchanged in context", "Chars", "Repeated output", "Chars"]


def waste_cells(w: Waste) -> list[str]:
    return [str(w.again), f"{w.again_chars:,}", str(w.again_edited), str(w.unchanged), f"{w.unchanged_chars:,}", str(w.repeated), f"{w.repeated_chars:,}"]


def summed(sessions: list[Session]) -> Waste:
    total = Waste()
    for s in sessions:
        w = s.waste
        total.reads += w.reads
        total.read_chars += w.read_chars
        total.again += w.again
        total.again_chars += w.again_chars
        total.again_edited += w.again_edited
        total.unchanged += w.unchanged
        total.unchanged_chars += w.unchanged_chars
        total.repeated += w.repeated
        total.repeated_chars += w.repeated_chars
        total.again_by_compaction += w.again_by_compaction
    return total


def waste_summary(sessions: list[Session]) -> str:
    total = summed(sessions)
    share = total.again_chars / total.read_chars if total.read_chars else None
    lines = [
        f"Of {total.read_chars:,} characters read by {total.reads:,} Read calls, {total.again_chars:,} ({pct(share)}) came from "
        f"{total.again:,} reads after a compaction of a file an earlier context of the session had read, {total.again_edited:,} of them "
        f"a file edited before it. Reads of a file unchanged since the read before it in the same context: {total.unchanged:,}, "
        f"{total.unchanged_chars:,} characters. Other calls that returned again, in one context, the output they had returned: "
        f"{total.repeated:,}, {total.repeated_chars:,} characters."
    ]
    after = sorted(total.again_by_compaction)
    if after:
        lines.append(f"After each of {len(after):,} compactions, the characters read again: median {after[len(after) // 2]:,}, largest {after[-1]:,}.")
    lines.append(
        "The global rules ask for the documents the work rests on to be read again after a compaction, so the reads again after one "
        "are its price in reads, and an edited file among them is one whose state the summary did not carry."
    )
    return "\n\n".join(lines)


def waste_table(sessions: list[Session]) -> str:
    rows = [
        [short(s.id), project_name(s.project), str(len(s.compactions)), str(s.waste.reads)] + waste_cells(s.waste)
        for s in sessions if s.waste.any
    ]
    return table(["Session", "Project", "Compactions", "Reads"] + WASTE_HEADERS, rows) + "\n\n" + waste_summary(sessions)


def waste_by_project(sessions: list[Session]) -> str:
    by_project: dict[str, list[Session]] = {}
    for s in sessions:
        by_project.setdefault(s.project, []).append(s)
    rows: list[list[str]] = []
    for project, group in by_project.items():
        total = summed(group)
        if total.reads or total.any:
            rows.append([project_name(project), str(len(group)), str(sum(len(s.compactions) for s in group)), str(total.reads)] + waste_cells(total))
    return table(["Project", "Sessions", "Compactions", "Reads"] + WASTE_HEADERS, rows) + "\n\n" + waste_summary(sessions)


def ask_words(text: str) -> frozenset[str]:
    """An ask's words, lower-cased, each run of digits the same word."""
    return frozenset(re.findall(r"\w+", re.sub(r"\d+", "0", text.lower())))


def group_asks(words: list[frozenset[str]]) -> list[int]:
    """Each ask's group: two asks whose shared words are ``ASK_LIKENESS`` or more of the words of both are one, and so is
    a run of such pairs. The pairs are found through a prefix of each ask's rarest words, which any two that alike share."""
    rarity = Counter(w for ws in words for w in ws)
    parent = list(range(len(words)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    index: defaultdict[str, list[int]] = defaultdict(list)
    for i in sorted(range(len(words)), key=lambda i: len(words[i])):
        ws = words[i]
        if not ws:
            continue
        prefix = sorted(ws, key=lambda w: (rarity[w], w))[: len(ws) - math.ceil(ASK_LIKENESS * len(ws)) + 1]
        for j in {j for w in prefix for j in index[w]}:
            if Fraction(len(ws & words[j]), len(ws | words[j])) >= ASK_LIKENESS:
                parent[root(i)] = root(j)
        for w in prefix:
            index[w].append(i)
    return [root(i) for i in range(len(words))]


def quoted(text: str) -> str:
    flat = " ".join(text.split())
    cut = flat[:ASK_QUOTE_CHARS] + ("..." if len(flat) > ASK_QUOTE_CHARS else "")
    return cut.replace("|", "\\|")


def asks_table(sessions: list[Session], top: int, quote: bool) -> str:
    asks = [(s, a) for s in sessions for a in s.asks]
    groups: defaultdict[int, list[tuple[Session, Ask]]] = defaultdict(list)
    for (s, a), g in zip(asks, group_asks([ask_words(a.text) for _, a in asks])):
        groups[g].append((s, a))
    ranked = sorted((m for m in groups.values() if len(m) > 1), key=lambda m: (-len(m), -len({s.id for s, _ in m})))
    rows: list[list[str]] = []
    for rank, members in enumerate(ranked[:top], 1):
        times = sorted(a.at for _, a in members if a.at is not None)
        lengths = sorted(len(a.text.split()) for _, a in members)
        row = [
            str(rank), str(len(members)), str(len({s.id for s, _ in members})), str(len({s.project for s, _ in members})),
            str(lengths[len(lengths) // 2]), day(times[0]) if times else "?", day(times[-1]) if times else "?",
        ]
        if quote:
            row.append(quoted(Counter(" ".join(a.text.split()) for _, a in members).most_common(1)[0][0]))
        rows.append(row)
    headers = ["Rank", "Prompts", "Sessions", "Projects", "Words", "First", "Last"] + (["Ask"] if quote else [])
    return (
        f"{table(headers, rows)}\n\n{len(asks):,} prompts of the person's over {len(sessions)} sessions, {len(ranked):,} asks made more than once. "
        f"Two prompts are one ask when {int(ASK_LIKENESS * 100)}% or more of the words of both are shared. "
        "A plugin's prompt, a notification and a command are not the person's ask. `--quote` prints each ask's words."
    )


def session_report(s: Session, sessions: list[Session]) -> str:
    out = [f"Session {s.id} in {project_name(s.project)}, started {day(s.started)}: {s.prompts} prompts, {len(s.requests)} requests, "
           f"{len(s.compactions)} compactions, cache share {pct(s.cache_share)}" + (f", {s.own_usd:.2f} USD of its own" if s.own_usd is not None else "") + ".", ""]
    if s.came_from is not None:
        out += [f"Came from {short(s.came_from)} ({s.how}).", ""]
    went_on = [f"{short(o.id)} ({o.how})" for o in sessions if o.came_from == s.id]
    if went_on:
        out += ["Went on in " + ", ".join(went_on) + ".", ""]
    rows = [[str(r.turn), r.at.strftime("%H:%M"), f"{r.context:,}", f"{r.read:,}", f"{r.created:,}", f"{r.out:,}", r.model] for r in s.requests]
    out.append(table(["Turn", "Time", "Context", "Read from cache", "Written to cache", "Output", "Model"], rows))
    if s.compactions:
        out += ["", "Compactions:", "", table(["Turn", "Time", "Trigger", "Tokens before", "Seconds"],
                [[str(c.turn), c.at.strftime("%H:%M"), c.trigger, f"{c.pre_tokens:,}", f"{c.duration_ms / 1000:.0f}"] for c in s.compactions])]
    if s.warnings:
        out += ["", "Warnings:", "", table(["Turn", "Tokens", "Window", "Handoff", "Commit", "Compaction"],
                [[str(w.turn), f"{w.tokens:,}", f"{w.percent}%", followed(w.handoff_turns, "after"), followed(w.commit_turns, "after"), followed(w.compaction_turns, "after")] for w in s.warnings])]
    if s.waste.any:
        w = s.waste
        out += ["", f"Read again after its compactions: {w.again} reads, {w.again_chars:,} characters ({w.again_edited} of them edited files). "
                f"Read again unchanged in one context: {w.unchanged}, {w.unchanged_chars:,} characters. Repeated output: {w.repeated}, {w.repeated_chars:,} characters."]
    if s.tools:
        out += ["", "Tool calls: " + ", ".join(f"{name} {n}" for name, n in sorted(s.tools.items(), key=lambda kv: -kv[1]))]
    if s.hooks:
        out += ["", "Hooks: " + ", ".join(f"{name} {n}" for name, n in sorted(s.hooks.items()))]
    return "\n".join(out)


def full_report(sessions: list[Session], roots: list[Path], since: datetime | None) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    scope = f"since {since.date().isoformat()}" if since else "all"
    where = " and ".join(f"`{r}`" for r in roots)
    archived = sum(1 for s in sessions if s.path.name.endswith(".tar.xz"))
    return "\n".join([
        f"# Sessions read on {today}",
        "",
        f"Written by `session-transcripts report` over {where} ({scope}): {len(sessions)} sessions, {archived} of them from an archive. Counts and sizes only, no prompt and no answer.",
        "",
        "## Sessions",
        "",
        "A session's cost is its own: the engine's running total, less what it carried from the session whose total it ran on from or the parent it was forked from.",
        "",
        list_table(sessions),
        "",
        "## Warnings",
        "",
        "Each session the kit warned about its context, with what followed in the same session. `session-transcripts warnings` lists every warning.",
        "",
        warnings_summary(sessions),
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
        "## Chains",
        "",
        chains_table(sessions),
        "",
        "## Waste",
        "",
        "What the sessions read or ran again, by project. `session-transcripts waste` lists each session.",
        "",
        waste_by_project(sessions),
        "",
        "## Hooks",
        "",
        hooks_table(sessions),
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="The reader over the sessions' transcripts.")
    parser.add_argument("command", choices=("list", "session", "warnings", "cache", "compactions", "hooks", "chains", "waste", "asks", "report", "week"))
    parser.add_argument("id", nargs="?", help="the session id, for `session`")
    parser.add_argument("--root", default=os.path.expanduser("~/.claude/projects"))
    parser.add_argument("--archive", action="append", default=[], help="a directory of archived sessions, `<project>/<id>.tar.xz`, read beside the root; repeatable")
    parser.add_argument("--measure-dir", default=str(MEASURE_DIR), help="session-kit's timeline, whose first line after a clear or a resume names the session before")
    parser.add_argument("--project", help="keep the project folders whose name holds this text")
    parser.add_argument("--since", help="keep the sessions started on or after this date (YYYY-MM-DD)")
    parser.add_argument("--top", type=int, default=20, help="for `asks`: how many asks to rank")
    parser.add_argument("--quote", action="store_true", help="for `asks`: print each ask's words, which are the person's own")
    parser.add_argument("--out", help="for `report`: the file to write; default docs/measurements/sessions-<date>.md")
    parser.add_argument("--week", help="for `week`: the last day of the review (YYYY-MM-DD), its Monday the first; default today")
    parser.add_argument("--load-dir", default=str(week.LOAD_DIR), help="for `week`: the hold's settings and log, where the review is written")
    args = parser.parse_args()
    roots = [Path(args.root)] + [Path(a) for a in args.archive]
    for root in roots:
        if not root.is_dir():
            print(f"{root}: no such directory")
            return 2
    measure = Path(args.measure_dir).expanduser()
    since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc) if args.since else None
    if args.command == "session":
        if not args.id:
            print("session takes the session id")
            return 2
        everyone = read_all(roots, args.project, None, measure)
        matches = [s for s in everyone if s.id.startswith(args.id)]
        if len(matches) != 1:
            print(f"{len(matches)} sessions match {args.id}")
            return 1
        print(session_report(matches[0], everyone))
        return 0
    if args.command == "week":
        as_of = date.fromisoformat(args.week) if args.week else date.today()
        return week.write(read_all(roots, args.project, None, measure), Path(args.load_dir).expanduser(), as_of, str(Path.home()))
    sessions = read_all(roots, args.project, since, measure)
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
    elif args.command == "chains":
        print(chains_table(sessions))
    elif args.command == "waste":
        print(waste_table(sessions))
    elif args.command == "asks":
        print(asks_table(sessions, args.top, args.quote))
    else:
        out = Path(args.out) if args.out else Path("docs/measurements") / f"sessions-{datetime.now(timezone.utc).date().isoformat()}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(full_report(sessions, roots, since), encoding="utf-8")
        print(f"{out}: {len(sessions)} sessions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
