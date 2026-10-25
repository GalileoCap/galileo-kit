# What reaches the model

Every text the kit puts in front of a session, verbatim or by its source, for the owner's review. Written 2026-10-25 at session-kit 0.11.0. The numbers are the defaults. When a text changes, this file is rewritten from the sources it names.

## Always loaded

- `global/CLAUDE.md`, linked at `~/.claude/CLAUDE.md`: the rules, about 47 lines, in every session on this machine. `global/RATIONALE.md` and `global/goals-objectives-actions.md` are read on demand, when the rules point at them.
- The project's `CLAUDE.md` and `CLAUDE.local.md`, loaded by the engine beside the global rules.
- The `handoff` skill's description, in the skill list: "Write the project's live state to CLAUDE.local.md (uncommitted) so a compaction or a lost session loses nothing. `init` creates it from the template." Its body, `plugins/session-kit/skills/handoff/SKILL.md`, loads when it is invoked.

## Added to a tool result, by the in-process module (`hooks/context.tsx` and its siblings)

The context warning, after a tool call, from 250,000 tokens and every 25,000 after, afresh after a compaction. Three tiers by the count, each `Context at <tokens> tokens (<percent>% of <window>).` followed by:

- From 250,000: "Aim for a safe point: finish the step under the cursor, commit if it is green, write CLAUDE.local.md, then tell the user it is safe to compact."
- From 500,000: "End this turn at the next green commit, even with the task unfinished: write CLAUDE.local.md, reach a clean tree, and tell the user whether it is safe to compact. Start nothing new before that."
- From 750,000: "Stop starting anything new. Commit or discard what is in the tree, write CLAUDE.local.md now, and end this turn saying you are ready to compact."

With the `chain` option on, "tell the user it is safe to compact" becomes "call the clear_point tool", and the firmest tier "call the clear_point tool now".

The test log, after a failed test run through Bash: "The test run failed; its whole output is in <tempdir>/claude-kit-last-test-<session id>.log."

The document cap, after an Edit or Write of a markdown file under `docs/` past 1,500 lines: "<path> is <n> lines, past the 1500-line cap: split it at the seam it shows."

The single-edit nudge, after a Bash call that is a Python heredoc doing one file edit: "This Bash call is a Python heredoc doing one file edit: a read, one replace, a write. The Edit tool makes the same change for about a third fewer tokens and shows it as a diff."

## Added beside a prompt, by the in-process module (`hooks/checkout.ts`)

On the first prompt of a context (a new conversation, or one just compacted or cleared), when the handoff is not current, one of:

- "session-kit: CLAUDE.local.md is missing: run /session-kit:handoff init before working, so the next context starts from the files."
- "session-kit: CLAUDE.local.md predates the last commit: read it knowing that, and run /session-kit:handoff at the next clear point."

## Added to a tool result, by the settings hooks (`hooks/hooks.json`)

The formatter, after an Edit, Write or Bash edit, when a formatter or linter left something: "<tool> left this in <path>:" and up to a few lines of the tool's output, or "<tool> on <path> did not run: <error>".

The tells hook, after the same: "Banned prose tells in what this edit wrote. Rewrite each sentence; swapping the mark is not enough:" then one line per tell, `<file>:<line>  <rule>  '<text>': <advice>`.

At session start, when the language-server config left a package out: "pyrightconfig.json (the language server's view of the packages): <detail>", with a system message "Navigation is partial: <detail>" for the person.

At session start and on a directory change, when direnv is not loaded, a system message for the person only: "The direnv environment is NOT loaded: Bash runs the machine's tools, not the project's pinned ones. <detail>. Fix: with direnv on the app's PATH, run direnv allow in <dir>, then /clear."

## Refusals, by the guard (`hooks/guard.py`)

A refused tool call returns its reason to the model as the denial. A rule reads the command with its quoted text and heredoc bodies blanked, unless one holds a substitution, and the two test-runner rules match a runner only where a command segment starts, behind a launcher or a path (`A47`, the guard reads the command as the shell runs it).

- `git commit --no-verify`: "git commit --no-verify skips the hooks. Fix the failure instead of bypassing it."
- `git push --force` or `-f`: "git push --force rewrites the remote. Use --force-with-lease if it is intended."
- `git rebase -i`: "git rebase -i needs an editor and cannot run here. Squash with git reset --soft and a new commit instead."
- `git reset --hard`: "git reset --hard destroys uncommitted work. Prefer git reset --soft."
- A test runner with `-x` or `--exitfirst`: "-x / --exitfirst hides every failure after the first. Let the suite finish and read the whole list."
- A call starting with shell `timeout`: "Do not wrap a Bash call in shell `timeout`: the tool has its own `timeout` parameter, in milliseconds where the shell's is seconds. Inside a script it is fine."
- A test runner piped to grep, head, tail, less or more: "Write test output to a file (`&> log`) and search the file. Piping it inline throws the rest away and forces a rerun."
- A bare `git stash` or `git stash pop`: "A bare git stash / stash pop works on a stack shared by every worktree, and another session may pop yours. Use a temporary WIP commit, or `git stash push -u -m \"<tag>\"` then `git stash apply <sha>`."
- `git commit --amend` on a published commit: refused with its reason in `guard.py`.
- The Artifact tool: "A deliverable is a file in the project, never a published page. Write it as markdown or a plain .html beside the work, or in the scratchpad, and answer with its path."

## Tools the model is given, with the `chain` option on (the default)

`clear_point`, with `next_step` ("session" or "owner") and `note`: "Call this at a clear point: the tree is committed and green, nothing is in flight, and the next step is known. When this turn ends, session-kit writes the handoff (CLAUDE.local.md), compacts the context, and continues with the next step, or stops when that step waits on the owner. Then end the turn with nothing more started." Its result: "Clear point noted. End this turn now, with nothing more started. When it ends, session-kit writes the handoff and compacts the context, then" either "stops, since the next step is the owner's." or "continues with: <note>". A third chain since the person's last prompt is refused (`A45`, a loop guard on the chain): "session-kit has run 2 chains since the person's last prompt and runs no more with nobody at the prompt. End this turn now, with nothing more started, and wait for the person: their next prompt lets the chain run again."

`new_task`, with `task`: "Call this when the prompt just given is a task unrelated to the task this context holds, before starting on it: one task per context. session-kit then offers the person the handoff and a clear, or to keep going here, and sends their prompt again after. Then end the turn, saying in one line that it is a new task, with nothing started. A context that holds no task yet (new, or just cleared) takes the prompt as its task, whatever CLAUDE.local.md describes." Its result: "New task noted. Start nothing on it. End this turn now, saying in one line that it is a new task: the band offers the handoff and a clear, or to keep going here, and the prompt is sent again after." In a context that holds no task yet: "This context holds no other task (it is new, or just cleared), so there is nothing to clear: start on the prompt. CLAUDE.local.md still describes the last task, and the next handoff rewrites it for this one."

## Prompts the module submits

After the chain's compaction, as the plugin's prompt: "Continue. Read again in full the documents CLAUDE.local.md lists, then take its next step: <note>".

After a `new_task` clear, or on "Keep going here": the person's own last prompt, sent again as their words. A prompt that is not their own words (a notification, a schedule, another session's, a plugin's, a slash command) is never sent in their place (`A46`, prompt origins as a closed set).

## Instructions given to a compaction

To the engine's own compaction, the one it starts at its threshold, appended to whatever instructions it had: "This compaction comes without a handoff, so the summary stands in for CLAUDE.local.md. Keep the task in the user's own words, every decision with who took it and why, where the work stands (done, in progress, not started), the last check that ran and its result, the open questions for the user, and the next step as one line. Name by path every document the work rests on, so the next turn reads each again in full."

To the chain's compaction: "CLAUDE.local.md holds the handoff written for this compaction: keep the task, the decisions, where the work stands, the last proof and the next step as it states them, and the paths of the documents it lists." followed by the same fields.

## What the person sees and the model does not

The band above the prompt past the threshold: "Context <tokens> tokens (<percent>% of <window>): find a clear point, commit, write the handoff, ask to compact.", ending "call clear_point." with the `chain` option on. The chain's stage line and the `new_task` offer with its two buttons. Each band has a Dismiss button (`A43`, the bands are dismissable), which the model never sees, and draws above the bands of the plugins beneath it (`A44`, the band composes with the bands beneath it). The toasts when a chain step did not run. At the end of a main-loop turn, one dim line from `hooks/checkout.ts` when the tree holds uncommitted changes or the handoff is missing or stale: "session-kit: <n> uncommitted changes at the end of the turn. CLAUDE.local.md predates the last commit (/session-kit:handoff)."
