# session-kit: goals, objectives, actions, and a port to a mod

Draft of 2026-10-24, for the owner to correct. It covers `session-kit` 0.5.1 (`086e6aa` in `~/devel/galileo/misc/claude-kit`) and the mod API of Claude Code 2.1.308 (`plugin-authoring/types/claude-code.d.ts`). It follows the process in `goals-objectives-actions.md`. When the owner has approved the objectives, this document moves into the `session-kit` repository as its documentation, and the port starts there.

## Goals

Only the owner's words. Each dated to when it was said in this project.

| Id | Goal | Said |
| --- | --- | --- |
| G1 | Reduce agent confusion when context grows. | 2026-10-24 |
| G2 | Improve performance. | 2026-10-24 |
| G3 | Make my work with agents consistent and good across projects. | 2026-10-24 |

G2 is read here as cost and latency: tokens, model turns, and the time hooks add to each tool call. That reading is the session's and needs the owner's word.

## Objectives

`owner` means the owner said it in so many words, and those are approved. `inferred` means read from a hook's docstring, `global/RATIONALE.md` or a commit message, and proposed until the owner approves it.

| Id | Objective | From | Source | Status |
| --- | --- | --- | --- | --- |
| O1 | One task per context. A change of idea starts a fresh context, so unrelated or conflicting tasks never share one. | G1 | owner | approved |
| O2 | Lose nothing at a context boundary. | G1, G2 | owner (gave this as the example of an objective and its goals) | approved |
| O3 | Automate the routine parts of the process, so the owner's attention goes to decisions. | G2, G3 (the session's guess, since the owner called this objective inferred without naming its goals) | inferred, from "so the user doesn't need to look at it constantly" and "focus on more important things" | proposed |
| O4 | Manage the goals, objectives and actions process itself, shared across every project. | G3 | owner | approved |
| O5 | Simple and one-off tasks are not slowed. A formal process is not applied where it would make the work worse. | G3 | owner | approved |
| O6 | A rule that prose has failed to hold is held mechanically, when a narrow check can tell a breach. | G3 | inferred, from `guard.py` ("a reminder in a CLAUDE.md has already failed to hold it") | proposed |
| O7 | Machine-written prose reads as a person's. | G3 | inferred, from RATIONALE "A file you touch leaves with fewer prose tells" | proposed |
| O8 | Commands run with the project's own tools and configuration: its direnv environment, its formatters, its language-server view. | G2, G3 | inferred, from `direnv_env.sh`, `format.py`, `pyright_env.py` | proposed |
| O9 | Evidence of a run survives: a failed test run's output is kept where it can be read again. | G1, G2 | inferred, from `test_log.py` and RATIONALE "Test output goes to a file" | proposed |
| O10 | The kit is never the reason a session fails. | G3 | inferred, from every hook's docstring ("a hook never breaks the session") | proposed. It may be a constraint on every action instead of an objective of its own. |

O10 and O6 pull against each other in one place: `guard.py` fails open, so a crash in it lets through the call it exists to refuse. A mod can choose per hook, and the guard is where failing closed belongs.

O1 has no action today. The only path is the owner running `/session-kit:handoff` and `/clear` by hand.

## Actions in place: what each piece does, why it took its shape, and what a mod changes

Every piece of session-kit 0.5.1 is an action the sessions that built it decided. Each is `decided` and awaits the owner's validation through this document. The dates are the commits that shipped them.

| Id | Piece | Serves | Why this shape | Cost today | As a mod |
| --- | --- | --- | --- | --- | --- |
| A1 | `context_pressure.py` (PostToolUse `*`), 2026-10-11, reworked 2026-10-22 | G1, O2, O3 | It tells the model, because the model is the one that knows where a clear point is. It fires after tool calls, so the warning arrives while the model can still choose where to stop. Holding the end of every long turn was tried and dropped in 0.5.0: it added a closing paragraph about the context to every turn (RATIONALE "Ask for a compaction at a clear point"). | One Python start and a 256 kB transcript read per tool call of any kind. `WINDOW` is a constant of 1M, so on a 200k model the 50% trigger is never reached and the hook stays quiet. | `$.session.usage().context` gives `tokens`, `window` and `percent` from the engine, in-process, which fixes the window. Text for the model goes on a tool result's `context`, the same reminder a PostToolUse hook adds. A band above the prompt can show the person the figure without the model reading it. |
| A2 | `handoff` skill, 2026-10-11 | O2 | It needs the model, which is the only one that can summarise decisions and state. | One model turn when run. | Stays a skill. A mod can run it with `$.command.run({ command: "session-kit:handoff" })`. |
| A3 | `guard.py` (PreToolUse Bash, Artifact), 2026-10-11 | O6 | Regexes over the command text, each narrow, with carve-outs. Settings hook, so it runs in every mode. | One Python start per Bash call, plus a `git branch -r --contains` on `--amend`. Fails open. On a personal login another mod can approve a call it denied. | A `tool.call` hook with a `.catch` that denies, so it fails closed, and sits in the same chain as other mods. Whether it runs above a third-party mod's approval is still open (PLAN.md, "Mod ordering"). |
| A4 | `nudge_single_edit.py` (PreToolUse Bash), 2026-10-11 | G2, and no objective (see below) | A shell `case` filters before Python starts, so only Python heredocs pay. | Near zero. | Same check in-process. Low value on its own. |
| A5 | `doc_length.py` (PostToolUse Edit, Write), 2026-10-11 | G1, and no objective (see below) | Counts lines of `docs/*.md`. | One Python start per Edit or Write. | In-process with `$.fs`. |
| A6 | `session-tells hook` (PostToolUse Edit, Write, Bash edits), 2026-10-11 | O7 | The rules are Python, with tree-sitter readers for TypeScript and Rust. | One `uv run` per edit, the heaviest hook. | The rules stay Python. A mod would run them with `$.process.run`, which keeps the spawn, so it stays a settings hook unless the rules move to TypeScript (about 850 lines of rules). |
| A7 | `format.py` (PostToolUse Edit, Write, Bash edits), 2026-10-11 | O8 | Picks ruff, oxlint and biome from the project's config. | One Python start, then the tools themselves. | Saves only the Python wrapper. The tools still spawn. |
| A8 | `test_log.py` (PostToolUse, PostToolUseFailure Bash), 2026-10-11 | O9 | Writes the last test run whole to a session-scoped temp file. | One Python start per Bash call. | `tool.call` with `await next(e)` sees the output in-process and writes it with `$.fs`. |
| A9 | `direnv_env.sh` (SessionStart, CwdChanged, FileChanged), 2026-10-11 | O8 | Writes to `CLAUDE_ENV_FILE`, which Claude Code sources before each Bash command. | Rare events. | The 2.1.308 types have no equivalent of `CLAUDE_ENV_FILE`, so it stays a settings hook. |
| A10 | `pyright_env.py` (SessionStart), 2026-10-11 | O8 | Off unless the project asks, since it replaces a root config. | Once per session. | Stays. |
| A11 | `bin/`, `codeintel/`, 2026-10-11 and 2026-10-12 | O6, O7, O8 | Commands and rules, no hooks. | None per call. | Unchanged. |
| A12 | `global/CLAUDE.md` and `RATIONALE.md`, 2026-10-11 | G3 | A plugin cannot ship a `CLAUDE.md`, so the rules are linked into `~/.claude/CLAUDE.md`. | Loaded into every session. | Unchanged. Under the process, each rule names its objective (`goals-objectives-actions.md`, "Where the entries live"). |

Two actions trace to a goal and to no objective: A4 (steer the model to the cheaper way of doing the same thing) and A5 (a document past 1500 lines costs context). Under the process that is a gap. Either an objective is missing (something like "the model's routine work takes the cheaper path"), or these two are small enough to retire. The owner's call.

Per tool call the plugin starts, today: on any tool, one Python process (A1). On a Bash call, three (A3, A8, A1), and on a Bash call that edited files, a fourth (A7) and a `uv run` (A6). On an Edit or Write, three Python processes and a `uv run`. Nobody has measured what these add per call. A port should start by measuring it (the debug log times each hook), so the gain under G2 is a number.

## The context guard, rethought

The owner's two ideas: as a mod, the warning could be acted on without the model reading it, which saves tokens. Better still, the mod could run `/session-kit:handoff`, then `/compact`, then "Continue" on its own. Both serve O3.

### What the API allows

All three steps exist in 2.1.308:

- `$.command.run({ command: "session-kit:handoff" })` runs the skill as if typed, queued until the session is idle.
- `$.session.compact({ instructions })` is the call `/compact` makes. It runs between turns only and rejects while a turn runs.
- `$.prompt.submit({ text })` starts a turn once the session is idle. Without `asUser` the model reads it framed as sent by the plugin.
- `turn.complete` fires when a turn ends, which is where a chain starts.
- A `session.compact` hook sees every compaction, the engine's own automatic one (`trigger: "auto"`) included, and can rewrite its `instructions`.

### Hiding the warning saves little

The warnings run from 50% to 100% of a 1M window every 25k tokens: about 20 per session at about 80 tokens each, some 1,600 tokens, re-read at cache-read prices. That is noise next to one compaction. The cost the history records was behavioural: a held stop put a paragraph about the context into every turn. Under G2, token savings are a weak reason to hide the signal.

### Who knows where the clear point is

A compaction costs least at a phase boundary: the commit is green, nothing is in flight, no question waits on the owner. A mod can see that a turn ended, that the tree is clean, and the context figure. It cannot see whether the model is half way through a multi-turn step, or whether the turn ended on a question the owner has not answered. Only the model knows that. So the design question is which party says "this is a clear point". Three candidate actions:

| Option | Who decides | What runs | Risk |
| --- | --- | --- | --- |
| A. Port as is | The model, warned | The mod measures in-process with the engine's window and warns the model as today. The owner runs `/session-kit:handoff` and `/compact`. | None new. O3 stays unmet: the owner still has to act. |
| B. The model signals, the mod acts | The model, warned | The mod registers a tool (`$.tool.register`), say `clear_point`, and warns as today. At a clear point the model calls it. When that turn ends the mod runs the handoff, compacts, then submits a continue prompt that also says to read again the documents `CLAUDE.local.md` lists. If the handoff's Next step waits on the owner, the mod stops after the compaction, and the band shows that the next step is the owner's. | A model that calls the tool at the wrong moment. The warning text and the tool's description carry the definition of a clear point. |
| C. The mod decides alone | Heuristics | At `turn.complete` past the threshold, with a clean tree and a final message that asks nothing, the mod runs the chain. The model never reads a warning. | Compacts mid-step whenever the heuristics misread. A missed question to the owner gets "continued" past. |

B fits O3 and leaves with the model the judgement only it can make. The model still reads the warning, at a token cost shown above to be small. The session's pick is B, for the owner to validate.

Two refinements, for either A or B:

- A backstop for the engine's own compaction (O2). When the context hits the engine's threshold, the compaction comes without a handoff. A `session.compact` hook on `trigger: "auto"` can add instructions that make the summary keep the task, the decisions and the next step. It cannot run the handoff first, since that needs a model turn.
- One model call instead of two (G2, to try, unverified). The handoff turn and the compaction each read all of the context. The `session.compact` hook could tell the summariser to write its summary in `CLAUDE.local.md`'s fields, then write the file from the summary it gets back (`SessionCompacted.messages` holds it). The summariser has no tools, so it cannot check `git status` or the last test run the way the skill can. Measure the two summaries side by side before choosing.

## One task per context (O1)

Nothing serves O1 today. Three candidate actions, cheapest first:

1. A rule in `global/CLAUDE.md`: when a prompt is unrelated to the task in `CLAUDE.local.md`, name the mismatch and propose `/session-kit:handoff` then `/clear` before starting. Costs nothing. It is prose, which is the kind of rule O6 exists because prose fails to hold.
2. The model signals, as in option B: it calls a registered `new_task` tool, and the mod offers the handoff and clear in the band.
3. The mod judges on `prompt.submit`: above some context size (a small context gains little from a clear), one `$.model.complete` on Haiku with a low `maxTokens` compares the prompt to `CLAUDE.local.md`'s Task. On "unrelated" it drops the prompt once, the way cache-tax does, and offers the clear. Costs one small model call per prompt above the size. A false "unrelated" costs the owner a resend.

A cold cache makes the case stronger. Clearing then avoids paying the cache write on a context about to be abandoned, which is where cache-tax's signal meets this one.

## One mod or several

One plugin, `session-kit`, holding the settings hooks that stay and one hooks module per concern (context, guard, test log). Reasons:

- The context band, the chain and a future cache signal share the same figures and `$.state`. The research report's rule for merging, shared code or state, holds here.
- `hooks.json` takes a list of modules, so concerns stay in separate files without separate plugins. (To confirm with `claude plugin validate` on the first module.)
- Turning one concern off needs a `userConfig` toggle we write. Accepted, since all of it is ours and tested together.

### Order

Each step ships on its own and leaves the kit working:

1. Context, as option A: the mod measures with the engine's window, warns the model through the tool result's `context`, and draws a band. A1 is retired. Measure the hook times before and after.
2. The chain, option B, behind a `userConfig` toggle, off by default until it has run in a few real sessions.
3. A8, A5 and A4 move in-process (the last two if they survive the gap above). Small, and they retire three Python starts on a Bash call.
4. The guard, once the mod-ordering question is answered. Both guards run side by side for a while, the mod failing closed and the settings hook as it is.
5. One task per context, after the owner picks a way.
6. Stay as settings hooks: A6, A7, A9, A10.

The mods API is early access and moves between releases. The settings hooks ride a stable contract. That argues for keeping the guard's settings hook even after the mod guard lands.

## Open questions for the owner

1. The reading of G2 as cost and latency.
2. O3's goals, and approval or correction of O3 and O6 to O10.
3. A4 and A5: a missing objective, or retire them?
4. The context chain: A, B or C? Should the chain ever submit "Continue" without the owner, or stop after the compaction every time?
5. One task per context: which of the three ways, and is a Haiku call per prompt acceptable for the third?
6. Where the documentation lives in `session-kit`: a `docs/intent.md` beside the README, or the README itself?
7. Is the 1M window the only one in use? With the engine's figure it no longer matters for the port, but it decides whether A1 has been quiet on some sessions.
