# Where we stand, in plain words

Written 2026-10-25 for the owner, who asked where the work is. Rewritten whole each time it is asked for. The record behind it is `docs/intent/` and `docs/PLAN.md`. This file names things by what they are and keeps the ids in parentheses for the reader who wants the file.

## What this repository is

Your whole setup for working with agents, in one place: the rules every session loads, the `session-kit` plugin that enforces some of them, the documents that say why, and the record of what was decided and what it serves.

## What we set out to do this week

Three things, in the order you gave them.

1. Move the plugin's hooks inside the engine. `session-kit`'s hooks were Python scripts the engine spawned on every tool call. Claude Code 2.1.308 lets a plugin run code in-process as a "mod", which is cheaper per call and can draw on the screen and ask the engine for figures the scripts had to guess. The plan (the port, `A20`) moved them one at a time, the kit kept working after each step.
2. Keep the record of intent true. You set the process: goals in your words, objectives you approve, actions a session decides and you validate. A tool (`session-intent`) now generates the index and checks the record, so a stale entry fails a gate instead of standing there unread.
3. Watch the system work and improve it from evidence. You added the objective that the system is observed over time (`O17`). A reader over the session transcripts (`session-transcripts`) now writes a report under `docs/measurements/`, and its first finding changed a setting the same day, and the archive of 381 old sessions is read with it.

## What is done

All of it committed on `main`, none of it pushed. You asked to hold the push.

- The context warning is in-process (`A16`). The engine's own token figure is read after each tool call. From 250,000 tokens the model is told to find a clear point, every 25,000 tokens, firmer at 500,000 and at 750,000. A band above the prompt shows you the count. You set the threshold as a token count after the first transcript report. The percent of the window is still there as an alternative. Your archive of 381 sessions, read the same day, puts your own compactions at a median of 256,000 tokens and shows the old warning at 500,000 was obeyed within a turn almost every time, so both tiers hold.
- The clear-point chain (`A17`), off by default. With the `chain` option on, the model calls a `clear_point` tool when it reaches one, and the plugin runs the handoff, the compaction and the "continue" prompt without you. **The backstop** (`A18`) gives the engine's own automatic compaction the handoff's fields, so an unplanned compaction loses less.
- One task per context (`A19`). The rule is in the global rules. With `chain` on, the model calls a `new_task` tool when a prompt changes subject, and the band offers you the handoff and a clear, or to keep going, and sends your prompt again either way.
- The test log, the document-length cap and the single-edit nudge moved in-process (`A11`, `A8`, `A7`). A Bash call now pays about 32 ms of hooks instead of about 100.
- The intent index and check (`A21`). `session-intent index` writes `docs/intent/INDEX.md`, leading with what waits on you. `session-intent check` fails on a dangling path, a missing field, a retired entry nothing supersedes, or a `CLAUDE.md` block out of step.
- The transcript reader (`A22`). `session-transcripts report` reads every project's transcripts and writes a dated report. The first one (`docs/measurements/sessions-2026-10-25.md`) found that the old warning had never fired in 39 sessions and that every one of 145 compactions was manual, at a median of 152,000 tokens.

The plugin is at version 0.10.0. Its checks are green: validation, 28 engine tests, the type check, the Python hook tests, 22 cases for the intent tool, 18 for the transcript reader.

## What is not proven

No mod has run in a real session yet. Everything above is proven by the engine's test harness alone. The install path pulls from GitHub, so a real run waits on the push, or on a marketplace added from the local checkout.

## What waits on you

- The push. It unblocks the real-session run of every module.
- Mod ordering. Whether a mod's refusal runs before another installed mod's approval. The last piece of the port, the guard as a mod, waits on the answer.
- Three objectives to approve or cut, inferred by a session from your earlier rules: commands run with the project's own tools (`O14`), routine work takes the cheaper path (`O15`), a document the work rests on is read whole (`O16`).
- One constraint to state or strike: the kit is never the reason a session fails, the guard excepted (`C1`).
- Two numbers I chose: the firmest warning tier at 750,000 tokens, and the global rule's "skip the ask" line at 150,000 tokens, both unmeasured.
- Twenty-one actions to validate, listed first in `docs/intent/INDEX.md`. You validate in batches at a clear point, and nothing waits on it.

## What is next, in order

1. After the push: install 0.10.0 and watch one real session, the warning, the band, one chain run, one `new_task` press of each button.
2. The reader's `rules` command: how often a rule is not held, from the transcripts.
3. After the first real session: the measuring module, which records what each hook did.
4. The guard as a mod, once mod ordering is answered.
5. The `cache-tax` decision, once the context mod is validated.

## The communication objective, added today

You said the ids mean nothing on their own: "Approve O14?" cannot be acted on. That is now an objective in your words (`O18`), with two actions: a rule that an id is never written without its name (`A23`, in force now, with a `session-intent names` command that prints them), and a mod that draws the name beside every id in a reply (`A24`, its shape decided and waiting to be built).
