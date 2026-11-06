---
id: A96
from: [O22, O24]
source: owner
status: decided 2026-11-06
kind: behaviour
implemented_by: [plugins/session-kit/hooks/load.ts, plugins/session-kit/hooks/context.tsx, plugins/session-kit/hooks/band.tsx, plugins/session-kit/transcripts/week.py]
proven_by: [plugins/session-kit/hooks/load.test.tsx, plugins/session-kit/transcripts/test_week.py]
supersedes: [A92, A95]
---

# A96 The owner's prompt goes on, and the band asks why

With `~/.claude/session-kit/load/settings.json` in place, the owner's prompt outside its window, or into a session that is not active while `sessions.max` others are, goes on at once. The band then shows a Why now row with a one-line field and a ✕, naming the window or each active session. The session never waits on the answer. The windows, the personal folders and what counts as an active session are as `A92` (the working window holds the owner's prompt for a reason) and `A95` (a prompt into one session more than three waits for a reason) set them.

The question is logged in `holds.jsonl` as `asked` when the prompt goes on. The answer adds a line of its own: `answered` with the reason, or `dismissed` for the ✕. A reason given for the window opens the pass of `passMinutes` for every session, so their prompts are not asked about until it ends, and a reason given for the sessions opens none. While a question waits in a session, that session's later prompts are not asked about again. A prompt from the phone, which draws no band, is logged with no reason, as before. The week review keeps one row per question, from its last line, and counts the answered, the dismissed and the unanswered.

The owner's decision of 2026-11-06: "Remove the stoppers based on time or session count. The sessions should start regardless, but I should still be prompted to justify (dismissable, asynchronous to the session)."

## Context

The wait for the answer is the shell loop `A92` used, in bounds of ten minutes that start again while nothing is written. It runs apart from the hook, which returns as soon as the question is on the band. The band writes only the answer's file, and the log and the pass are written by the module that asked. So the validator's calls line, which a new helper making `$` calls would push past its cut (`docs/PLAN.md`, Deferred), gains no name.

## Options

- Log only the answer. Not taken: a question left unanswered when the session closes would leave no trace in the week.
- Ask again on every prompt while a question waits. Not taken: one row per session is the friction, and more rows are noise.
- Keep the hold, with a button to send without a reason. Not taken: the owner asked that the session never wait.

## Consequences

Nothing of it reaches the model (`C5`, nothing of the load measures reaches a session). A question unanswered when the session quits stays `asked` in the log. A hot reload drops the wait under way while the row stays, so an answer given after one clears the row and goes unlogged. The pass now opens when the reason is written, so the status line names it at its next refresh. Lines from before 0.49.0 (`sent`, `returned`) read as they did.
