# The rules-and-load audit, read for the kit

Read on 2026-10-29 from the owner's audit, [`rules-and-load.md`](../../../claude-analysis/rules-and-load.md), its data in [`audit-data/`](../../../claude-analysis/audit-data/), and engine 2.1.308's API. The audit's decisions are the owner's and are not reopened here. This reads the kit's side: what the engine makes harder than it looks, the objectives the work would rest on, and an order. The T-Agents items and the lane and merge procedure are not the kit's.

## 1. What the engine allows, checked

### The kit sees the question in the next-step box

Yes. `tool.call` raises for every tool, MCP and the desktop app's own included: the kit's measure log holds 698 calls of `mcp__ccd_turn__wrap_up` and 65 of `AskUserQuestion`. A hook on `wrap_up` reads its arguments, so the kit has the question (`ask`), its buttons (`actions`, each a `label` and a `message`) and `blocked`.

Three limits:

- `AskUserQuestion` is answered inside the turn that asked it, so at the turn's end it is never pending. Only `wrap_up` with an `ask` is.
- A question written in the reply's prose (lane4 on 2026-10-29, five questions in an earlier turn's text) is not seen. Reading the reply for question marks would misfire, so this case stays out of the fix.
- A button of `wrap_up` that names an app action (`commit`, `create_pr`, `merge`) is the app's to run. The band cannot run it, and draws it as text.

### A band button sends its message as the person's prompt

Yes, by `$.prompt.submit({ text, asUser: true })`, which the pre-send check's Send as is already uses. The model reads the text bare, as if typed. The transcript names the plugin, and every hook sees the origin `plugin`. That last part costs something: the kit's own hooks treat a `plugin` origin as not the person's (`NOT_THE_PERSONS` in `context.tsx`), so a prompt the kit sends for the person gets no tagged-line ids, and is not kept as the last prompt. The question's buttons and the hold below both need these hooks to take a prompt the kit sent for the person as the person's.

The phone draws no band, only toasts, so a question carried across a compaction cannot be pressed there.

### A prompt held for a reason, then sent unchanged with no trace

This is harder than it looks. The kit has two ways to hold a prompt, and neither is clean yet.

1. Drop it, then send it again (what the pre-send check does). `prompt.submit` answers `{ drop }`, the prompt never enters the conversation, and after the reason the kit sends the text `asUser`. The model reads nothing of the hold. But the second sending is not the same prompt:
   - Pasted images and `@file` mentions are not expanded on a plugin's prompt. The owner iterates from screenshots, so a held screenshot would be lost.
   - A prompt typed while a turn runs joins that turn. Sent again, it waits for the turn to end and starts one of its own.
   - The origin becomes `plugin`, with the cost above.
2. Wait inside the hook. The hook does not call `next(e)` until the reason comes, and then passes the prompt on as it arrived: images, mentions, origin and timing all kept. The types say nothing of a time limit on a `prompt.submit` hook, nor of what the prompt box does while one waits. This would be the right way if it holds. It needs a probe first: a dev mod that waits 60 seconds in `prompt.submit`, driven on the terminal and the desktop.

The probe ran on the desktop on 2026-10-29, a dev mod holding a prompt in `prompt.submit`. The owner left the terminal out.

- A hook's budget is 10 seconds of its own time, and the clock stops while a `$` call other than a `$.clock` wait is in flight. No `$` call waits on the person.
- Held by a 60-second `$.process.run`: the prompt entered when it ended, unchanged, the pasted screenshot attached and the origin `composer`.
- A prompt typed during the hold queued behind it, and could not overtake it.
- An interrupt during the hold dropped the held prompt: it never entered, and the owner sent it again.
- Held by a 15-second `$.clock.sleep`: the engine passed the prompt on at 10 seconds, and the hook's own `next` after its wait never landed.

So the hold is the second way, with a process as its wait: a process that ends when the band writes the reason to a file the kit names. An interrupt during the hold has to put the held text back in the prompt box (`C3`, a hook that writes to the owner's input loses none of it).

The reason is typed into an `Input` on the band. The terminal, desktop and VS Code draw `Input`. The phone draws neither a band nor an `Input`, and the phone is the likeliest off-window channel (`volume.md`: 54% of off-window sittings are three messages or fewer). On the phone a prompt can be passed and logged as "phone, no reason", or refused with a toast that sends the owner to the desktop. The second is the friction the audit asks for, but it blocks an answer the owner may need to give. This is the owner's call.

Nothing of the hold reaches the model under either way: a drop's reason is shown to the person alone, and the band, the status line, toasts and the pane are the person's. The probe also checks that a drop leaves no row in the transcript the model reads.

### The 30-minute pass

Easy, with one choice. The pass is a time in a file under `~/.claude/session-kit/`, so every session reads it, and `$.clock` counts it down on the band. The choice: a pass for the sitting (every session, which this read recommends, since a reason per session would mean six reasons at a sitting) or for that session alone.

### Other parts of 2a

- Across sessions. The window's close ("how many are working or waiting on you"), the concurrent-session friction and the morning list need each session's state where every session can read it: a file per session under `~/.claude/session-kit/sessions/`, written at each turn's start and end, with a heartbeat so a closed session drops out. The kit has no such registry today. It is the shared ground of three items.
- The morning list at 06:00 needs a session to be running at 06:00. With the app closed, nothing runs. Building the list when the first pane opens after 06:00 needs no timer and shows the same list.
- Where 2a's settings live. The window, the focus list, the project kinds (work, personal) and the 2b bar go under `~/.claude/session-kit/`, outside every project, since sessions read a project's `.claude/claude-kit.json`. The kit's own code is read by the session working on the kit, which cannot be helped and is that session's alone.
- Order on `prompt.submit`. The hold goes outermost, before the pre-send check, so a prompt held off-window is not first held by Haiku.

## 2. The rule fixes, read

- The pending question. Under `O12` (lose nothing at a context boundary): an action, no new objective. Its rule, "nothing of the kit's starts a turn or a compaction while a question waits", is a constraint every later piece keeps, as `C3` is, so it is put to the owner as `C4` below.
- R18 (an id carries its name), names by a program.
  - A hook that rewrites the file the model just wrote leaves the model's picture of the file stale, and its next `Edit` may miss. The hook's note has to tell the model what it added, so the next edit matches.
  - Ids are the project's own: `O18` in T-Agents is not the kit's `O18`. The hook reads the project's `docs/intent/`, and does nothing where there is none.
  - The kit cannot install a commit-msg hook without writing into each repository's `.git/hooks`. A `tool.call` hook on `git commit -m` can add the names to a plain `-m` subject. For a message from a file or a heredoc, it can refuse with the corrected subject, which the audit found followed 81 to 91% of the time.
- R31 (test output to a file).
  - The guard has matched a runner only at a command's start since `88914bd` (2026-10-25), with the case "a grep that names a runner, piped" allowed. Most of the 87% may predate that. Measure again from 2026-10-25 before changing more.
  - The `2>&1` hole the T-Agents dev session found is fixed in 0.42.5, with `rg` and `|&` added.
- R24 (never deliver red), "tested".
  - `test_log.ts` keeps one record, the last run with a fingerprint of the tree. It does not know which files a run covered, nor which files changed since.
  - A first version: keep each file's hash at each run, and name the source files changed since the last run. That covers "changed after the last run", but not "covered by it".
  - "Covered" needs a map from a source file to its tests, which only a project can give, by a convention or its coverage data. The trial project is the one to say which.
- R20 (compact at a clear point), one threshold. Mechanical. The rule's prose loses its number and points to the kit's context warning, which lowers the rulebook's word count.
- The person-only lines, the "tested" line and the background tasks. A line at a turn's end reaches the model only beside the next prompt. These are one line, in one place: the checkout facts `checkout.ts` already adds beside the person's prompt. That place cannot hide a pending question.
- The tells listed once per session. Easy. The list for a long file is capped, with a count of the rest.
- Format and pyright quiet on success.
  - The pyright notice is the kit's, and is cut easily.
  - "PostToolUse hook modified" is the engine's own note after the format hook rewrites the file. The kit can't make the engine quiet. It can only avoid the rewrite: format a `Write`'s content before it lands, in a `tool.call` hook. An `Edit` is a fragment and cannot be formatted alone, so `Edit` keeps the note.
  - Read the 20.7 M tokens by tool before choosing. If most come from `Edit`, the gain is small.
- The single-edit nudge. Cut.
- Background tasks with no check-in. The kit sees a `run_in_background` call and its id. A task's end comes back as a notification prompt, and a stop as `TaskStop`. The line lists the ids still open at the turn's end.
- `session-transcripts rules` and a rule's trial.
  - The port copies `rule_costs.py` and `owner_signals.py` into the kit's `session-transcripts`, with tests. Neither `owner-messages*.jsonl` nor any output that quotes the owner's messages enters the kit.
  - The trial rule is a line in `global/goals-objectives-actions.md`'s section on adding a rule, for the owner to approve.

## 3. Candidate objectives

Each is an outcome, names no mechanism, and waits on the owner's approval. Most of the rule fixes fit approved objectives and need no new one: R18 under `O18` (an id is never written without its name), R24 under `O6` (done rests on a record a program wrote), R20 under `O12`, the quiet hooks and the tells under `O15` (routine work takes the cheaper path), the person-only lines under `O5` (every step moves to a program where one can do it), the audit's port under `O17` (the system observed and improved from the transcripts).

- `C4` Nothing of the kit's starts a turn or a compaction while a question of the session's waits on the owner. Where one must, the question goes across whole, with its buttons. From `O12`, `O19`. The rule the owner gave for the defect and for every piece after it.
- `O20` A rule spreads beyond one project only once its trial shows it works. From `G1`, `G3`. Rests on the audit's finding that the newest layers draw complaints within days (`rule-costs.md`, `owner-signals.md`).
- `O21` Nothing a session starts is left running unseen. From `G4`, `G5`. The three corrections and "RAM is tight" (`owner-signals.md`).
- `O22` My work keeps to my working window, and each exception is a choice I make with a reason. From `G4`. Rests on `volume.md`.
- `O23` My week's attention goes to the must-haves I name for it. From `G2`. Rests on `volume.md`'s week by folder.
- `O24` I run no more sessions at once than I can review. From `G2`, `G4`. Rests on `volume.md` and the audit's "parallel sessions multiply interruptions".
- `C5` Nothing of the load measures reaches a session. From `O22`, `O23`, `O24`. The audit's "the sessions don't find out", as a constraint every piece of 2a keeps.

`O22` to `O24` are about the owner's own hours, which `G4` (optimize time and reduce costs) holds only if "time" includes the owner's own. If they rest on a goal of the owner's that is not written yet, such as a sustainable working day, that goal is the owner's to state, and these move under it.

The owner approved all seven on 2026-10-29, `O22` to `O24` under a new goal, `G6` (controlled working hours). On the phone, an off-window prompt is passed and logged. The 30-minute pass holds for the sitting, across every session.

The 2b bar is an action under `O22`, written into the kit's settings when 2a goes live, and never an objective.

## 4. An order

The owner's order is the defect, then focus and the off-window friction, then the rule fixes. This read agrees with the first two and changes the inside of the second:

1. The defect (`C4`), now, its regression test shown. Then the session registry, which 2a needs.
2. The hold probe, run on 2026-10-29 (section 1): a hook waiting on a process keeps the prompt as it was.
3. 2a's measured core, built on 2026-10-29 as `A92` and `A93`, before Friday's review can run: the window and the project kinds in `~/.claude/session-kit/`, the hold with its reason and the log, the 30-minute pass, and `session-transcripts week` with the 2b bar. The four-week clock starts when the hold goes live, and the first Friday review reads every day of the log since.
4. The rest of 2a: the focus list and its tags, the countdown and the close, the concurrent-session friction, the streak, the morning list. They share the registry from step 1.
5. The rule fixes, cheapest first: R20's one number, the nudge cut, the pyright notice, the tells once per session. Then the turn-end line (the person-only lines, background tasks, R24's first version, trialled in one project). Then R18's programs. Then the audit's port and the trial rule.

The cheap rule fixes can go between the 2a steps, since each is an hour or less and touches nothing 2a does.
