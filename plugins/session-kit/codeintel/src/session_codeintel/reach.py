"""What the engine's validator names, graded: the 2.1.308 release's vocabulary.

Every member of ``$`` with the reach its declaration supports, what a hook
on each event sees and what a reviewer reads it for, and the kinds of note
the validator prints. Each moves with a Claude Code release: a member the
table lacks is named unclassified, and a note of a kind it lacks is shown
as the validator printed it.
"""

from __future__ import annotations

from session_codeintel import footprint

LEVELS = ("draws and remembers", "reads", "writes, runs or drives Claude", "reaches the network")
REACH: tuple[tuple[str, int, tuple[str, ...]], ...] = (
    ("network", 3, ("http.fetch",)),
    ("MCP servers", 3, ("mcp.call", "mcp.connect")),
    ("runs processes", 2, ("process.run", "process.spawn")),
    ("writes files", 2, ("fs.write",)),
    ("sets env vars", 2, ("env.set",)),
    ("changes config", 2, ("config.set",)),
    ("calls a model", 2, ("model.complete", "model.fork", "model.classify")),
    (
        "drives the session",
        2,
        (
            "session.compact",
            "session.send",
            "session.append",
            "turn.abort",
            "prompt.submit",
            "tool.call",
            "tool.register",
            "command.run",
            "agent.spawn",
            "agent.register",
        ),
    ),
    ("writes the prompt box", 1, ("prompt.fill", "prompt.suggest")),
    ("writes the clipboard", 1, ("ui.copy",)),
    ("holds the Anthropic credential", 1, ("session.authorize",)),
    ("reads the sign-in", 1, ("session.identity",)),
    (
        "reads files",
        1,
        ("fs.read", "fs.list", "fs.exists", "fs.stat", "fs.ancestors", "session.repo"),
    ),
    ("reads env vars", 1, ("env.get",)),
    ("reads settings", 1, ("settings.read", "config.list")),
    ("reads the transcript", 1, ("session.messages",)),
    ("reads the system prompt", 1, ("prompt.compose",)),
    ("reads the prompt box", 1, ("prompt.read",)),
    ("reads the prompt's attachments", 1, ("prompt.media",)),
    ("reads the selection", 1, ("ui.selection",)),
    ("reads plugins' state", 1, ("state.get",)),
    ("telemetry", 1, ("telemetry.log", "telemetry.mark")),
    ("runs a timer", 0, ("clock.every",)),
    ("plays audio", 0, ("audio.play", "audio.speak")),
    ("keeps a store", 0, ("store.get", "store.set", "store.delete", "store.keys")),
    (
        "draws",
        0,
        (
            "ui.notice",
            "ui.invalidate",
            "ui.blit",
            "ui.resolve",
            "ui.log",
            "ui.ask",
            "ui.toast",
            "ui.notify",
            "ui.status",
            "ui.open",
            "ui.close",
            "ui.panes",
            "ui.scroll",
            "ui.focus",
            "ui.view",
        ),
    ),
    (
        "",
        0,
        (
            "plugin.name",
            "plugin.root",
            "session.cwd",
            "session.root",
            "session.model",
            "session.turns",
            "session.id",
            "session.surfaces",
            "session.surface",
            "session.usage",
            "session.version",
            "tool.list",
            "tool.check",
            "command.list",
            "command.register",
            "agent.list",
            "state.set",
            "clock.now",
            "clock.sleep",
            "clock.after",
        ),
    ),
)
"""Every member of ``$`` in the 2.1.308 type declarations, widest reach first, by our reading."""
MEMBERS = {member: (level, label) for label, level, found in REACH for member in found}
ORDER = [label for label, _, _ in REACH]

EVENTS = {
    "tool.call": "the tool calls it matches: read whether it approves, refuses or rewrites one",
    "tool.check": "the permission decisions: read whether it answers one",
    "prompt.submit": "every prompt: read whether it rewrites or drops one",
    "prompt.compose": "the system prompt: read whether it changes it",
    "prompt.context": "the context beside each prompt: read what it adds",
    "prompt.section": "the system prompt's sections: read whether it changes one",
    "session.append": "the rows the transcript keeps: read whether it changes one",
    "session.compact": "every compaction: read whether it changes or skips one",
    "turn.step": "every model request: read whether it changes the model, the effort or the stream",
    "ui.render": "what the surfaces draw: read whether it passes on what it does not draw",
    "telemetry.log": "the telemetry records it matches",
    "agent.spawn": "every subagent's start: read whether it changes or refuses one",
    "command.run": "the slash commands it matches",
}
"""What a hook on each event sees, and what the reviewer reads it for."""
UNMATCHED_HOT = frozenset(
    {
        "tool.call",
        "tool.check",
        "classic.PreToolUse",
        "classic.PostToolUse",
        "classic.PostToolUseFailure",
    }
)
KINDS = (
    "hooks telemetry for",
    "gating hook with .catch",
    "gating hook without .catch",
    "hooks",
    "calls",
    "env reads",
    "env writes",
    "state reads",
    "state writes",
    "declares on $",
    "declares state",
)
"""The validator's notes by the words that end their head, a longer end before a shorter."""

SETTINGS_EVENT = "the settings hooks' event of that name"
HOT = frozenset({"turn.step", "ui.render", "*"})


def kind_of(head: str) -> tuple[str, str]:
    """Split a note's head into its subject and its kind; the kind is empty when unknown."""
    for kind in KINDS:
        if head == kind or head.endswith(f" {kind}"):
            return head[: -len(kind)].strip(), kind
    return head, ""


def hot(event: str, matcher: str) -> bool:
    """Whether a hook runs on nearly every step: drawing, each request, every tool call."""
    return event in HOT or "*" in event or (event in UNMATCHED_HOT and not matcher)


def note(event: str) -> str:
    """Return what a hook on the event sees and what to read it for; empty when unknown."""
    if event in EVENTS:
        return EVENTS[event]
    return SETTINGS_EVENT if event.startswith("classic.") else ""


def graded(found: dict[str, tuple[str, ...]]) -> tuple[list[tuple[str, str, int, str]], list[str]]:
    """Grade every call: member, the functions it is made through, level and label."""
    calls: list[tuple[str, str, int, str]] = []
    unclassified: list[str] = []
    for head, listed in found.items():
        if kind_of(head)[1] != "calls":
            continue
        for item in listed:
            if footprint.CUT.search(item):
                continue
            member, _, via = item.partition(" (via ")
            rule = MEMBERS.get(member.removeprefix("$."))
            if rule is None:
                unclassified.append(member)
                continue
            calls.append((member, via.removesuffix(")"), *rule))
    calls.sort(key=lambda c: (-c[2], ORDER.index(c[3]), c[0]))
    return calls, sorted(set(unclassified))
