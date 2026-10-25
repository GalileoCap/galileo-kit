# Two projects read for the kit

Read on 2026-10-25, on the owner's ask: what in each project could become a tool of the kit, what could be abstracted into the global rules, and what each project should remove because the kit replaces it. The projects are `~/devel/iquall/tagents/dev` (the long-lived project, 4,733 commits, whose rules the kit was first cut from) and `~/devel/galileo/misc/generic-app` (started this week, 159 commits, built around a functional style with effects marked and checked). Nothing here is decided. Each candidate names what it serves and what it would cost, and the last section lists what waits on the owner.

## What the kit already took from tagents

The project's own inventory, `docs/workflow/claude-kit-inventory.md`, records the move of 2026-10-11 and 2026-10-12: the context warning and its stop hook, the document cap, the single-edit nudge, the git half of the guard, the test-command refusals, the Artifact refusal, the direnv and pyright halves of the environment hook, the formatter, the test log, the handoff skill and its template, and twenty-seven rules into `global/CLAUDE.md`. What follows is what stayed behind and still reads as generic, plus what generic-app adds that tagents never had.

## tagents: tools to lift

| # | What it is there | Why it is generic | What the kit would gain | Cost |
| --- | --- | --- | --- | --- |
| T1 | The SessionStart hook's generic half: worktree, branch, whether `CLAUDE.local.md` exists, `git status`, the last commits. The Stop hook's generic half: uncommitted changes at the end of a turn, a `CLAUDE.local.md` older than the last commit. | Every project has a checkout and a handoff. The two reminders are the mechanical half of "commit proactively" and of the handoff rule. | A `session.start` context and a `turn.complete` check in the context module, both in-process. The stale-handoff check is what the chain and the backstop have no answer for today. | Small. The `turn.complete` hook exists. |
| T2 | `scripts/rulebook`: a word budget on `CLAUDE.md` and the skills together, refused by the gate when over. From the research that instruction-following degrades with stacked instructions. | Every project loads a rulebook on every turn, and the kit's own global file has no budget. | `session-intent budget`, or a check in the rules tool, reading the budget from `.claude/claude-kit.json`, over `CLAUDE.md`, `global/CLAUDE.md` and the skills. The owner's cost in `G4` terms is tokens per turn. | Small. |
| T3 | `scripts/number`: an id allocator behind a mutex, outside every checkout, which reissues no id. Written after four renumberings and two live collisions between lanes. | Any project with several sessions and ids in documents. The kit's own intent ids are picked by reading the directory, which is the race the script was written for. | `session-intent next <level>` claiming the next `G`, `O`, `A` or `C` id under a lock. With the reference mod (`A24`) this is the id side of `O18`. | Small. |
| T4 | `rule_guard.py`'s suppression warning: an Edit or Write carrying `noqa`, `type: ignore`, `@ts-ignore` and the rest is told the marker needs the owner's approval. | The global rule asks for the approval and nothing checks it. generic-app keeps its exceptions as numbered rows in `docs/decisions.md`, awaiting or approved. | A check on Edit and Write that lists the markers written, and a `check` that every marker in the tree names a row in the project's decisions. The second is what turns the rule into a ledger. | Small for the warning, medium for the ledger. |
| T5 | `tagents-quality`: the code map (a generated index of modules by system, freshness-gated), the duplicate gate (a function body in two modules), the fallback finder (`x or v`, `.get(k, v)`, broad `except`, each judged in a ledger), the file-length lint, and `abstract-template`, the package template that carries the quality bar (`ruff.base.toml`, `pyright.base.json`, `scripts/check.base.sh`). | The LLM pitfall register behind them (no memory across sessions, copy the nearest pattern, type appeasement, defensive fiction) is true of every project. The owner's inventory already named the code map as generalisable. | A `session-quality` command with the duplicate and fallback gates and the file-length lint, parameterised by `claude-kit.json`. The template as the kit's project template (`O4`). | Large. The code map's hand-held half (`codemap.toml`) is the part that does not generalise. |
| T6 | `scripts/watched`: no script goes on without a decision. A run with no progress for five minutes is ended with its diagnostics and exit 125, which is no verdict on the code. | Any long run a session starts, in any project. The Bash tool's own timeout kills without diagnostics. | A wrapper the test log could run test commands through, or a rule alone. | Medium. |
| T7 | `OWED.md` and `scripts/owed`: what a change leaves to do outside the code, written in the commit that makes it owed, listed by a range of history at a deploy or a sync. | Every project with a deploy or a shared environment has such steps, and they were lost three ways before the file. | Possibly a rule before a tool: the shape is a file a range of history can be asked about. | Small as a rule. |
| T8 | `/iterate`, fast-working mode: static checks only while the owner iterates, every report ending "tests not run (iterating)", the tests run once at the end, the mode written into the handoff so a compaction keeps it. | The owner iterates on screens in every project. | A kit skill, `session-kit:iterate`, with the project naming its static legs in `claude-kit.json`. | Small. |
| T9 | `scripts/regenerate --check`: the gate regenerates and diffs every generated file, so a hand edit is lost at the next run. | Generated files drift in every project that has them. | A rule first (below). A tool only when a second project generates. | None now. |

Not lifted, and why: `scripts/findings` (GitLab is the project's), `scripts/status` (the kit's `docs/BRIEFING.md` and the intent index answer "where are we" here), the test slot and the offload host (one machine's), `scripts/sync` and `scripts/merge` (the lane workflow), the verifier (a process the global rules already carry as blind tests and "done means it was run").

## tagents: rules to abstract

Each is a candidate action under the objective named. The wording is the project's, cut to what holds everywhere.

- A rulebook has a budget, and a rule that takes it over removes another (`O16`, `G4`). With T2.
- An id comes from an allocator and is never read off a document, because two sessions reading the same file compute the same next number (`O18`, `O6`). With T3.
- The docs are the specification: when the code diverges from them, stop and ask which to keep (`O16`).
- The gate regenerates and diffs every generated file, and a hand edit to one is lost at the next run (`O8`). With T9.
- Structure never changes behaviour, and a fix says that it does: a cleanup commit passes the suite with no test edited, and a test that has to change names a behavioural change, which gets its own commit (`O8`). The project's Q8 and F8.
- A default is declared or it is a fallback, and a fallback speaks or it refuses: a value substituted for an absence is logged, typed or tested by name, and identity, authority and secrecy are never substituted (`O8`, `G5`). The project's Q3, Q4 and the refusal classes. generic-app reaches the same place from the other side with its proofs (below), which is the strongest sign the rule is general.
- Look before you write: before adding a function or a module, search for its home (`O8`). The project's Q2. Without the code map it is a habit, and the duplicate gate is what catches the failure.
- Read before you claim, and cite the line (`O6`). The project's Q12.
- Say what you did not do: a handoff lists what it touched, what it saw and left, and what it could not prove (`O6`, `O12`). The project's Q11, which the kit's handoff template only half asks.
- Two tries, and the second differs from the first in one variable alone (`O6`). The testing doctrine's refinement of the global two-tries rule.
- Does it fail alone? The first question on a red, before any attribution, and a red that passes alone is never attributed to a change (`O6`). Never re-run to green.
- A shared file changes minimally, keeps its names and formatting, and is named in the commit (`O7`). For any repository several sessions work.
- The LLM pitfall register (type appeasement, defensive fiction, test bending, confident completion, name hallucination, each with what it looks like in code) belongs in `global/RATIONALE.md` as the reason behind the code rules, whichever of them move.

One conflict to put to the owner. tagents says "a rule is added on the owner's word alone; a session that thinks one is owed writes it as a doubt". The kit's process says a session decides an action, rules included, and the owner validates after. Both cannot hold in one project.

## tagents: what to remove

| What | Why | Before it goes |
| --- | --- | --- |
| `.claude/skills/handoff/` and `.claude/templates/CLAUDE.local.md` | The kit ships `session-kit:handoff` and a template. The project's copy adds Stack, Intent, Inbox and a ranked open-items shape. | The kit's skill takes a project template when `.claude/templates/CLAUDE.local.md` exists, so the extra fields survive. One small change to the kit. |
| `tagents_quality/tells.py`, `prose.py`, `tests/test_tells.py`, `tests/test_prose_settings.py`, the `tells.toml` ledger | `session-tells` is the same tool moved to the kit, and the project's `claude-kit.json` already configures it (readers, guide, languages, history codes). No `scripts/check` calls the project's copy. | A grep for `tagents-quality tells` over the skills and docs, then delete. |
| The suppression warning in `rule_guard.py` | Once T4 is in the kit. The bare `pytest`, `vitest` and `tsc` rules and the model-name rule stay: they are the project's. | T4 built. |
| The generic halves of the SessionStart and Stop hooks in `.claude/settings.json` | Once T1 is in the kit. The inbox, findings count and worktree title stay. | T1 built. |
| `scripts/codeintel`, the wrapper that pins `session-codeintel` at a commit | The marketplace pins the plugin's version, which is the same guarantee (`O2`). | Confirm the plugin's `session-codeintel` on PATH gives the same engine version the wrapper pins, since the project's rule tests pin the ast-grep version. |
| `CLAUDE.md` §3 "Code and navigation": the typechecker-finds-callers and sweep bullets | They restate global rules. The LSP note and the legacy-branch note are the project's. | Nothing. |

Also for the owner: tagents has its own intent log (`docs/intent/goals.md`, one file per objective with actions as lines, no ids, `Lane:` and `State:` fields) and generic-app a flat `docs/decisions.md`. Neither is the kit's ladder, so `session-intent` reads neither. `O3` says each project owns a copy of the process. Whether they converge, and when, is the owner's.

## generic-app: tools to lift

| # | What it is there | Why it is generic | What the kit would gain | Cost |
| --- | --- | --- | --- | --- |
| G1 | The pure-core rule pack: `py-core-no-io`, `py-core-sync`, `py-shell-declares-effects`, `py-no-raise`, `ts-effects-declared`, the nested `ruff.toml` banning `os`, `time`, `random`, the clock and `uuid` from the core, and the ESLint block banning effect globals, `Date.now`, `Math.random`, `await` and framework imports from `src/core`. Thirty-one ast-grep rules, each with a test, run by `ast-grep test` in the gate. | The pure core and the effect shell are a shape any project can take, and the checks are the shape's definition. The rules name the project's paths only. | `session-codeintel recipes` already ships tested rules. A "layers" pack: the project names its core and shell directories in `claude-kit.json`, and the pack's rules and configs are generated or copied with those paths. | Medium. The `*-through-*` rules ("a Select is written only in `Choice`") are instances of one shape, "X has one home", and a rule generator for that shape would cover both projects' vocabulary rules. |
| G2 | `pnpm looks`: a class string of two or more classes written in two places fails, with an allowlist that names each coincidence's files and fails when it drifts. | Any Tailwind or shadcn frontend. tagents' console had the same disease (fifty-three hand-made dialogs, the loading ladder in sixteen files). | A `session-codeintel looks` command with the allowlist shape. | Small, it is one TypeScript file and its test. |
| G3 | `just docs`: a document under `docs/` that `CLAUDE.md` or the README does not link to fails the gate. | Every project's document list rots. The kit's own `CLAUDE.md` keeps one by hand. | A `session-intent docs` check, or a line in `check`. | Small. |
| G4 | The measurements behind `CONVENTIONS-IMPACT.md`: code lines per area per snapshot, McCabe per function (ruff `C901` at cap 0, a counter on the TypeScript AST), repeated looks per snapshot, run over a `git archive` of each commit. The scripts sit in a scratchpad and will be lost. | `O17` is the system observed and improved. This is the same for the code the system produces. The report found six defects by a convention and a 16% drop in complexity, numbers nothing else gives. | `session-codeintel measure <ref>...`: size, complexity and repetition per snapshot, written under `docs/measurements/`. Rescue the scripts first. | Medium. |
| G5 | The lint-exception table: every relaxation is a numbered row with where, what and why, under "awaiting approval" or "approved", and the code names the row. No marker in the code. | The global rule needs the owner's approval and gives it nowhere to live. | The ledger half of T4: a check that every suppression and every relaxed rule in the configs names a row. | With T4. |
| G6 | The hand-written `Result` with `fail: Fail[E]`, about a hundred lines, chosen over libraries basedpyright cannot check. | A project that takes the functional shape needs one. | A copy in the kit's template, since a project owns its copy (`O3`). | None beyond the template. |

## generic-app: rules to abstract

These are rules about the shape of code, where the global rules today are about how to work. They are candidates for a second global file, `global/CODE.md`, that a project's `CLAUDE.md` imports when it takes the shape, since a shell-script repository or a document project has no core and no shell. Each is in the project's own words, cut to what holds.

- Code is pure by default and an effect names itself: pure code does no I/O, reads no clock and draws no randomness, and lives in the core. Effects live in the shell, and every function there names its effects in a line the gate reads (`Effects:` in a docstring, `@effects` in JSDoc). A function with no effects belongs in the core. Split an effectful operation into pure steps around the effect itself.
- Failures are values. A function returns `Err` or takes a `fail` that lists the errors it may fail with, and the type checker holds every caller to the list. `raise` and `throw` are refused outside the boundary that unwinds them. A failure is handled only at a boundary, in one statement where it can (a combinator), with a `match` only where an arm runs several statements.
- A check returns a proof, and the write takes it with its target, so a write can only act on what was checked. Reads of what a viewer may see take a proof too. Authority is a type. This is tagents' refusal classes made structural, and the two projects agreeing is the case for the rule.
- What leaves the server is a view, a type made to be shown, so a row cannot leave unshaped. A secret shown is a `Redacted`, which only `redact` makes.
- A unit is a type: a moment is a `Millis`, a token a `TokenDigest`, a password a `PasswordHash`. A duration stays an integer.
- A thing shown in two places is a component named for what it shows, made on the second use. A look shared by different things is an entry in a looks file. A page writes neither. (The global "no abstraction before its second use" from the other side.)
- A new document gets its line in the index in the commit that adds it, and the gate fails on one the index misses.
- A lint exception is a numbered row with its reason, awaiting or approved, and never a marker in the code.
- A structural rule is held by a tested gate: the project's "a new component that owns a primitive gets such a rule, with its test" is the general form of tagents' "a shape the vocabulary already names needs a gate, or the next twenty-three arrive the same way".

What the measurements say for the rules' cost: the backend's code shrank by 2.6% and its complexity by 16.5%, the frontend grew by 2.8% with repeated class strings down from 23 to 1, the gates grew from 5 rules to 27, and six real defects were found by a convention turning them into type errors, one of them an access-control leak. That is the evidence for moving the shape, and the kind of number G4 would give for every later change.

## generic-app: what to remove or change

| What | Why | Before it goes |
| --- | --- | --- |
| `CONVENTIONS-IMPACT.md`, `REFACTOR-REVIEW.md`, `REVIEW-WALKTHROUGH.md`, uncommitted at the root | Review notes the sessions wrote, each saying "delete it when you are done". The impact numbers are worth keeping once G4 exists, under `docs/measurements/`. | Rescue the measurement scripts from the scratchpad into the kit (G4). Then delete the three, or commit the impact report under `docs/measurements/` and delete the two reviews. |
| The "Gates" paragraph's suppression sentence in `CLAUDE.md` | The global rule says it. The project part, where the table lives, stays. | Nothing. |
| Nothing else | The project has no hooks, no skills and no scripts of its own that the kit duplicates. | |

To add instead of remove: `.claude/claude-kit.json` naming `just check`, `just test` and `just e2e` as test commands, so the kit's guard, test log and `-x` rule cover `just`. Today they see only the bare runners.

## What waits on the owner

1. Which tools to build first. The session's order, cheapest and most used first: T1 (the session-start and turn-end checks), T4 with G5 (the suppression check and its ledger), T3 (the id allocator in `session-intent`), T2 (the rulebook budget), G3 (the docs check), G2 (the looks check), G1 (the pure-core rule pack), G4 (the code measure, with the scripts rescued now), T8 (the iterate skill), T5 (the quality gates and the template), T6 and T7 last.
2. Whether the code-shape rules go into `global/CLAUDE.md` for every session or into a `global/CODE.md` a project imports when it takes the shape. The session proposes the second.
3. The rule conflict: tagents' "a rule is added on the owner's word alone" against the kit's "a session decides an action and the owner validates". One wins, or tagents keeps its own as a project rule that overrides.
4. Whether tagents' intent log and generic-app's `docs/decisions.md` converge on the kit's ladder, so `session-intent` reads them, and when.
5. The handoff project template (the kit change the tagents removals wait on).
