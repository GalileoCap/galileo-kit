# Why the rules are the rules

`CLAUDE.md` in this directory is the rulebook every session loads. This file is the argument behind it: what goes wrong without each rule, and the case that produced it where there was one. The cases come from the project these rules were first written in, a monorepo worked by several Claude Code sessions at once, one per git worktree.

**Reading it is optional.** It is not loaded into a session. Open it when a rule looks arbitrary, when you are about to argue with one, or when you need to know whether the case in front of you is the case a rule was written for. Every rule in `CLAUDE.md` works without it.

**Nothing here binds.** If this file and `CLAUDE.md` disagree, `CLAUDE.md` wins and the difference is a bug in this file. The headings and the rules' lead words are the same in both, so a rule and its reason are found the same way.

## How to work

**Say what you are about to do, then do it.** Restating a multi-part ask puts a misreading in front of the owner before any work is spent on it. A question asked mid-flight reaches an owner who has moved on, and work done on a guess is thrown away when the guess was wrong. Working autonomously with the assumptions written down lets the owner review a choice nobody asked them about.

**Be critical.** An agent that agrees with every design carries the owner's mistakes into code, where they cost more to undo. The owner asked for the better alternative to be named every time, their own designs included.

**No abstraction before its second use.** An interface drawn from one implementation encodes that implementation's accidents. The second use is what shows which parts vary. Until it arrives, the layer is one more thing every reader crosses and one more place every change touches. A third-party type used directly keeps its own documentation.

**When a signature changes, the typechecker finds the callers.** A text search for a name misses aliases, re-exports and calls through a variable, and finds comments and strings. A language server can be wrong in the quiet way: one started at the root of a repository of several packages found 2 of 50 call sites until it was configured per package, and said nothing about the other 48. The typechecker reads the program the runtime will run, and its error list after the change is complete for everything the types can see.

**A mechanical sweep goes through a parser.** A regex matches characters, so it also matches inside a longer expression, in comments and in strings, and misses a call split over two lines. In the first project about 200 call sites had to be awaited when a store's methods went async. The regex sweep matched `store.history(` inside `harness.store.history(` and wrote `harness.await store.history(`, and it awaited all of `f(x)[-1]`, which awaits the subscript of a coroutine. A parser sees the attribute chain as one node, and a tested rule carries the extra pass the precedence case needs. Below about ten sites the rule and its planted case cost more than the sweep, and the typechecker after a hand edit catches what a slip leaves.

**Surface unrelated failures immediately.** A failure fixed without a word loses its cause and whoever owns it. One called flaky stays in the suite and teaches everyone to rerun until green. A deterministic suite has no flaky tests until one is shown to be, and that showing is the finding.

**A fix that has not worked after two tries stops and shows evidence.** A third attempt made blind usually repeats the first two with variations. Evidence lets somebody with other context decide, and it costs less of their time than the loop costs. A mismatch papered over in the consuming layer leaves the producing layer wrong for every other consumer.

**You own what you grew.** The seam a split needs is usually visible to whoever just worked in the file and to nobody else. A tripped cap left for a later cleanup is found by someone who has to learn the file first. In the first project a file went from 300 code lines to 315 when its handlers gained a parameter, and the session that added the parameter made the split.

**A deliverable is a file.** A published page is not versioned with the code it describes: it cannot be read at a commit, it does not travel with a branch, and nobody reviews it with the change. A document that outlives the tree it describes is a document nobody can check.

**A file you touch leaves with fewer prose tells.** Machine-written prose carries habits (the em dash, `X, not Y`, intensifiers, signposting, history in comments) that make a reader skim it and trust it less. The first project measured some 27 000 em dashes in its docs alone: too many for a sweep that reads and judges each one, and a mechanical swap of the mark leaves the sentence as it was. A file being edited is a file being read, so the removal costs a minute there and the counts fall with the work. A history comment goes stale the day it is written, and the commit already holds that history.

**A temporary file is scoped to whoever wrote it.** In the first project a hook wrote every worktree's last test run to one fixed path under `/tmp`, so each session read whichever run had finished last, from any worktree.

**What is kept gets an entry in the project's intent.** A decision kept without its reason is decided again by the next session that meets it, and a session that agrees with whatever is in front of it carries a stale decision as far as a right one. The ladder from a goal to an action makes every kept piece say what it serves, so a session can see when an action has lost its objective, and the owner approves at the level where the words are theirs. The one-off exemption is there because the process costs a file per entry, and a task whose result dies with the session has nothing for the file to hold. The process is in `goals-objectives-actions.md` beside this file, and what it borrows from OKRs, ADRs, impact mapping and the rest is in `goals-objectives-actions-prior-art.md`.

## Sessions

**Ask for a compaction at a clear point.** A compaction costs least where nothing is in flight, and a phase boundary is such a place whatever the context's size. A warning that arrives mid-task reads as permission to finish the task: one session reached 70% of its window after seven warnings inside a single turn, and the reply that ended the turn never mentioned compacting. So the rule names the boundaries. Holding the end of every long turn until its reply spoke of compacting was tried, and it put a closing paragraph about the context into each one: the warnings and the named boundaries carry the signal at less cost.

**After a compaction or a clear, read again in full the documents the work rests on.** A summary keeps what a document concluded and drops the conditions it was concluded under. The next decision often turns on those: which option held only if something else was true, or what the failure path was.

**Memory holds what crosses conversations: preferences and feedback.** Memory is one machine's and one tool's, and invisible to review. A project fact kept there goes stale with nobody placed to correct it, and later contradicts the file that did get updated.

## Git

**Commit proactively.** Uncommitted work is lost to a crash, a wrong checkout or another session's stash. A commit is the unit the owner can read, review and revert.

**Never deliver red.** What is handed back as done is what others build on, and a red delivery moves the debugging to someone without the context. Green means the checks the author was asked to run. A whole suite before every merge made each change wait on every other one, and a project with an integration branch and someone who proves the union may let that branch go red for a while. The exception is the two-tries rule seen from the other side: a fix that failed twice is handed back with its evidence instead of looping.

**Work only in your own checkout and on your own branch.** Every worktree of a repository shares one stash stack, with no lock and no owner marker, so a bare `git stash pop` can restore another session's work into your tree or lose yours into theirs. A branch that rebases under the one it merges into merges twice, strands a live worktree mid-conflict, and breaks every commit id it published.

**Refused outright.** `--no-verify` skips the checks a commit claims to have passed. `reset --hard` destroys uncommitted work with no way back. Amending a pushed commit forks every clone that has it. A force-push overwrites whatever others pushed since, where `--force-with-lease` refuses when the remote moved.

**Publishing is the owner's.** A push or a published page reaches people, and may be cached or indexed even after it is removed. When work is seen is the owner's decision.

## Gates and tests

**Quality gates are zero warnings.** A gate that tolerates warnings stops being read: a new warning arrives among fifty old ones and nobody sees it. At zero, every new one is visible the moment it appears.

**Suppressions and type escapes need the owner's approval.** Each one decides that the check is wrong at this site, and they accumulate without anybody deciding that in aggregate. Refactor, suppress or re-scope is a trade-off with costs on each side, and the owner is the one who carries them. Deleting a suppression only gives a check back.

**Test output goes to a file.** Piped into `head`, `tail` or `grep`, a run keeps only what the filter guessed, and a second look means running the suite again. `-x` hides every failure after the first, so a change is proved one failure at a time. A shell `timeout` around a call duplicates the tool's own cap in another unit (seconds against milliseconds), and its kill truncates a summary into something that reads as a failing gate.

**A slow test is a smell, and a danger until it is acknowledged.** A test that takes seconds is usually waiting on something real: the clock, the network, a lock, a race that happens to pass. Each slow test is fine alone, and a suite slows by their accumulation until every run pays for all of them. A per-test timeout makes the cost visible when the test is written, and an acknowledged slow test says why it is allowed. Raising a cap so a run fits removes the signal that said something changed.

**Blind tests are scaffolding.** A test written with the code in view agrees with whatever the code does, bug included, and proves nothing a reviewer could not see by reading the diff. Written from the behaviour asked for, it can disagree with the code, and that disagreement is the defect it exists to find. Kept forever, the same tests pin the code in place and make every run slower: the first project's suite grew past 1 400 backend tests and its runs became most of a change's time. So they prove the change and leave with it. The kinds kept have earned a place. A defect has shown where the code is fragile. A promise to other systems breaks someone outside when it moves. A rule whose failure is silent (a permission, money, lost data, a secret) is noticed only by a test: when a demo of the first project widened what members could read, the tests refusing them were the only signal that a permission had changed.

**A defect fix lands with a regression test that failed before it.** A test that never failed may not reach the defect at all. Seeing it red first is the proof that it does.

**Each test proves a sentence nothing else proves.** Every test costs time in every run and friction in every change near it. The first project's suites grew past 1 400 backend tests and 160 console test files, and a review found the same shapes throughout: a whole page mounted to read one string, one rule tested over every member of a table, and one behaviour proved by a unit file and an end-to-end file side by side.

**Done means it was run.** A test proves the code does what the test's author expected of it, and a mock proves the code agrees with the mock. Neither shows that the feature behaves when a person drives it, which is the claim "done" makes.
