# Working rules for every project

These come from `session-kit` (`global/CLAUDE.md`). A project's `CLAUDE.md` adds to them and wins where it differs. Each rule's reason is under the same heading in `RATIONALE.md` beside this file: read it before arguing with a rule. A pure-core project also imports `CODE.md`. The plugin's commands (`session-intent`, `session-docs`, `session-tells`, `session-suppressions`, `session-rulebook`, `session-owed`, `session-watched`, `session-codeintel`, `session-transcripts`) are on PATH, each with `--help`.

## How to work

- **Say what you are about to do, then do it.** Restate a multi-part ask and its deliverables, and ask clarifying questions before the work starts. Then work autonomously and record the assumptions you made.
- **A tagged line is handled as its tag says.** `Do:` is an order, open until reported. `Decide:` is a binding answer, recorded and not reopened. `Ask:` is a question, answered with no edits and no runs that write. `Later:` is deferred work, written to the plan. `FYI:` is context, with no action. The reply ends with one line per item, in the form the kit's context gives, then each untagged line it acted on with the tag it read, then the owner's questions.
- **Be critical.** Question every design decision, the owner's included, and offer the better alternative.
- **No abstraction before its second use.** No Protocol layer, plugin system or extension point until a second implementation exists. Use third-party types directly.
- **When a signature changes, the typechecker finds the callers.** Its error list after the change is the ground truth. For what the types cannot see (a string key, a reflective call, a config file), search the text and read every hit.
- **A mechanical sweep goes through a parser.** About ten sites or more change through a tool that matches syntax, such as `ast-grep`, from a tested rule (`session-codeintel recipes list`) tried on a planted case first. A regex does not qualify. Below ten, edit each by hand.
- **An unrelated failure is fixed when the fix is mechanical, and named either way.** A fix that changes no behaviour and needs no decision goes in its own commit, and the reply names it. Any other is reported in one line with a proposed next step, and never called flaky.
- **A fix that has not worked after two tries stops and shows evidence.** Hand back what was tried and what happened. A mismatch between layers is fixed in the layer that holds it.
- **You own what you grew.** A gate your change trips is yours to answer in your own commit, and a file you push past a length cap is yours to split.
- **A deliverable is a file.** A report, plan or diagram asked for is written as a local file and answered with its path.
- **A new document gets its line in the index in the commit that adds it.** `session-docs check` holds it.
- **A file you touch leaves with fewer prose tells.** Write none, and remove those in the comments and prose of every file you edit by rewriting the sentence: a dash swapped for a comma is the same sentence. A comment that tells history is deleted. Quoted text and strings a test asserts on stay. `session-tells show <file>` lists a file's.
- **A temporary file is scoped to whoever wrote it.** Name it after the session or the worktree, or make it with `mktemp`.

## Intent

The record of why a project is what it is, one file per entry under `docs/intent/`. The process is `goals-objectives-actions.md` beside this file: read it before writing an entry. Only the owner states a goal, and an objective needs the owner's approval. A session decides actions, which the owner validates after the fact.

- **What is kept gets an entry.** A rule, a design choice, a plan of several phases or a decision a later session relies on. A one-off task writes nothing.
- **An entry is filed at the level it is.** A goal is why the project exists, and no piece of the work completes it. An objective is a change seen from outside that names no mechanism. An action is the mechanism. A request of the owner's goes at its own level with the owner as its source, and when no goal fits it, ask the owner why they want it.
- **Links go upward only, and nothing is deleted.** A validated action is never rewritten: a new action supersedes it and the old one is retired.
- **The tools hold the record.** `session-intent next <level>` gives an id, `index` regenerates `INDEX.md`, and `check` is the gate.
- **An id carries its name.** Any id (an entry, an issue, a ticket) is written with its name at its first mention in a reply and in each section of a document the owner decides from. `session-intent names` prints them.

## Sessions

- **One task per context.** A prompt unrelated to the task this context holds is named as such before anything starts on it. A new or just-cleared context takes the prompt as its task, whatever `CLAUDE.local.md` describes. Call the `new_task` tool and end the turn, or without it propose the handoff and `/clear` in one line.
- **Ask for a compaction at a clear point.** Past 150,000 tokens of context, at a boundary between two phases of work, commit, write `CLAUDE.local.md` (`/session-kit:handoff`) and end the turn asking to compact.
- **After a compaction or a clear, read again in full the documents the work rests on**: those `CLAUDE.local.md` lists and any the owner named.
- **Memory holds what crosses conversations: preferences and feedback.** A project's state lives in its files. A note goes where it belongs: a rule in `CLAUDE.md`, deferred work in the plan, a preference in memory.

## Git

- **Commit proactively**, whenever a logical unit is complete.
- **Never deliver red.** What is handed back as done is green on the gates and the tests the change reaches. A project may let an integration branch go red when its rules name who proves the union. A fix that failed twice is delivered red with its evidence.
- **Work only in your own checkout and on your own branch.** Never merge, rebase, cherry-pick or pull another branch into yours, or commit to one that is not yours, unless asked.
- **Refused outright:** the guard refuses these and says the alternative: `git commit --no-verify`, `git reset --hard`, amending a pushed commit, a force-push without lease, a bare `git stash` or `stash pop`, a test run piped into a filter or stopped at `-x`, a shell `timeout` around a call, and an Artifact.
- **Publishing is the owner's.** Never push, open a pull request or publish anything unless asked.
- **What a change leaves to do outside the code is written in `OWED.md`.** A step a deploy, a sync or another worktree has to take is a `###` entry, in the commit that makes it owed, under a `##` section naming when it is due. An entry is never removed.

## Gates and tests

- **Quality gates are zero warnings.** A warning is a failure, and the bar is not lowered to pass it.
- **The rulebook has a word budget.** `session-rulebook` holds what every turn loads, and the skills apart, to `rulebook` in `.claude/claude-kit.json`. A rule that takes the rulebook over removes another.
- **A suppression or a type escape carries its reason in place, and the index lists them.** Each marker (`noqa`, `type: ignore`, `@ts-expect-error`, `Any`, a cast out of `object` or `unknown`, a rule relaxed in config) has a few words of why on its line or the line above. `session-suppressions index` writes `docs/suppressions.md`, and `check` is the gate.
- **No run goes on without a decision.** A run that may last goes through `session-watched -- <command>`, which ends it after five minutes without progress with exit 125 and its diagnostics. Report their path.
- **A slow test is a smell, and a danger until it is acknowledged.** Give every test a timeout of a few seconds. One that needs more stays only when the owner accepts it, with its reason beside it. A cap is never raised to fit a run.
- **Blind tests are scaffolding.** Before the code, write the tests from the behaviour asked for alone. Before calling the work done, delete them, except a defect's regression test, a test of what the project promises other systems, and a test of a rule whose failure is silent and costly (permissions, money, lost data, secrets).
- **A defect fix lands with a regression test that failed before it.**
- **Each test proves a sentence nothing else proves.** Name the sentence first and check that no typechecker, test or gate proves it already. Prefer one file with a few pointed cases.
- **Done means it was run.** Before saying a feature is done, drive it the way its user would (the screen, the real call, a real model) and say which scenarios ran, which did not, and why. While the owner iterates, `/session-kit:iterate` runs the static checks alone and the tests once at the end.
