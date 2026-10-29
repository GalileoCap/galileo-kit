# Where we stand, in plain words

Written 2026-10-25 for the owner, who asked for the project as a newcomer would meet it. Rewritten whole each time it is asked for. The record behind it is `docs/intent/` and `docs/PLAN.md`. This file names things by what they are and keeps the ids in parentheses for the reader who wants the file.

## What this repository is

Your whole setup for working with agents, in one place. It has three layers.

1. The rules. `global/CLAUDE.md` is imported by an `@` line in `~/.claude/CLAUDE.md`, so every Claude Code session on this machine loads it, in every project. Each rule is one bold sentence with its mechanism, and `global/RATIONALE.md` carries the reason under the same heading, read on demand. `global/CODE.md` holds the rules about the shape of code, which a project takes by importing it. `global/goals-objectives-actions.md` is the process behind the record of intent, with its prior art beside it.
2. The plugin, `session-kit`. The repository is a Claude Code plugin marketplace holding one plugin, which enforces some of the rules in-process, keeps the handoff, and puts nine commands on the Bash tool's PATH.
3. The record. `docs/intent/` holds why the project is what it is, one file per entry, and `docs/` the research, the reviews, the analyses, the measurements and the plan.

The repository was `claude-kit` and then `claude-mods` before the two merged under this name on 2026-10-24. The kit's own goals are the merged project's goals, and the rules it ships are its own actions, so the kit is a project like any other under its own process.

## The rules, in one paragraph each

How to work: say what you are about to do, then do it. Be critical of every decision, the owner's included. No abstraction before its second use. When a signature changes, the typechecker finds the callers, and a sweep over ten sites or more goes through a parser such as `ast-grep`. A mechanical unrelated failure is fixed in its own commit and named, and one that needs a decision is reported. A fix that has failed twice stops and shows evidence. A deliverable is a file, and an Artifact is refused. A new document gets its index line in the commit that adds it. A touched file leaves with fewer prose tells. A temporary file is scoped to its writer.

Intent: what is kept gets an entry. Goals in your words, objectives you approve, actions a session decides and you validate after the fact, constraints that hold whatever is built. Links go upward only, and nothing is deleted: a validated action is superseded by a new one. The tools hold the record, and an id is never written without its name.

Sessions: one task per context. A compaction is asked for at a clear point, after a commit and a handoff. After a compaction the documents the work rests on are read again in full. Memory holds preferences and feedback, and the project's state lives in its files.

Git: commit proactively, deliver green, work only in your own checkout and on your own branch, and never push or publish unless asked. The guard refuses outright `git commit --no-verify`, `git reset --hard`, an amend of a pushed commit, a force-push and a bare stash. What a change leaves to do outside the code is an entry in `OWED.md`.

Gates and tests: zero warnings. The rulebook every turn loads has a word budget of 7,500. A suppression carries its reason in place and the index lists them. Test output goes to a file, which is then searched, and the guard refuses a pipe inline, `-x` and shell `timeout`. A run that may last goes through `session-watched`. A slow test is a smell. Blind tests are scaffolding, written before the code and deleted before done, three kinds kept. A defect fix lands with its regression test. Each test proves a sentence nothing else proves. Done means it was run.

## The plugin, piece by piece

`plugins/session-kit/` at version 0.20.0. The engine loads one hooks module per plugin, `hooks/kit.tsx`, which calls one file per concern beside it, each with its tests, run against the engine itself by `claude plugin test`.

- The context module (`context.tsx`, `A16` context measured in-process). After every tool call it reads the engine's own token figure and, from 250,000 tokens, tells the model to find a clear point, every 25,000 tokens, firmer at 500,000 and at 750,000. A band above the prompt shows you the count. The engine's own automatic compaction gets the handoff's fields (`A18`, the backstop). With the `chain` option on, off by default, the model gets a `clear_point` tool, after which the handoff, the compaction and a continue prompt run without you (`A17`, the model signals and the mod acts), and a `new_task` tool for a prompt that changes subject, after which the band offers the handoff and a clear, or to keep going (`A19`, one task per context).
- The checkout checks (`checkout.ts`, `A25`): a context block when `CLAUDE.local.md` is missing or older than the last commit, and a dim line at the end of a turn counting uncommitted changes.
- The suppression warning (`suppressions.ts`, `A39` suppressions justified in place): after an edit that writes `noqa`, `type: ignore`, `@ts-ignore` and the rest, the model is told to write the reason beside it and to regenerate `docs/suppressions.md`.
- The single-edit nudge (`A7`), the document-length cap (`A8`) and the test log (`A11`), each a small in-process hook.
- Still as settings hooks, scripts the engine spawns. The guard (`guard.py`, `A6`) refuses the git and test-run commands the rules mark as refused, and the Artifact tool. The formatter (`format.py`, `A10`) formats what an edit wrote with the project's own tools. The direnv environment (`A12`) and the root `pyrightconfig.json` for multi-package repositories (`A13`) set up the project. The prose-tells hook (`A9`) lists the machine-prose habits an edit wrote.
- Two skills: `/session-kit:handoff` writes `CLAUDE.local.md`, the live state a session reads first after a compaction (`A5`), and `/session-kit:iterate` is the fast-working mode while you iterate, static checks after each change and the tests once at the end (`A34`).
- Nine commands on PATH. `session-tells` lists and checks prose tells (one rule per habit, each self-tested, 129 tests). `session-codeintel` is the code-intelligence package: pinned `ast-grep`, `ruff` and `import-linter`, rewrite recipes, the looks check (`A30`), the layers pack that writes the pure-core gate (`A31`), the code measure (`A33`), the quality gates (`A35`: duplicates, fallbacks and file length, every site judged in `quality-ledger.toml`), the project template (`A36`: three base files a package's configs extend, with a drift check) and `pyright-env`. `session-intent` indexes and checks the record, prints names and allocates ids under a lock (`A21`, `A27`, `A40`). `session-transcripts` reads every session's transcript and writes the reports under `docs/measurements/` (`A22`). `session-suppressions` lists, indexes and checks the suppressions. `session-rulebook` counts the loaded words against the budget (`A28`). `session-docs` checks that `CLAUDE.md` names every document (`A29`). `session-watched` runs a command and ends it with diagnostics after five minutes with no progress (`A37`). `session-owed` lists what a range of history owes (`A38`). All but the two packages are standard-library Python or bash, each with its cases.

A project configures the kit in `.claude/claude-kit.json`: its test commands, its rulebook budgets, its documents root, its looks and layers, its measured areas, its quality areas and ledger, its owed file, its suppressions index, its intent directory and levels, and the static legs the iterate skill runs. The kit's own settings file is the example.

## The record

Sixty-six entries under `docs/intent/`: five goals in your words (`G1` the way you work with agents, through `G5` the vulnerability surface), eighteen objectives, one constraint and forty-two actions. `INDEX.md` is generated and leads with what waits on you. The project's `CLAUDE.md` lists the goals, the approved objectives and the entries that wait, and `session-intent check` holds the two together.

The documents: `docs/PLAN.md` (done, candidates, next, open questions, deferred), `docs/claude-code-mods-research.md` (how plugins and mods work and every path by which installed code changes), `docs/session-kit-port.md` (the analysis behind the port), `docs/session-tooling-design.md` (the shape of the transcript tooling), `docs/what-reaches-the-model.md` (every text the kit puts in front of a session, which you reviewed), `docs/analyses/tagents-and-generic-app.md` (your two projects read for the kit), `docs/reviews/cache-tax.md` (the only candidate reviewed so far), `docs/measurements/` (hook times, two session reports, one code measure) and `docs/suppressions.md` (generated).

## How it got here

- 2026-10-11 and 12: the kit cut from `tagents`, your long-lived project: the hooks, the handoff, the commands and twenty-seven rules.
- 2026-10-22 to 24: the research on plugins and mods, the review of `cache-tax`, and your decision to port `session-kit`'s hooks to a mod before weighing any other mod. The process set, rethought against prior art, corrected three times, and confirmed. `claude-mods` merged into the kit, the goals written in your words, the objectives approved.
- 2026-10-24 and 25: the port, step by step, the kit working after each. The intent tool, then the transcript reader, whose first report moved the warning threshold the same day, and your archive of 381 sessions read to confirm the tiers. Clear communication made an objective (`O18`) when the ids stopped meaning anything.
- 2026-10-25: your two projects read for the kit, and the analysis's order built through: the checkout checks, the suppression check, the id allocator, the rulebook budget, the docs check, the looks check, the layers pack, the code-shape rules, the code measure, the iterate skill, the quality gates, the template, the watched run and the owed record.
- 2026-10-25, last: you read `docs/what-reaches-the-model.md` and changed four rules. Suppressions are justified in place and indexed instead of approved (`A39`). The intent levels come from the settings (`A40`). History in a loaded document is a tell (`A41`). A mechanical unrelated failure is fixed by the session (`A42`). The global rules gained an Intent section inline.

## What is done and what is proven

Everything above is committed on `main`, 42 commits since the remote's `086e6aa`, and none of it pushed. You asked to hold the push.

At 0.20.0: the hooks module's 36 engine tests pass and its types check against the 2.1.308 engine the desktop app bundles. The intent tool has 44 cases, the suppressions tool 16, the transcript reader 18, the watched run 17, the owed record 11, the tells 129 tests, the code-intelligence package 56. Both packages' gates are green at zero warnings. The kit's own gates are green: the record checks, the seven suppressions carry their reasons and the index is current, every document is named, the rulebook stands at 4,462 of 5,000 words, and the quality gate holds 156 judged sites.

## What is not proven

No module, skill or command has run in a real session. Everything is proven by the engine's test harness and the commands' own cases. The install path pulls from GitHub, so a real run waits on the push, or on a marketplace added from the local checkout. Neither the template nor the quality gate has run over a project outside the kit. The chain is built and tested and has run nowhere, so it stays off.

## What waits on you

- The push. It unblocks the real-session run of every module and the install on your other projects.
- Six findings in `quality-ledger.toml`, each raised for you to fix, keep or re-class: the guard failing open when git cannot answer, a settings file that does not parse dropping the test commands, an allowance without a reason, a file the tokenizer refuses counted short, an unreadable file searched for no marker, an uncounted bad transcript line.
- Three objectives to approve or cut: commands run with the project's own tools (`O14`), routine work takes the cheaper path (`O15`), a document the work rests on is read whole (`O16`). One constraint to state or strike: the kit is never the reason a session fails, the guard excepted (`C1`).
- Mod ordering: whether a mod's refusal runs before another installed mod's approval. The guard's mod form, the last step of the port, waits on the answer.
- The analysis's remaining questions: tagents' rule ownership against the kit's, whether your projects' records converge on the ladder, the handoff project template.
- Forty actions to validate, listed first in `docs/intent/INDEX.md`. Nothing waits on them.

## What is next, in order

1. After the push: install 0.20.0 and watch one real session: the warning and its band, the checkout checks, one `clear_point` run end to end with `chain` on, one press of each `new_task` button. Then `chain` on by default.
2. The transcript reader's `rules` command and, after the first real session, the measuring module that records what each hook did.
3. The reference mod (`A24`), which draws the name beside each id in a reply.
4. The guard as a mod, once mod ordering is answered, then the `cache-tax` decision against the context module.
5. Your projects taking the kit: generic-app committing its impact report and taking the layers pack, tagents moving its quality ledgers and its watched and owed scripts to the kit's commands.

## Where to look first

Read `CLAUDE.md` at the root, then `global/CLAUDE.md`, then `docs/intent/INDEX.md`. `README.md` is the table of every piece of the plugin with its event and what it does, and the configuration and the tests. `docs/PLAN.md` is the order of work. `CLAUDE.local.md`, uncommitted, is where the last session left off.
