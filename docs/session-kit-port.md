# The port of `session-kit`'s hooks to a mod

The analysis behind the port, written 2026-10-24 against `session-kit` 0.5.1 (`086e6aa`) and the mod API of Claude Code 2.1.308 (`plugin-authoring/types/claude-code.d.ts`). The entries it produced are files under `docs/intent/`, and this document keeps what an entry has no room for: the API findings, the reasoning across options, the measurements still to take. Where the two disagree, the entry wins.

## Where the first draft's entries went

The first draft gave `session-kit` a ladder of its own, with three goals the owner had said of it. When `claude-mods` merged into this repository the two ladders became one, under the five goals `G1` to `G5`.

- Its `G3`, "make my work with agents consistent and good across projects", is `G1`. Its `G2`, "improve performance", is `G4`, whose words fix the reading that was open: time and cost. Its `G1`, "reduce agent confusion when context grows", survives through its two objectives, `O11` and `O12`, which hang from `G2` and `G3` directly.
- Its `O1`, `O2` and `O5`, the owner's words, are `O11`, `O12` and `O13`. Its `O8` is `O14`, still proposed. Its `O3` (automate the routine parts), `O6` (a rule prose failed to hold is held mechanically) and `O4` (manage the process) fold into `O5` and `O3`. Its `O7` (prose reads as a person's) folds into `O8`, and its `O9` (evidence of a run survives) into `O6` and `O9`. Its `O10` is the constraint `C1`.
- Its `A1` to `A12`, the pieces of 0.5.1, are `A4` to `A15`. The two that hung from a goal and no objective, the single-edit nudge and the document-length warning, now hang from `O15` and `O16`, proposed so that the owner approves them or retires the hooks with them.
- The decisions the analysis reached are `A16` to `A21`: the context mod, the chain, the backstop for the engine's own compaction, one task per context, one plugin with one module per concern and its order, and the index and check tool for `docs/intent/`.

## What each piece costs today

Per tool call the plugin starts, today: on any tool, one Python process (`A4`). On a Bash call, three (`A6`, `A11`, `A4`), and on a Bash call that edited files, a fourth (`A10`) and a `uv run` (`A9`). On an Edit or Write, three Python processes and a `uv run`. Nobody has measured what these add per call. The port starts by measuring it, since the debug log times each hook, so the gain under `G4` is a number. That measurement is what validates `A16`.

`C1` and `O5` pull against each other in one place: `guard.py` fails open, so a crash in it lets through the call it exists to refuse. A mod can choose per hook, and the guard is where failing closed belongs. `C1` names it as the exception.

## The context chain

The owner's two ideas: as a mod, the warning could be acted on without the model reading it, which saves tokens. Better still, the mod could run `/session-kit:handoff`, then `/compact`, then "Continue" on its own.

### What the API allows

All three steps exist in 2.1.308:

- `$.command.run({ command: "session-kit:handoff" })` runs the skill as if typed, queued until the session is idle.
- `$.session.compact({ instructions })` is the call `/compact` makes. It runs between turns only and rejects while a turn runs.
- `$.prompt.submit({ text })` starts a turn once the session is idle. Without `asUser` the model reads it framed as sent by the plugin.
- `turn.complete` fires when a turn ends, which is where a chain starts.
- A `session.compact` hook sees every compaction, the engine's own automatic one (`trigger: "auto"`) included, and can rewrite its `instructions`.

### Hiding the warning saves little

The warnings run from 50% to 100% of a 1M window every 25k tokens: about 20 per session at about 80 tokens each, some 1,600 tokens, re-read at cache-read prices. That is noise next to one compaction. The cost the history records was behavioural: a held stop put a paragraph about the context into every turn. Under `G4`, token savings are a weak reason to hide the signal. The saving is in the steps the owner stops running by hand, which is `O5`.

### Who knows where the clear point is

A compaction costs least at a phase boundary: the commit is green, nothing is in flight, no question waits on the owner. A mod can see that a turn ended, that the tree is clean, and the context figure. It cannot see whether the model is half way through a multi-turn step, or whether the turn ended on a question the owner has not answered. Only the model knows that. So the design question is which party says "this is a clear point". The three options are recorded in `A16` and `A17`: the owner acts (A), the model signals and the mod acts (B), the mod decides alone (C). `A16` takes A as the first step and `A17` takes B on top of it, behind a toggle. C is rejected in both.

Two refinements, recorded in `A18` and `A17`'s consequences:

- A backstop for the engine's own compaction (`O12`). When the context hits the engine's threshold, the compaction comes without a handoff. A `session.compact` hook on `trigger: "auto"` can add instructions that make the summary keep the task, the decisions and the next step. It cannot run the handoff first, since that needs a model turn.
- One model call instead of two (`G4`, to try, unverified). The handoff turn and the compaction each read all of the context. The `session.compact` hook could tell the summariser to write its summary in `CLAUDE.local.md`'s fields, then write the file from the summary it gets back (`SessionCompacted.messages` holds it). The summariser has no tools, so it cannot check `git status` or the last test run the way the skill can. Measure the two summaries side by side before choosing.

## One task per context

Nothing served `O11`. The three ways, cheapest first, are recorded in `A19`: a rule in `global/CLAUDE.md`, the model signalling through a registered `new_task` tool, and the mod judging each prompt above a context size with one small model call. `A19` takes the rule now and the tool with the port, and rejects the judge: a model call per prompt, and a false "unrelated" costs the owner a resend. A cold cache makes the case stronger. Clearing then avoids paying the cache write on a context about to be abandoned, which is where `cache-tax`'s signal meets this one (`O10`).

## One mod or several

One plugin, `session-kit`, holding the settings hooks that stay and one hooks module per concern (context, guard, test log), recorded as `A20` with the order the steps ship in. The reasons, in short: the context band, the chain and a future cache signal share the same figures and `$.state`, which is the research report's rule for merging. `hooks.json` takes a list of modules, so concerns stay in separate files without separate plugins, to confirm with `claude plugin validate` on the first module. Turning one concern off needs a `userConfig` toggle we write, accepted since all of it is ours and tested together. The mods API is early access and moves between releases, while the settings hooks ride a stable contract. So the guard's settings hook stays even after the mod guard lands.

## Open questions for the owner

1. `O14` to `O16`: approve or cut. `A7` and `A8` go with `O15` and `O16`.
2. `C1`: state it as the owner's, or strike it.
3. `A17`: may the chain submit "Continue" without the owner when the handoff's next step is the session's, or stop after the compaction every time?
4. `A19`: the rule now and the tool with the port, with the per-prompt judge rejected.
5. Is the 1M window the only one in use? With the engine's figure it no longer matters for the port, but it decides whether `A4` has been quiet on some sessions.
6. Mod ordering, from `docs/PLAN.md`: whether a mod's deny runs before or after another user-installed mod's approval, which decides when the guard's mod form can land.
