---
id: A25
from: [O12, O6]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/hooks/checkout.ts, plugins/session-kit/hooks/kit.tsx]
proven_by: [plugins/session-kit/hooks/checkout.test.ts]
supersedes: []
---

# A25 The checkout checks

A hooks module of `session-kit`. On the first prompt of a context (a new conversation, or one just compacted or cleared), context beside the prompt tells the model when `CLAUDE.local.md` is missing or older than the last commit, with the handoff command to run. A prompt is the first of its context while the engine reports no context figure, as it does for a fresh window until its first response. At the end of a turn of the main loop, one dim line tells the person how many uncommitted changes the tree holds and whether the handoff predates the last commit. Outside a git repository both stay silent.

## Context

The first project's `.claude/settings.json` ran the same two checks as shell hooks (the inventory's H11 and H13), and the kit left them behind at the move because their other halves (the inbox, the findings count, the worktree title) were the project's. The 2026-10-25 reading of that project named the generic halves as the first tool to lift, since a handoff that goes stale is what a compaction then reads as current, and no other piece of the kit sees it.

## Options

- The git state at the start too (branch, status, recent commits), as the project's hook printed. The engine already sends its own `gitStatus` block, so the kit's would be a second copy. Left out.
- Holding the end of a turn until the model commits. A turn may end with work in flight when the next step is the owner's, and the rationale records what holding every turn cost. The line is for the person.
- A toast instead of a transcript line. A toast leaves. The line stays where the person scrolls.
- The advice as a `prompt.context` block beside the instruction files, as first built. In the owner's work instance `cc-plugin-sec-default`, most likely seated by an organisation policy ahead of every user-installed plugin, answers `prompt.context` without passing it on, so the block never reached the model there. `prompt.submit` passes that mod (the `new_task` resend proved it), so the advice rides beside the first prompt. A slash command's prompt carries none, and a prompt with no words is left alone, the matcher the engine needs for a second `prompt.submit` hook in the module.

## Consequences

Two `git` runs at the end of every main-loop turn, a few tens of milliseconds. Every prompt costs one read of the context figure, and the first of a context two `git` runs more. The advice is sent once per context, which is when a stale handoff is read as current. Undone if the person finds the line noise, which would say the checks fire where the rule allows an uncommitted tree.
