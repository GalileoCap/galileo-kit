# The prefixes and check-ins proposal, read against the kit

Read on 2026-10-29 against session-kit 0.37.4 at `cd4cf2f` and Claude Code 2.1.308. The proposal is `proposal-prefixes-and-check-ins.md` beside this file, copied in unchanged. This file says where the proposal is harder than it looks, gives the two candidate objectives as they should go to the owner, and proposes the rulebook budget. Nothing is built.

Sources read: `hooks/context.tsx` (the chain, the new-task offer, the cold-cache timer), `bin/session-watched`, `types/index.d.ts`, `OWED.md`, `docs/PLAN.md` (open questions), the 2.1.308 binary for the names of the calls, and the reviewed clones (`effortless`, `cache-guard`, `image-peek`) for how `drop` and `$.prompt.fill` are used.

## The API calls

All four calls the proposal adds exist in 2.1.308 by name: `prompt.fill`, `prompt.read`, `model.fork` and `ui.selection` are strings in the binary. `{ drop }` from `prompt.submit` is used by `cache-guard`. `$.prompt.fill` leaves a draft in place unless called with `mode: 'replace'`, as `effortless` and `image-peek` call it. The engine's types are compiled into the binary, so the signatures beyond those uses are not verified. Part A's sending side is buildable on what exists.

## Where it is harder than it looks

### 1. The watcher rests on a mechanism no real session has shown

Part B's watcher is the cold-cache timer's design: a `$.clock.after` in module memory, its deadline in `$.state`, set again at `session.start`, and `$.prompt.submit` from the timer while nobody is at the prompt. `OWED.md` lists the cold-cache timer (`A49`) among what has run only in the engine's tests. So nobody yet knows whether a timer fires in an idle desktop session, in a session whose window is in the background, or after the Mac sleeps. Part B multiplies that bet: a tick every ten minutes, for hours. **Proving the cold-cache timer in a real desktop session comes before any of Part B.**

The timer lives in the session's process. The proposal treats the kit's watcher as the party that "knows the time, with a timer that survives reloads". That holds only while the session is open and the Mac is awake. If the Mac sleeps, `session-watched`, the run and the watcher stop together. If the app quits, the watcher stops. A run started with `nohup` survives, but nothing probes it until a session starts again. That is the night the owner most wants watched. The run card's "a notice reaches your desktop and phone if it ends or stalls" overstates this. It should say "while this session is open and the machine awake", or the watcher moves outside the session (see 8).

### 2. A wake collides with the chain

`stepChain` in `context.tsx` treats any main-agent turn that ends with reason `answer` as the end of the chain's current stage. A wake is a turn. It can land between the handoff command and `/compact`, which are separate turns joined by `$.clock.after(0)`. Then the wake's own end advances the chain: the compaction starts with the handoff unwritten, or the handoff turn's end goes unseen. When the chain waits on the owner, a wake's end clears it with the journal line "the person moved on", which is false.

The same holds for the new-task offer: a wake while the band offers the clear runs a turn on the old task, against `O11` (one task per context). Each wake also calls `turn.start`, which disarms the cold-cache timer, so a ten-minute tick never lets the cold chain fire. The proposal says a wake waits for a turn in progress. It must also wait while `chain` or `newTask` is set, queue its event, and fire on the next idle. The turn-end item check's auto-prompt and the detached-run gate's prompt need the same guard, since they too start a turn from `turn.complete`. Neither should fire on a turn whose chain stage is `requested`, the turn that called `clear_point`.

### 3. A wake on a cold cache is not "one model turn"

The cost section counts a wake as one turn. On a cache past its lifetime, that turn rewrites all of the prefix. At 300,000 tokens of context it costs more than a hundred ordinary turns' reads. Nine of every ten wakes in an overnight run land on a cold cache: a stall at 02:00, a passed ETA at 04:00. Two ways out:

- The cold-cache chain compacts first, as it does today when context is past the floor. The wake then lands on a small context.
- A wake past the cache's lifetime only notifies, and its model turn waits for the owner's next prompt. Only `ended` and "a pause point you asked for" wake the model at once.

The proposal's measure "tokens per wake" should be split by warm and cold.

### 4. The registry cannot live in `$.state`

The new-task clear starts the session's named values over (`clearThenResend`). Registered runs and open `Do` items kept in `$.state` would vanish with it. Losing the open items there is arguably right, since a new task starts clean. Losing a run's registry is not: the run keeps going, and nothing watches it. The registry goes to a file, `.claude/runs/<label>.json` beside the status file. It is read again at `session.start`, and that also lets a later session in the project adopt a run.

Two sessions in one project, or two worktrees, share `.claude/runs/`. So a label needs its session's id, and a run with no live session gets a band row in the next one that opens: "embed bench, registered by a closed session, ended 03:12".

### 5. `--pause-mark` and `--progress` read output that `session-watched` does not read today

Today it only measures the size of stdout when stdout is a regular file. Matching a line means reading the file's new bytes on each sample. Three consequences:

- A run whose output goes to a pipe or a terminal has no pause points and no progress.
- Python writes to a file in blocks, so `finished model 6/14` can show up minutes late, or not until the run ends. The run card has to set `PYTHONUNBUFFERED=1`, or the equivalent, for the job.
- Ending the run "right after the matching line" can cut the write that follows the print. Many jobs print "finished model 7" and then save. A stop at a pause point needs a short grace, or a second pattern that marks the save.

On a remote run, `session-watched` runs only on this machine: the probe sees the remote lines, and nothing on the remote host can stop at one. `stop_at_pause` holds only for local runs, and the tool should refuse it otherwise.

### 6. The detached-run gate's exemption cannot be computed

"A background Bash run expected to finish within 30 minutes" needs an expectation the kit does not have. Simpler and computable: every background Bash run is exempt, since the harness reports its exit. The gate covers only the detached patterns. A background run that hangs is already ended by `session-watched`'s five minutes if it is watched. An unwatched one is the existing run rule's concern. The pattern list belongs beside the guard's: `test_log.ts` already copies `guard.py`'s launcher pattern by hand, and a third copy should share it.

### 7. The organization's policy may skip the kit's `prompt.submit` in the work instance

`docs/PLAN.md`'s first open question records `cc-plugin-sec-default` sending `prompt.context` and `session.compact` on past the kit in the work instance (`C2`, the organization's security default sits outermost). If it does the same to `prompt.submit`, three things stop there without a word: the open-item store, the pre-send check and the secret hold. The turn-end check would then find no items and report nothing. The first real session in the work instance has to show that `prompt.submit` reaches the kit. Until then, the secret hold must not be described as "always on".

### 8. What the pre-send check costs per message

- It runs inside `prompt.submit`, so the owner waits for Haiku on every message of four or more bullets. Those are the long messages, this one among them. A few seconds each, every time, is friction. It also adds to the kit's time per hook that `A55` (a timeline of turns and tool calls with the kit's time per concern) measures.
- When `$.model.complete` fails or times out, the message has to go on unchanged, by `C1` (the kit is never the reason a session fails). It needs a hard limit, two seconds or so.
- On a surface that draws no band, a held message has no buttons to send it as is. The owner sees the drop reason and an empty box, or a refilled one, from the phone. With `$.session.surfaces` the check can run only where a band is drawn. The secret hold is the exception, since its refill is all of the answer.
- "Send as is" sends through `$.prompt.submit`, which runs the hook again. It needs a one-shot pass, or the message is held again.
- A pasted secret held before the model is right, but the app's own prompt history may still hold the text. The hold protects the transcript and the API. The machine's history keeps the text.

### 9. Tag parsing meets pasted text

The owner's messages often carry pasted documents: this one was a single pasted block. A pasted proposal or log full of `Do:` lines would open items the owner never sent. The parser has to see where pasted content starts and ends, which `prompt.submit`'s text may or may not mark. That has to be tried before the parser is written.

### 10. The closing block meets the desktop app's own closing rules

The desktop app tells the model that the next-step box holds one question, and that the message asks only what the box does not show. The proposal's `Asks you:` lists every question at the end of the message. The owner's rules win over the app's, but the session then gets two instructions that disagree. The rule should say plainly that `Asks you:` lists every question, the box's included. Separately, the status line was just shortened so the usage window fits (`5086699`). "2 open Do" belongs on the band and the `/kit` pane.

### 11. Matching by first words is the weak joint

Matching on "tag, order and first words" breaks when the model paraphrases, translates (the Spanish sessions) or merges two items.

Decided by the owner on 2026-10-29: the check matches by an id the kit assigns. The `prompt.submit` hook parses the tagged lines, gives each an id of the tag word, a hyphen and a number (`Do-1`, `Ask-1`, `Decide-1`, `Later-1`), and attaches the list as hidden context with the instruction to end the reply with one line per item, starting with its id. The closing lines start with the id (`Do-1 Done: rename to Verdict (commit 3f2a1c0)`), so the ids stay visible and the owner can refer back with them ("Do-3 isn't done") without ever writing one. The word-hyphen-number shape clashes with nothing: one letter and digits would read as an intent id (`A1` an action, `C1` a constraint) or as `M27`, `T8` and `Q4` in the analyses. The counter runs per tag across the session, so an item open across turns keeps its id, and a clear starts the counts over. The check reads an id only at the start of a closing line: an id in prose or in pasted text is ignored, and pasted content never opens items.

## What is easier than it looks

- Registering `check_in` follows `clear_point`'s pattern, and `turn.complete` already filters to the main agent (`e.agentId`).
- A wake prompt is a plugin-origin prompt, so `isThePersons` already keeps it from overwriting `lastPrompt` or resetting the chain's evidence.
- `--hold` is `--warn` plus two writes to the status file. A run the session waits on keeps the five-minute end with no change.
- The `services` key reads beside `test_commands`, which the kit already loads.

## The order this suggests

1. Prove the cold-cache timer in a real desktop session, idle and with the Mac asleep and woken. Prove that `prompt.submit` reaches the kit in the work instance.
2. `session-watched --status`, `--hold`, `--eta`, `--progress`, `--pause-mark`. They are useful alone, and the `Status?` answer reads them without any watcher.
3. The tag rule and the turn-end check, with the kit-assigned ids of 11, the wake guard from 2, and items kept in `$.state`.
4. `check_in`, its file registry and the watcher, with the warm and cold split from 3.
5. The detached-run gate.
6. The pre-send check, the secret hold first, since it needs no model.

## The candidate objectives

As the owner would approve them. Each is a change seen from outside and names no mechanism.

- Every line the owner sends has a visible outcome. For every line the owner sends, the owner can see what became of it. From `G2` (focus on the parts only I can do) and `G3` (consistent quality, reviewing what matters).
- A long run reports itself. The owner learns how a long run is going, and when it needs them, without asking. From `G2` (focus on the parts only I can do) and `G4` (optimize time and reduce costs).

The proposal places both under `G2` "next to the existing objective on clear communication". That objective is `O18` (communication with the owner is clear), which stands under `G1` and `G3`. The first candidate sits closer to `G3`, since what it saves is the owner rereading replies to find what was dropped. The second saves polling time, which is `G4`. Neither duplicates `O6` (a session's word is not the proof) or `O18`.

## The rulebook budget

The rules load at 3,163 of 7,500 words (`A81`, the default budget of 7,500 words), and `global/CLAUDE.md` holds 1,432 of them. The proposal's two drafts add about 95 words, plus about 90 that replace the current 35-word bullet. That is about 150 words net, to roughly 3,310, so the budget holds without removing any rule.

The proposal is to keep the budget at 7,500 and spend less than the drafts ask, about 70 words:

- The tag rule, about 45 words. It keeps what the model has to act on: the five meanings, one line per item, the `Read as` line, and the questions last. The closing block's exact line forms (`Done`, `Not done`, `In progress`, `Decided`, `Parked`) go into the text the kit attaches at `prompt.submit` when a message carries tags. The model reads them only on the turn that needs them, every turn in a project without the kit pays nothing, and the rule stays true where the kit is absent.
- The run rule, about 60 words, replacing the 35-word bullet. It keeps the split between waited-on and registered runs, "no clock ends a registered run", the four decisions and "a stop that could lose work is the owner's". The run card's five lines go into `check_in`'s tool description, which the model reads when it registers a run.

This follows the rule that holds the rulebook: what every turn loads should be what every turn needs. The format of a block is needed on the turns that write one.
