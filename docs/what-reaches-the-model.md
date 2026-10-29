# What reaches the model

Every text the kit puts in front of a session, verbatim or by its source, for the owner's review. Written 2026-10-25 at session-kit 0.11.0. The numbers are the defaults. When a text changes, this file is rewritten from the sources it names.

## Always loaded

- `global/CLAUDE.md`, linked at `~/.claude/CLAUDE.md`: the rules, 56 lines and 1,432 words, in every session on this machine, each cut to its obligation (`A77`, a global rule states its obligation). `global/RATIONALE.md` and `global/goals-objectives-actions.md` are read on demand, when the rules point at them.
- The project's `CLAUDE.md` and `CLAUDE.local.md`, loaded by the engine beside the global rules. After the model's text, `CLAUDE.local.md` holds a section the kit wrote (`A63`, facts from git and the session beside the model's prose in the handoff), between the markers `<!-- session-kit facts -->` and `<!-- end of session-kit facts -->`, under the heading "Facts from git and the session": "Written by session-kit from git and its own records at <hh:mm> on <date>, when the turn that wrote this file ended. The model did not write this section, and the next write of the file replaces it." Then one line each for the branch against its upstream, the uncommitted paths, the last test run's verdict on this tree, the person's last prompt quoted verbatim up to 600 characters, the commits since it (six at most, newest first), and the commit ids the model's text names that the repository does not hold.
- The `handoff` skill's description, in the skill list: "Write the project's live state to CLAUDE.local.md (uncommitted) so a compaction or a lost session loses nothing. `init` creates it from the template." Its body, `plugins/session-kit/skills/handoff/SKILL.md`, loads when it is invoked.

## Added to a tool result, by the in-process module (`hooks/context.tsx` and its siblings)

The context warning, after a tool call, from 250,000 tokens and every 25,000 after, afresh after a compaction. The count is the engine's figure with the tool output landed since its last measurement on top, at 3.5 characters a token (`A62`, the context figure projected between the engine's measurements). Three tiers by the count, each `Context at <tokens> tokens (<percent>% of <window>).` followed by:

- From 250,000: "Aim for a safe point: finish the step under the cursor, commit if it is green, write CLAUDE.local.md, then tell the user it is safe to compact."
- From 300,000 (1.2 times the trigger), and at once when the count first reaches it inside a step: "End this turn at the next green commit, even with the task unfinished: write CLAUDE.local.md, reach a clean tree, and tell the user whether it is safe to compact. Start nothing new before that."
- From 400,000 (1.6 times the trigger), likewise at once: "Stop starting anything new. Commit or discard what is in the tree, write CLAUDE.local.md now, and end this turn saying you are ready to compact."

With the `chain` option on, "tell the user it is safe to compact" becomes "call the clear_point tool", and the firmest tier "call the clear_point tool now".

The test log, after a failed test run through Bash: "The test run failed; its whole output is in <tempdir>/claude-kit-last-test-<session id>.log."

At a `git commit`, when the last test run failed: "The last test run (<command>, at <hh:mm>) failed, and none has passed since. Run the tests again before this is delivered as green, or deliver it red with the evidence." When it passed and files have changed since: "The last test run (<command>, at <hh:mm>) passed on a different tree, and files have changed since it ran. Run the tests again before this is delivered as green, or say they did not run on this tree." (`A52`, a check result stamped with the tree it ran on.) A run that passed on this tree, or none recorded, adds nothing.

After the second failed try at a fix, the same test command failing with the same error after an edit, beside the log's line: "session-kit: <command> has failed with the same error after two edits. A fix that has not worked after two tries stops and shows evidence: state what was tried and what happened, and let the owner or the next reader decide." (`A53`, the two-tries rule as a program.)

The document cap, after an Edit or Write of a markdown file under `docs/` past 1,500 lines: "<path> is <n> lines, past the 1500-line cap: split it at the seam it shows."

The single-edit nudge, after a Bash call that is a Python heredoc doing one file edit: "This Bash call is a Python heredoc doing one file edit: a read, one replace, a write. The Edit tool makes the same change for about a third fewer tokens and shows it as a diff."

## Added beside a prompt, by the in-process module (`hooks/checkout.ts`)

On the first prompt of a context (a new conversation, or one just compacted or cleared), when the handoff is not current, one of:

- "session-kit: CLAUDE.local.md is missing: run /session-kit:handoff init before working, so the next context starts from the files."
- "session-kit: CLAUDE.local.md predates the last commit: read it knowing that, and run /session-kit:handoff at the next clear point."

## Added beside a tagged prompt, by the in-process module (`hooks/tags.ts`)

On a prompt of the person's with a line that starts with `Do:`, `Decide:`, `Ask:` or `Later:` (`A83`, tagged items get ids from the kit and a turn-end check), outside fenced blocks and pasted content: "session-kit: the owner's tagged items, by id: Do-1 "<first words>" · Ask-1 "<first words>". End the reply with one line per item, starting with its id: "Do-1 Done: …", "Do-1 Not done: <why>", "Do-1 In progress: <what remains>", "Decide-1 Decided: <where it is recorded>", "Later-1 Parked: <where>", "Ask-1 Answered: <first words>". Then "Read as Do: …" or "Read as FYI: …" for each untagged line you acted on, and last, under "Asks you:", each question the owner must answer, one per line." The list carries every item still open in the session, the new ones after. The message itself reaches the model with each item's tag written as its id (`Do-1: …`, `A84`, the ids stand in the owner's message).

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

`clear_point`, with `next_step` ("session" or "owner") and `note`: "Call this at a clear point: the tree is committed and green, nothing is in flight, and the next step is known. When this turn ends, session-kit writes the handoff (CLAUDE.local.md), compacts the context, and continues with the next step, or stops when that step waits on the owner. Then end the turn with nothing more started." Its result: "Clear point noted. End this turn now, with nothing more started. When it ends, session-kit writes the handoff and compacts the context, then" either "stops, since the next step is the owner's." or "continues with: <note>". At the third signal since the person's last prompt, the fifth, and every one from the seventh, a judge reads the chain (`A54`, a Haiku judge reads the unattended chain for a loop or a step beyond its task). When it finds a loop, a step beyond the task, or gives no verdict, the result is "Clear point noted. session-kit's judge stops the chain after the compaction: <why> End this turn now, with nothing more started, saying in one line what is left for the owner. When it ends, session-kit writes the handoff and compacts the context, then stops." The why is one of "the session is going round: <reason>.", "the next step goes beyond the owner's task: <reason>." or "the judge gave no verdict (<why>), and an unjudged chain waits for the owner."

The cold-cache timer (`A49`, the cold-cache timer runs the chain before the cache goes cold) runs the same handoff command and compaction with no tool call and no prompt of its own, when a turn's end past the floor is left alone for the cache's lifetime less the lead, and stops there.

`new_task`, with `task`, and `effort` with `effort_reason` when the new task needs another effort: "Call this when the prompt just given is a task unrelated to the task this context holds, before starting on it: one task per context. session-kit then offers the person the handoff and a clear, or to keep going here, and sends their prompt again after. Then end the turn, saying in one line that it is a new task, with nothing started. A context that holds no task yet (new, or just cleared) takes the prompt as its task, whatever CLAUDE.local.md describes. When the new task needs another effort than this session runs at, name it with its reason: the person may take it with the clear, and never in this context." The `effort` field: "The effort the new task needs, only when it differs from this session's: lower for routine or mechanical work, higher for design or debugging." An effort that is not a level is refused: "effort must be one of low, medium, high, xhigh, max, or left out." A proposal is kept only when it differs from the effort of the session's last request, and is set by `/effort <level>` after the clear, before the prompt is sent again, only when the person presses "Handoff, clear, effort <level>" (`A65`, an effort for the new task carried by the offer). Its result: "New task noted. Start nothing on it. End this turn now, saying in one line that it is a new task: the band offers the handoff and a clear, or to keep going here, and the prompt is sent again after." In a context that holds no task yet: "This context holds no other task (it is new, or just cleared), so there is nothing to clear: start on the prompt. CLAUDE.local.md still describes the last task, and the next handoff rewrites it for this one."

## Prompts the module submits

After the chain's compaction, as the plugin's prompt: "Continue. Read again in full the documents CLAUDE.local.md lists, then take its next step: <note>".

At the end of a turn whose reply left a tagged item without a closing line, once per item, as the plugin's prompt: "session-kit: your reply leaves these tagged items without a closing line: Do-1 "<first words>". Report each on a line that starts with its id, or say why not." Never while the chain or a new-task offer is under way.

After a `new_task` clear, or on "Keep going here": the person's own last prompt, sent again as their words. A prompt that is not their own words (a notification, a schedule, another session's, a plugin's, a slash command) is never sent in their place (`A46`, prompt origins as a closed set).

## Sent to a judge model

The chain's judge (`A54`), Haiku through `$.model.complete`, with the system prompt "You judge whether an autonomous coding session should go on by itself while its owner is away. Answer with one line: CONTINUE, LOOP or BEYOND, then a colon and one sentence saying why." Its prompt gives the owner's task from the Task section of `CLAUDE.local.md`, their last prompt, the chains since with their next steps and commits, the commits since the first, and the step proposed, then: "Answer LOOP when the session is going round: the same step again, steps that undo each other, or a fix tried again that keeps failing, with nothing committed between. Answer BEYOND when the proposed step goes further than the owner's task asked: work the task does not name, or a decision that is the owner's (publishing, pushing, installing, choosing between options the owner has not chosen, approving its own work). Otherwise answer CONTINUE."

The pre-send check (`A85`, a pre-send check by Haiku, held on the band), Haiku through `$.model.complete`, on a message of the person's that starts with `??` or holds four bullets or more, with the system prompt "You check a message the owner is about to send to a coding agent, against the owner's own rules. Answer with JSON alone: {"findings": […], "rewrite": "…"}. …". Its prompt gives the six rules of `hooks/presend.ts` (tags, a contradicted tag, an id without its name, a short go-ahead after several questions, a long run with no estimate or stop, a reversal with no reason), the last reply's `Asks you:` block or last paragraph, the output of `session-intent names`, and the message between `<<<` and `>>>`. Its answer reaches the person alone, on the band.

## Instructions given to a compaction

To the chain's compaction: "CLAUDE.local.md holds the handoff written for this compaction: keep the task, the decisions, where the work stands, the last proof and the next step as it states them, and the paths of the documents it lists." followed by the handoff's fields: "Keep the task in the user's own words, every decision with who took it and why, where the work stands (done, in progress, not started), the last check that ran and its result, the open questions for the user, and the next step as one line. Name by path every document the work rests on, so the next turn reads each again in full." The engine's own compaction, the one it starts at its threshold, gets nothing from the kit (`C2`).

## What the person sees and the model does not

The band above the prompt keeps a row for what needs the person, each a bold label, figures and buttons (`A71`, the band draws by urgency and keeps only what needs a decision). Past the threshold the context row reads "Context <tokens>k / <window> <percent>%" with "+<n>k last turn" when the last turn grew the context, and the buttons "Handoff" and, with the `chain` option on, "Handoff and compact" (`A72`, the band's buttons act and a press is the person's signal), absent while a turn runs. A usage window at 95% or more: "The 5-hour usage window is at <percent>% and resets at <hh:mm>.", the 7-day window and any other resetting "on <day> <month> at <hh:mm>", the spend limit named "The spend limit". The chain's stage line, which after a chain the judge stopped ends "The chain stopped since <why>", and the `new_task` offer with its buttons, its line ending ". Proposed effort <level>: <reason>" and a third button when the model proposed another effort. While the cold-cache timer is set, the context row (with the `chain` option on) ends "runs itself at <hh:mm>", and its Dismiss stops the timer too. With no context row, or the option off, a "Cache" row shows: "handoff and compact at <hh:mm>, before it goes cold" with "Run chain now". Once the chain has run, the chain's "Compacted. The next step is yours: go on from the handoff, written before the cache went cold." A failed handoff, compaction, clear or effort stays as a "Failed" row with the sentence, "Try again" for a chain's, and Dismiss (`A74`, failures stay on the band and an unattended end is notified). Each row has a Dismiss button (`A43`, the bands are dismissable), which the model never sees, and draws above the bands of the plugins beneath it (`A44`, the band composes with the bands beneath it).

A status line under the prompt on every surface: "ctx <percent>% <tokens>k +<n>k · you <span>", the span since the person's last message as "<1m", "12m" or "2h05m",, one segment per usage window ("5h 62%", "7d 20%", and " resets <when>" from 80%) and "compacts at <hh:mm>" while the cold timer is set. The line that closes a turn gets " · ctx <percent>%". `/kit` opens a pane with the context and a bar, the windows, the cache timer, the chain and its last eight stage lines, the handoff's state, the uncommitted files and the last test run (`A73`, the kit's numbers always on a status line, a turn line and a pane). A notification when a chain ends with the next step the owner's and when a chain fails. The toasts when a chain step did not run, only where no band is drawn.

Where a surface draws no band (the phone, VS Code), the same moments go out as a toast (`A51`, the moments the band shows go out as a toast where no band is drawn). The band's context sentence ("Context <tokens> tokens (<percent>% of <window>): find a clear point, commit, write the handoff, ask to compact.", ending "call clear_point." with the `chain` option on) goes as the toast each time the model is warned, and a usage window's line when it reaches 80% and 95%. The others are "New task: <task>. From a terminal or the desktop, the band offers the handoff and a clear, or to keep going here.", then "Clear point: the handoff, the compaction and the continue run when this turn ends.", then "Compacted. The next step is yours: <note>", and "session-kit: the cache goes cold in <n> minutes with nobody at the prompt: writing the handoff." At the end of a main-loop turn, one dim line from `hooks/checkout.ts` when the tree holds uncommitted changes or the handoff is missing or stale: "session-kit: <n> uncommitted changes at the end of the turn. CLAUDE.local.md predates the last commit (/session-kit:handoff)." One more from `hooks/test_log.ts`, when the last test run failed or passed on a tree that has changed since (`A52`), a stale run once until the tree comes back to it (`A66`): "session-kit: the last test run (<command>, <hh:mm>) failed, and none has passed since." or "session-kit: the last test run (<command>, <hh:mm>) passed on a different tree: files have changed since it ran."

