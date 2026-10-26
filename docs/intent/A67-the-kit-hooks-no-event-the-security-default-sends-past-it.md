---
id: A67
from: [O12, O17, C2]
source: owner
status: decided 2026-10-26
kind: behaviour
implemented_by: [plugins/session-kit/hooks/measure.ts, plugins/session-kit/hooks/context.tsx, plugins/session-kit/footprint.toml, plugins/session-kit/.claude-plugin/plugin.json]
proven_by: [plugins/session-kit/footprint.toml]
supersedes: [A18]
---

# A67 The kit hooks no event the security default sends past it

The kit registers no hook on an event that the organization's security default (`C2`) sends past the plugins a person installs. Four hooks are removed in session-kit 0.35.2:

- `measure.ts`'s `classic.PostToolUse` and `classic.PostToolUseFailure`, which wrote the timeline's `tool.exec` line. No reader used that line, and it was last recorded on 2026-10-25. The time beneath the kit stays on each tool call's line (`A55`, a timeline of turns and tool calls with the kit's time per concern).
- `context.tsx`'s `session.compact` hook on the auto trigger, the backstop of `A18` (a backstop for the engine's own compaction), which this entry retires. The engine's own compaction runs with its own instructions, and the chain's `/compact` (`A61`, the chain compacts through /compact in every session) carries the handoff's.
- `context.tsx`'s `classic.PostModelSwitch`, from which the cold-cache timer (`A49`) took the cache's lifetime. The timer takes it from the `cacheMinutes` option and from a subagent's result.

## Context

The owner saw "its classic.PostToolUse hook was skipped. "cc-plugin-sec-default" runs first and sent the event on past it." in tagents' dev session and in this repository's session. The transcripts of 2026-10-26 held the same notice for `session.compact`, 372 times across sessions.

## Options

- Remove the hooks. Taken, by the owner's word. Each hook was dead on this machine and cost a notice in each session's context.
- Keep them for a machine where the default is not seated. Rejected: every machine the owner runs the kit on is under the same account.
- Move the default from the outermost seat through `prependPlugins` in user settings. Rejected: it weakens a security default the organization chose.

## Consequences

A summary the engine writes at its own threshold keeps what the engine's instructions ask for, and the handoff's fields reach it only through `CLAUDE.md` and the handoff file. After a model switch to a different cache lifetime the cold-cache timer goes on with the option's until a subagent's result states one. Should the organization stop seating the default, these hooks could come back under a new action.

## Proof

`plugins/session-kit/footprint.toml`, held by `session-codeintel footprint`, lists every hook the kit registers, and none of the four is in it. 69 engine tests passed on 2.1.308, the cold-cache tests rewritten on subagent results.
