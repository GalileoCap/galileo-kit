---
id: A61
from: [O5, O12]
source: session
status: decided 2026-10-26
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/footprint.toml]
proven_by: [plugins/session-kit/hooks/chain.test.tsx, plugins/session-kit/hooks/cold_cache.test.tsx]
supersedes: []
---

# A61 The chain compacts through /compact in every session

The chain of `A17` (the model signals a clear point, the mod runs the chain) and the cold-cache timer of `A49` compact by running `/compact` through `$.command.run`, with the handoff's instructions as its arguments, whether or not a person is at the prompt. `$.session.compact`, its twenty tries a second apart and the session's `isInteractive` reading are gone. What `/compact` printed goes to the chain file.

## Context

`docs/analyses/mods-for-the-kit.md`, M10, from effortless. Since 0.20.3 the chain took two paths: `/compact` by command where no person is at the prompt (the SDK, the desktop app), where `$.session.compact` is refused, and `$.session.compact` retried for twenty seconds where one is, since it rejects while a turn runs. The engine's types say `$.command.run` is queued and run once the session is idle, which is the wait the retry stood in for. The chain files under the temporary directory hold 31 compactions run on 2.1.308 by the desktop app, every one through `/compact` and none refused or skipped. The `$.session.compact` path has never run outside the tests: the terminal's engine is 2.1.296, which refuses the kit's module.

## Options

- Keep both paths. Rejected: the terminal keeps a path that has never run, beside a path proven in real sessions.
- `/compact` everywhere, as built. Every session takes the path proven in real sessions, and `$.session.compact` leaves the kit's footprint (`A60`, the kit's reach held to a reviewed footprint).
- `/compact` everywhere, and a `session.compact` hook on the manual trigger to see a veto, which `$.session.compact` returned as `{ skip }` and a command's result does not carry. Rejected: a plugin seated ahead of the kit answers the event before the kit's hook runs (`cc-plugin-sec-default` does so in the work instance), so the hook would see a veto only from a plugin beneath, and it adds an event to the footprint for a case no real run has shown.

## Consequences

A veto of the compaction by another plugin's `session.compact` hook lets the chain go on: the continue prompt goes into a context left whole, and the warning of `A16` (context measured in-process, the model warned) names the next clear point. The chain file records what `/compact` printed, so a veto shows there. A `/compact` the engine refuses stops the chain at once with a toast, with no second try. A dismissal of the band while `/compact` runs lets the compaction land and continues nothing. Undone if a real session shows `/compact` by command failing where a person is at the prompt.

## Proof

The chain's cases in `chain.test.tsx` were changed before the code to expect `/compact` with the handoff's instructions where a person is at the prompt, after a judge's stop, and under a dismissal while it runs, and `cold_cache.test.tsx` to expect it from the timer. They failed on 0.30.0 and pass on 0.31.0. A blind case, a refused `/compact` stopping the chain with no second try, passed and was deleted. The SDK session's case of 0.20.3, the engine's own compaction never asked, passed before and after. Not yet run: a chain in a terminal session, which needs an engine that loads the kit's module.
