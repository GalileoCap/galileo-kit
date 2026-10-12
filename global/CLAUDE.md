# Working rules for every project

These come from the `session-kit` repository (`global/CLAUDE.md`). A project's own `CLAUDE.md` adds to them and wins where it says otherwise. The rules marked **(refused)** are enforced by the plugin's guard and no longer depend on being read.

## How to work

- **Say what you are about to do, then do it.** Restate a multi-part ask and its deliverables before exploring. Ask clarifying questions up front rather than mid-flight. Otherwise work autonomously and record the assumptions you made, so they can be reviewed.
- **Be critical.** Question every design decision, the owner's included, and offer the better alternative when there is one.
- **No abstraction before its second use.** No Protocol layer, plugin system or extension point until a second implementation exists. Use third-party types directly.
- **Surface unrelated failures immediately.** A failure that is not yours is never fixed silently and never called flaky. One line saying what failed and a proposed next step, usually a follow-up commit.
- **A fix that has not worked after two tries stops and shows evidence.** State what was tried and what happened, and let the owner or the next reader decide, rather than looping a third and fourth time blind. A mismatch between layers is fixed in the layer that holds it.
- **You own what you grew.** A gate your change trips is yours to answer, in your own commit, even when that means a structural edit to a shared file. A file you push past a length cap is split by you, at the seam it shows.
- **Ask for a compaction at a clear point.** Between two phases of work (the build finished and the checks not yet run, a review requested, a question answered and its work not started), commit, write `CLAUDE.local.md` (`/session-kit:handoff`) and end the turn asking to compact. Under 30% of the context window, skip the ask. The plugin's hooks warn from half the window and hold a long turn's end until the reply says whether it is safe to compact.
- **A deliverable is a file.** A report, plan, diagram or summary that was asked for is written as a local file and answered with its path. Never publish a Claude Code Artifact, and never offer one. **(refused)**
- **A file you touch leaves with fewer prose tells.** Write none in what you add, and remove those already in the comments and prose of every file you edit, whether or not they bear on the change. Remove a tell by rewriting the sentence: a dash swapped for a comma is the same sentence. A comment that tells history (an issue number, a date, `used to`) is deleted. Quoted text and a string a test asserts on stay as they are. The plugin's hook lists the tells an edit wrote; `session-tells show <file>` lists a file's.
- **A temporary file is scoped to whoever wrote it.** Sessions on one machine run at the same time, so a fixed name under `/tmp` is last-writer-wins. Name it after the session or the worktree, or make it with `mktemp`.

## Git

- **Commit proactively**, whenever a logical unit is complete. Never leave finished work in the working tree.
- **Never deliver red.** What is handed back as done (a reply saying it is finished, a merge request, a push) is green. The exception is a fix that has failed twice, which is delivered red with its evidence.
- **Work only in your own checkout and on your own branch.** Run every command from it. Never merge, rebase, cherry-pick or pull another branch into yours, and never commit to a branch that is not yours, unless asked. The stash is shared by every worktree of a repository: never a bare `git stash` or `git stash pop`; use a WIP commit, or `git stash push -m <tag>` and apply by SHA. **(refused)**
- **Refused outright:** `git commit --no-verify`, `git reset --hard`, amending a commit already on a remote, and a force-push (`--force-with-lease` is fine). **(refused)**
- **Publishing is the owner's.** Never push, open a pull request or publish anything unless asked.

## Gates and tests

- **Quality gates are zero warnings.** A warning is a failure, and the bar is not lowered to pass it.
- **Suppressions and type escapes need the owner's approval**: `noqa`, `type: ignore`, `pyright: ignore`, `@ts-ignore`, `@ts-expect-error`, `Any`, a cast out of `object` or `unknown`, a rule relaxed in config. Surface the trade-off, and the owner picks refactor, suppress or re-scope. Deleting one needs no approval.
- **Test output goes to a file**, which is then searched. Never pipe it inline to `grep`, `head` or `tail` (**refused**), never stop at the first failure with `-x` (**refused**), and never wrap a Bash call in shell `timeout`, since the tool has its own (**refused**).
- **Tests are written blind, before the implementation.** Write a test before reading the code it exercises, or hand it to a sub-agent that has not seen that code. A test written with the code in view tends to agree with whatever the code does, bug included. The exception is a test that is necessarily shaped by the implementation, such as one asserting an internal helper's own behaviour, which is written with its code. A blind test may change once the implementation is real: say which and why.
- **A defect fix lands with a regression test that failed before it.** A weak test's fix is the strengthened assertion.
- **Each test proves a sentence nothing else proves.** Before writing one, name the sentence it proves and check that nothing already proves it: the typechecker, an existing test, a gate. Prefer one file with a few pointed cases over a file per module.
- **Done means it was run.** Passing tests prove the code does what their author expected; they do not prove the feature works. Before saying a feature is done, drive it the way its user would: the screen, the real call, a real model where it needs one. Say which scenarios ran, which did not, and why.
