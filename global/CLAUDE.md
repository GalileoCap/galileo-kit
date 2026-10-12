# Working rules for every project

These come from the `session-kit` repository (`global/CLAUDE.md`). A project's own `CLAUDE.md` adds to them and wins where it says otherwise.

- **Say what you are about to do, then do it.** Restate a multi-part ask and its deliverables before exploring. Ask clarifying questions up front rather than mid-flight. Otherwise work autonomously and record the assumptions you made, so they can be reviewed.
- **Ask for a compaction at a clear point.** Between two phases of work (the build finished and the checks not yet run, a review requested, a question answered and its work not started), commit, write `CLAUDE.local.md` (`/session-kit:handoff`) and end the turn asking to compact. Under 30% of the context window, skip the ask. The `session-kit` hooks warn from half the window and hold a long turn's end until the reply says whether it is safe to compact.
- **Surface unrelated failures immediately.** A failure that is not yours is never fixed silently and never called flaky. One line saying what failed and a proposed next step, usually a follow-up commit.
- **A fix that has not worked after two tries stops and shows evidence.** State what was tried and what happened, and let the owner or the next reader decide, rather than looping a third and fourth time blind. A mismatch between layers is fixed where it is, never papered over in the layer that consumes it.
- **A deliverable is a file.** A report, plan, diagram or summary that was asked for is written as a local file and answered with its path. Never publish a Claude Code Artifact, and never offer one.
