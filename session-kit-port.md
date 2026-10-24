# session-kit: its intent, and a port to a mod

Draft of 2026-10-24, for the owner to correct. It covers `session-kit` 0.5.1 (`086e6aa` in `~/devel/galileo/misc/claude-kit`) and the mod API of Claude Code 2.1.308 (`plugin-authoring/types/claude-code.d.ts`). When the owner has confirmed the intents, this document moves into the `session-kit` repository as its documentation, and the port starts there.

Each intent is marked by where it came from. **Owner** means the owner's own words in this project. **Inferred** means read from `global/RATIONALE.md`, a hook's docstring or a commit message, and waiting for the owner to confirm or correct.

## What session-kit is for

| | Intent | Source |
| --- | --- | --- |
| I1 | Keep a long session reliable. Quality drops well before the window is full, and it drops as unreliability that nobody notices. | Owner ("reduce agent confusion when context grows"), and the `context_pressure.py` docstring |
| I2 | Keep cost and latency down: tokens, model turns, and the time hooks add to each tool call. | Owner ("improve performance") |
| I3 | One task per context. A change of idea starts a fresh context, so unrelated or conflicting tasks never share one. | Owner |
| I4 | Lose nothing at a context boundary. The state of the work is written to a file before a compaction or a clear, and the next session reads it and the documents it names. | Inferred: the `handoff` skill, RATIONALE "Sessions" |
| I5 | Nobody has to watch. The session acts on its own signals, and the owner is asked only for decisions. | Owner ("so the user doesn't need to look at it constantly") |
| I6 | A rule that prose failed to hold is held mechanically, when a narrow check can tell a breach. | Inferred: the `guard.py` docstring ("a reminder in a CLAUDE.md has already failed to hold it") |
| I7 | Machine-written prose reads as a person's. | Inferred: RATIONALE "A file you touch leaves with fewer prose tells" |
| I8 | Commands run with the project's own tools and configuration: its direnv environment, its formatters, its language-server view. | Inferred: `direnv_env.sh`, `format.py`, `pyright_env.py` |
| I9 | Evidence survives: a failed test run's whole output is kept where it can be read again. | Inferred: `test_log.py`, RATIONALE "Test output goes to a file" |
| I10 | Steer the model to the cheaper way of doing the same thing. | Inferred: `nudge_single_edit.py` ("~35% cheaper in tokens") |
| I11 | A hook never breaks the session it serves. On anything unexpected, every hook exits with no output and no error. | Inferred: every hook's docstring |

I11 and I6 pull against each other: `guard.py` fails open, so a crash in it lets through the call it exists to refuse. A mod can choose per hook, and the guard is where failing closed belongs.

I3 has no piece today. The only path is the owner running `/session-kit:handoff` and `/clear` by hand.

## What each piece does, why it took that shape, and what a mod changes

| Piece | Intents | Why this shape | Cost today | As a mod |
| --- | --- | --- | --- | --- |
| `context_pressure.py` (PostToolUse `*`) | I1, I4, I5 | It tells the model, because the model is the one that knows where a clear point is. It fires after tool calls, so the warning arrives while the model can still choose where to stop. Holding the end of every long turn was tried and dropped in 0.5.0: it added a closing paragraph about the context to every turn (RATIONALE "Ask for a compaction at a clear point"). | One Python start and a 256 kB transcript read per tool call of any kind. `WINDOW` is a constant of 1M, so on a 200k model the 50% trigger is never reached and the hook is silent. | `$.session.usage().context` gives `tokens`, `window` and `percent` from the engine, in-process, which fixes the window. Text for the model goes on a tool result's `context`, the same reminder a PostToolUse hook adds. A band above the prompt can show the person the figure without the model reading it. |
| `handoff` skill | I4 | It needs the model, which is the only one that can summarise decisions and state. | One model turn when run. | Stays a skill. A mod can run it with `$.command.run({ command: "session-kit:handoff" })`. |
| `guard.py` (PreToolUse Bash, Artifact) | I6 | Regexes over the command text, each narrow, with carve-outs. Settings hook, so it runs in every mode. | One Python start per Bash call, plus a `git branch -r --contains` on `--amend`. Fails open. On a personal login another mod can approve a call it denied. | A `tool.call` hook with a `.catch` that denies, so it fails closed, and sits in the same chain as other mods. Whether it runs above a third-party mod's approval is still open (PLAN.md, "Mod ordering"). |
| `nudge_single_edit.py` (PreToolUse Bash) | I10 | A shell `case` filters before Python starts, so only Python heredocs pay. | Near zero. | Same check in-process. Low value on its own. |
| `doc_length.py` (PostToolUse Edit, Write) | I1 (inferred: long docs cost context) | Counts lines of `docs/*.md`. | One Python start per Edit or Write. | In-process with `$.fs`. |
| `session-tells hook` (PostToolUse Edit, Write, Bash edits) | I7 | The rules are Python, with tree-sitter readers for TypeScript and Rust. | One `uv run` per edit, the heaviest hook. | The rules stay Python. A mod would run them with `$.process.run`, which keeps the spawn, so it stays a settings hook unless the rules move to TypeScript (about 850 lines of rules). |
| `format.py` (PostToolUse Edit, Write, Bash edits) | I8 | Picks ruff, oxlint and biome from the project's config. | One Python start, then the tools themselves. | Saves only the Python wrapper. The tools still spawn. |
| `test_log.py` (PostToolUse, PostToolUseFailure Bash) | I9 | Writes the last test run whole to a session-scoped temp file. | One Python start per Bash call. | `tool.call` with `await next(e)` sees the output in-process and writes it with `$.fs`. |
| `direnv_env.sh` (SessionStart, CwdChanged, FileChanged) | I8 | Writes to `CLAUDE_ENV_FILE`, which Claude Code sources before each Bash command. | Rare events. | The 2.1.308 types have no equivalent of `CLAUDE_ENV_FILE`, so it stays a settings hook. |
| `pyright_env.py` (SessionStart) | I8 | Off unless the project asks, since it replaces a root config. | Once per session. | Stays. |
| `bin/`, `codeintel/`, `global/CLAUDE.md` | I6, I7, I8 | Commands and rules, no hooks. | None per call. | Unchanged. |

Per tool call the plugin starts, today: on any tool, one Python process (`context_pressure.py`). On a Bash call, three (`guard.py`, `test_log.py`, `context_pressure.py`), and on a Bash call that edited files, a fourth (`format.py`) and a `uv run`. On an Edit or Write, three Python processes and a `uv run`. Nobody has measured what these add per call. A port should start by measuring it (the debug log times each hook), so the gain is a number.

## The context guard, rethought

The owner's two ideas: as a mod, the warning could be acted on without the model reading it, which saves tokens. Better still, the mod could run `/session-kit:handoff`, then `/compact`, then "Continue" on its own.

### What the API allows

All three steps exist in 2.1.308:

- `$.command.run({ command: "session-kit:handoff" })` runs the skill as if typed, queued until the session is idle.
- `$.session.compact({ instructions })` is the call `/compact` makes. It runs between turns only and rejects while a turn runs.
- `$.prompt.submit({ text })` starts a turn once the session is idle. Without `asUser` the model reads it framed as sent by the plugin.
- `turn.complete` fires when a turn ends, which is where a chain starts.
- A `session.compact` hook sees every compaction, the engine's own automatic one (`trigger: "auto"`) included, and can rewrite its `instructions`.

### Hiding the warning saves little

The warnings run from 50% to 100% of a 1M window every 25k tokens: about 20 per session at about 80 tokens each, some 1,600 tokens, re-read at cache-read prices. That is noise next to one compaction. The cost the history records was behavioural: a held stop put a paragraph about the context into every turn. Token savings are a weak reason to hide the signal.

### Who knows where the clear point is

A compaction costs least at a phase boundary: the commit is green, nothing is in flight, no question waits on the owner. A mod can see that a turn ended, that the tree is clean, and the context figure. It cannot see whether the model is half way through a multi-turn step, or whether the turn ended on a question the owner has not answered. Only the model knows that. So the design question is which party says "this is a clear point".

| Option | Who decides | What runs | Risk |
| --- | --- | --- | --- |
| A. Port as is | The model, warned | The mod measures in-process with the engine's window and warns the model as today. The owner runs `/session-kit:handoff` and `/compact`. | None new. I5 stays unmet: the owner still has to act. |
| B. The model signals, the mod acts | The model, warned | The mod registers a tool (`$.tool.register`), say `clear_point`, and warns as today. At a clear point the model calls it. When that turn ends the mod runs the handoff, compacts, then submits a continue prompt that also says to read again the documents `CLAUDE.local.md` lists. If the handoff's Next step waits on the owner, the mod stops after the compaction, and the band shows that the next step is the owner's. | A model that calls the tool at the wrong moment. The warning text and the tool's description carry the definition of a clear point. |
| C. The mod decides alone | Heuristics | At `turn.complete` past the threshold, with a clean tree and a final message that asks nothing, the mod runs the chain. The model never reads a warning. | Compacts mid-step whenever the heuristics misread. A missed question to the owner gets "continued" past. |

B fits I5 and leaves with the model the judgement only it can make. The model still reads the warning, at a token cost shown above to be small.

Two refinements, for either A or B:

- A backstop for the engine's own compaction. When the context hits the engine's threshold, the compaction comes without a handoff. A `session.compact` hook on `trigger: "auto"` can add instructions that make the summary keep the task, the decisions and the next step. It cannot run the handoff first, since that needs a model turn.
- One model call instead of two (to try, unverified). The handoff turn and the compaction each read all of the context. The `session.compact` hook could tell the summariser to write its summary in `CLAUDE.local.md`'s fields, then write the file from the summary it gets back (`SessionCompacted.messages` holds it). The summariser has no tools, so it cannot check `git status` or the last test run the way the skill can. Measure the two summaries side by side before choosing.

## One task per context

Nothing serves I3 today. Three ways, cheapest first:

1. A rule in `global/CLAUDE.md`: when a prompt is unrelated to the task in `CLAUDE.local.md`, name the mismatch and propose `/session-kit:handoff` then `/clear` before starting. Costs nothing. It is prose, which is the kind of rule I6 exists because prose fails to hold.
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

1. Context, as option A: the mod measures with the engine's window, warns the model through the tool result's `context`, and draws a band. `context_pressure.py` is retired. Measure the hook times before and after.
2. The chain, option B, behind a `userConfig` toggle, off by default until it has run in a few real sessions.
3. `test_log`, `doc_length`, `nudge_single_edit` move in-process. Small, and they retire three Python starts on a Bash call.
4. The guard, once the mod-ordering question is answered. Both guards run side by side for a while, the mod failing closed and the settings hook as it is.
5. One task per context, after the owner picks a way.
6. Stay as settings hooks: `session-tells`, `format.py`, `direnv_env.sh`, `pyright_env.py`.

The mods API is early access and moves between releases. The settings hooks ride a stable contract. That argues for keeping the guard's settings hook even after the mod guard lands.

## Open questions for the owner

1. Are the intents right? Correct I4 and I6 to I11 especially, which are inferred.
2. The context chain: A, B or C? Should the chain ever submit "Continue" without the owner, or stop after the compaction every time?
3. One task per context: which of the three ways, and is a Haiku call per prompt acceptable for the third?
4. Where the documentation lives in `session-kit`: a `docs/intent.md` beside the README, or the README itself?
5. Is the 1M window the only one in use? With the engine's figure it no longer matters for the port, but it decides whether the current hook has been silent on some sessions.
