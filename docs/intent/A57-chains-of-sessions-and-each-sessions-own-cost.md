---
id: A57
from: [O17]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/transcripts/records.py, plugins/session-kit/transcripts/session_transcripts.py]
proven_by: [plugins/session-kit/transcripts/test_session_transcripts.py, docs/measurements/sessions-2026-10-25-deduplicated-with-archive.md]
supersedes: []
---

# A57 Chains of sessions, and each session's own cost

`session-transcripts chains` joins the sessions one piece of work was split across, and every table prints a session's own cost. A session came from another in one of three ways, tried in this order. The timeline of `A55` (a timeline of turns and tool calls with the kit's time per concern) opens the first file of a session a clear or a resume started with a line naming the session before it. A fork's transcript begins with a copy of its parent's records under the parent's id. And a session whose cost state shares its start with others came after the one of them that ended last before it began, a minute's slack allowed: its cost runs on from that one's. A chain is a session nothing read came from, with every session that came from it or from one of them, and its row gives the sessions, the projects, the days, the prompts, the requests, the compactions, the cost and how each was joined. `session <id>` says where a session came from and where it went on.

## Context

`docs/analyses/mods-for-the-kit.md`, M13, from auto-handoff's lineage in `$.store`. The design was the timeline's `session` line, written by `A55` when a clear or a resume starts a session in the same process. No timeline exists before 0.28.0 is installed, so the transcripts on disk were read for what they show of the same thing. Two joins were there. A fork's file (the desktop's fork, a session started with this one's context) begins with its parent's records. And the engine's `cost-state` record carries `startTime` with a `totalCostUSD` that is a running total: the eleven sessions of `concepts-main` from 2026-09-29 to 2026-10-13 share one start, and each one's total begins where the one before ended. The reader printed that running total as each session's cost, so those eleven summed to 410.21 USD where their running total ended at 82.30. The start is not the process: the desktop's Handoff and clear of 2026-10-25 kept the kit's module alive across the clear and still began a new total.

## Options

- The timeline alone. Rejected: it holds nothing from before the install, and a clear that keeps the process is the only one it names.
- The shared start alone, every session sharing it one chain in the order they began. Rejected: a fork runs beside its parent with the same start, and its own total runs on from the parent's at the fork, so the order of starts would subtract the wrong total.
- A session's own cost from its first cost state. Rejected: the first state is written partway through a session, after cost it has spent.
- Joining by the person's prompt (the `new_task` resend opening the next session). Rejected: the resend is the person's prompt for a new task, which is the opposite of one piece of work, and the timeline already names the clear it follows.

## Consequences

Over the 59 transcripts on disk the sessions' cost falls from 1,149 USD to 737, and `chains` finds seven: the eleven of `concepts-main` (82.30 USD), the session of 2026-10-24 here with its fork into `claude-mods` and the session its total ran on to (161.21), the four of this session's forks (no cost state, so no cost), and four more of two sessions each. A session whose predecessor's transcript is gone keeps the total it carried in. A desktop session writes no cost state, so its cost reads `?`. A fork's copied records are counted in the parent alone, so a fork whose parent's transcript is gone loses them from the counts. `--project` and `--since` read every transcript before they leave any out, since a session's predecessor may lie outside them. A chain says how its sessions were split. Whether a clear continued the work or started a new task (`A19`, one task per context) is the owner's reading.

## Proof

Cases in `test_session_transcripts.py`, kept as regressions and as the contract with the timeline. A fork's copy of its parent's records is counted in the parent alone. A session's cost is its own, the total carried from the session before it taken out, for a fork and for a shared start. A fork with no record of its own comes after its parent in its chain, which the first run on real transcripts got wrong. The timeline's `session` line joins the session a clear started to the one before it. Each failed before its fix. Run on the 59 transcripts on disk and over the owner's archive into `docs/measurements/sessions-2026-10-25-deduplicated-with-archive.md`, 35 chains over 440 sessions. The timeline's join has run on test data alone, since no installed kit has written one.
