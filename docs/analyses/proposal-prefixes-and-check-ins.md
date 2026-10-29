# Proposal: message prefixes and automatic check-ins for session-kit

This proposal is for the session-kit session to take on. It covers:

- Part A: a prefix convention in both directions, checked at the end of each turn.
- Part B: check-ins on long runs that need neither you nor the model to remember them.

The design builds on what session-kit 0.37.3 already has:

- the `tool.call`, `prompt.submit` and `turn.complete` events
- timers (`$.clock.after`), with deadlines stored so they survive a reload, as the cold-cache timer does
- prompt injection (`$.prompt.submit`), as the chain's "Continue" does
- reading the transcript (`$.session.messages`)
- registered tools (`$.tool.register`), as `clear_point` and `new_task` are
- `session-watched` with `--stall`, `--check` and `--beat`

You decided four things already:

- the work lands as this proposal plus a message for the kit session
- prefixes run both ways
- the convention gets a rule and a check at the end of each turn
- check-ins use watched runs with a scheduled wake

The remaining open questions are at the end.

---

## Why

The counts come from the 152 live sessions, so they are lower bounds.

- Lost and misread lines:
  - 5 messages of the kind "Ask me that question again", "some messages got lost" and "Put the open questions to me".
  - One message spent clarifying that a remark was only a note: "messages like these are just notes… not meant for you to prioritize them."
  - Many mixed messages where a decision, a question and a new task share one bulleted list.
- Polling:
  - 42 "Status?", "What's next?" and "Where are we?" messages.
  - One idle-machine incident that led to "check-in on the job every 30 minutes", followed by "I haven't seen you check-in on it, even if it's been 1h". The model cannot keep that promise, because it has no clock between turns.

---

## Part A: the prefix convention

### The tags you write

| Tag | Meaning for the session |
|---|---|
| `Do:` | An order. It stays open until it is reported done or not done. |
| `Decide:` | A binding answer to an open question. It gets recorded, and is not reopened. |
| `Ask:` | A question. It is answered and changes nothing: no edits, no runs that write. |
| `Later:` | Deferred work. It is written to the plan, with no action now. |
| `FYI:` | Context. No action, no reprioritising. It is acknowledged only if it changes something already planned. |

Parsing rules:

- A tag starts a line, with or without a leading bullet.
- Indented lines and nested bullets under a tag belong to it.
- The tags are English in every session, Spanish ones included.
- Untagged lines are read as they are today. Tags are optional, so nothing breaks while the habit forms. In a tagged message, the closing block shows how each untagged line was read.
- The tag decides the action. `Ask: should we drop RISC-V?` gets an answer and no edits, even if the answer is "yes, drop it".

`Ask:` covers what you now say in long form: "Don't touch any code, simply answer", "This is a side chat, do not take any actions."

### The closing block the session writes

When your message had tags, the reply ends with one line per tagged item, in your order, quoting the item's first words. Those words are the item's only name, so no new numbering appears.

```
Done: rename to Verdict (commit 3f2a1c0)
Not done: the two-tall card; the grid has no row span yet, needs A156 (stats grid) first
Decided: Q4 (refuse to delete) recorded in A61 (delete guard)
Parked: autonomy levels, written to docs/PLAN.md under "Later"
Asks you:
  Should the Value card show planned value per scenario or per agent?
```

- `FYI` items get no line.
- `Ask` items are answered in the body. The closing line `Answered: <first words>` appears only when the message held two or more of them, so none slips.
- `Asks you:` lists every question the session needs answered, one per line, each named. It comes last so it sits at the bottom of the reply, where it can't be hidden under the next-step box.
- A `Do` that spans several turns is reported `In progress: <first words>, <what remains>` and stays open.

### The turn-end check

- `prompt.submit`: parse the tagged lines and store each `Do`, `Decide`, `Ask` and `Later` as an open item, keeping its first words.
- `turn.complete`: (main agent only, on a turn that ended normally outside a chain step): read the last assistant message and match the closing block against the open items, by tag, order and first words.
  - Matched `Done`, `Not done`, `Decided`, `Parked` and `Answered` lines close their items.
  - `In progress` keeps an item open.
  - Any item with no line gets a band row: "Unanswered: Do 'rename to Verdict'". On top of that, one automatic prompt per item: "Your reply leaves these without a line: Do 'rename to Verdict'. Report each, or say why not."
- Open items carry across turns: The status line shows their count ("2 open Do"), so you can see what is still owed without scrolling back.

### Costs and risks

- Tokens: The block costs about 15 tokens per item, and only on tagged turns.
- False positives: A paraphrased echo can miss the first-words match. Measure the auto-prompt rate on items the reply did address. If it is above about 1 in 20, drop the auto-prompt and keep the band row.
- Interaction with the chain: The check never fires during a chain step or a `new_task` offer, and never twice for one item.

### Draft rule for `global/CLAUDE.md` (about 95 words)

```
- **A tagged line is handled as its tag says.** `Do:` is an order, open until reported;
  `Decide:` a binding answer, recorded; `Ask:` a question that changes nothing; `Later:`
  deferred work written to the plan; `FYI:` context with no action. A reply to tagged lines
  ends with one line per item in their order, quoting its first words: `Done`, `Not done`
  with the reason, `In progress`, `Decided` with where, `Parked` with where. An untagged
  line in a tagged message gets `Read as <tag>:` with what was done. The questions
  the owner must answer come last, one per line, each named.
```

The reason, for `RATIONALE.md`: a mixed message loses items, and a remark read as an order costs a revert. Tags let the owner route each line and check every order at a glance, and they make "answer only" one word long.

### What a mod can do with your message

These facts come from the mod API types of Claude Code 2.1.308, read for this proposal.

- `prompt.submit` runs before your message reaches the model, and a hook can do three things with it:
  - rewrite it: `next({ ...e, text })`
  - attach hidden context to it: `context`
  - hold it back: return `{ drop: "<reason>" }`, and the reason is shown to you
- `$.prompt.fill({ text })` puts text back into your prompt box, and `$.prompt.read()` reads the draft as it stands.
- `$.model.complete({ model: "haiku", prompt })` runs one completion through your own session's client, with no tools and no history. `$.model.classify(text, labels)` picks a label.
- `$.model.fork({ prompt })` asks one question over the session's own transcript. The prefix comes from the cache, every tool is denied, and the answer never enters the main session's context.
- An `AssistantMessage` render hook can draw its own tree around each block of a reply, on every surface, so a button under a reply is possible.
- `$.ui.selection()` returns text you selected with the mouse, on the surfaces that report a selection. Whether the desktop app does has to be tried.

### The pre-send check (Haiku, opt-in)

You turn it on per message by starting with `??`, or with a band toggle for a stretch of work. It also runs on its own for a message with four or more bullets, since that's where most items got lost (96 such messages in the live sessions).

1. The `prompt.submit` hook strips the trigger and calls Haiku with:
   - your draft
   - the tag rule and the ID rule
   - the `Asks you:` block of the last reply, read with `$.session.messages()`
   - the project's ID names from `session-intent names`

   Never the transcript. That's about 2,000 to 3,000 tokens in, answered in a few seconds.
2. If Haiku finds nothing, the message goes on unchanged.
3. Otherwise the hook holds it (`drop: "Held by the pre-send check"`) and puts your draft back in the box (`$.prompt.fill`). The band then shows at most three findings, each one line, with three buttons:
   - Send as is
   - Use the rewrite, which fills the box with Haiku's version for you to edit
   - Dismiss

   Nothing is rewritten without your click.

What it checks, all from your own rules:

- an untagged message that mixes a decision, a question and an order
- an ID with no name, such as "Do M27 before installing"
- "Yes to both" or "Proceed" after a reply that asked three questions, naming the ones left unanswered
- a long run asked for with no ETA, cadence or stop condition
- an `Ask:` line phrased as an order, or a `Do:` line phrased as a question
- a missing reason on a reversal ("Remove it", "Take them back")

One check needs no model and is always on: a pasted secret (a key, a token, a private-key block). The hook holds the message and puts it back with the value replaced by `<secret: use the keychain script>`.

The risk is friction. Measure the share of findings you accept. Below about 3 in 10, it costs more than it saves, and the automatic trigger goes.

### A clarify action on replies (parked)

Parked on 2026-10-29. You keep using side chats for now, and this design stays here for later.

Your side chats today are full forks of the session. All 14 that I checked ran on Opus 5.5, the parent's model, and each one becomes another session in the sidebar.

A clarify action can be lighter, in two tiers:

1. Quick clarify (Haiku). You select a passage, or press **Clarify** under a reply's last block, and optionally type a question. Haiku gets the passage, the reply and the project's ID names. The answer shows in a pane beside the chat. It is cheap and never enters the main session's context. It suits "what is A125?" and "explain this in plain words".
2. With full context (fork). A second button, **Ask with context**, sends the same question through `$.model.fork`. That uses the main model over the cached transcript, with tools denied, and the answer still stays out of the main context. It suits "why did you choose X over Y here?".

What stays in side chats: questions that need tools, like reading files, running a probe or looking at a teammate's html.

What has to be tried before building: whether the desktop app reports a selection to `$.ui.selection()`, and how a button under each reply looks there.

---

## Part B: check-ins nobody has to remember

### The idea

The kit does the periodic checking itself, mechanically and at zero tokens. It wakes the model only when something needs a decision. You see the state of the run in the status band without asking.

### What `session-watched` does today

Read from the installed script (session-kit 0.37.3):

- It starts the command as its own child, in the background, and polls it every `--sample` seconds (default 5).
- Progress is any of three signs, taken over the process tree and all its children:
  - CPU spent (at least 0.3 s since the last sign)
  - a process starting or ending
  - stdout or stderr growing, counted only when they go to a regular file (`&> log`)
- Every `--check` seconds (default 300), it prints a line saying it decided to go on and on what evidence: "12m0s in, making progress, continuing (cpu +41s, 3 processes, output +2KB)".
- After `--stall` seconds (default 300) with no sign at all, it:
  1. writes diagnostics: the tree, and a macOS `sample` of each process
  2. ends the tree (TERM, then KILL three seconds later)
  3. exits 125
- With `--warn` it writes the same diagnostics and lets the run go on, repeating the warning each window.
- If `session-watched` itself is ended, it ends the tree with it.

So it never ends a run for taking longer than expected. It has no notion of an ETA. A run that keeps using CPU or writing output can run for days.

What can end a run today, then, is a false stall: a run that is working while showing none of the three signs. Two cases from your work:
- A model loading from disk mostly waits on I/O, which spends little CPU and prints nothing.
- A command waiting on a remote host prints to a terminal or a pipe, which `session-watched` cannot measure.

Either one is ended at the fifth minute.

### What changes: no clock ends a registered run

There are two kinds of watched run, and they get different policies.

| | A run the session waits on | A registered run |
|---|---|---|
| Examples | a test suite, a build, an install | a benchmark, a sweep, an overnight eval, anything that outlives the turn |
| On a stall | Ended at 5 minutes, as today. A hung test blocks the session and holds nothing worth keeping. | Kept running. You are notified, and the session must decide. |
| On a passed ETA | Not applicable | Kept running. You are notified, and the session must decide. |
| Who can end it | `session-watched` on a stall, or the session | The run itself, a stop at the next pause point that the session records with its reason, a stop now that you approve, or you |

A registered run is started with `session-watched --hold`. That is today's `--warn`, plus writing `held` and the diagnostics' path into the status file. The kit's watcher still never touches a process.

### What "the session must handle it" means

A stall or a passed ETA puts the run into the state `needs decision`. The kit then:

1. Notifies you on desktop and phone: "embed bench passed its ETA (21:40) at 7/14. Still running."
2. Wakes the session with the status line, the diagnostics' path, and the decision it owes.
3. Keeps the run in `needs decision` until the session records one of these through `check_in`:
   - `revise`: a new ETA with its evidence. It names the measured rate, and why the first ETA was wrong. "7 of 14 in 92 min, 13 min a model against the 6 I assumed, from the two largest models. New ETA 23:10."
   - `wait`: the run is working without showing it, with the diagnosis and the next check time. "Loading the 70B weights, disk read at 1.1 GB/s in the sample. Check again 21:55."
   - `stop at pause`: end it after the current step, with the reason. Nothing finished is lost.
   - `ask`: put a stop now, or anything else that could lose work, to you. The run keeps going until you answer.
4. Escalates while no decision is recorded:
   - the turn-end check prompts once more when that turn ends
   - each 10-minute tick wakes the session again
   - after two unanswered wakes, you are notified: "embed bench needs a decision and the session has not made one"

A revised ETA is held to the evidence. With `--progress <pattern>`, the status file carries the done and total counts from the job's own output, for example `^finished model (\d+)/(\d+)`. The kit computes a measured ETA from them. The band shows both: "ETA 23:10 (session) · 23:25 (measured)". A revision earlier than the measured ETA must say why. Each further miss repeats the flow and notifies you again. The third one asks the session to check whether the run is still productive, by comparing the rate in the last window with the earlier rate.

### Where work can still be lost

These cases sit outside both watchers:

- A background Bash run is a child of the app. If the app quits or the machine restarts, the run most likely ends with it ("The app was quit while you were working" appears several times in your sessions). This has to be verified.
- For a run whose results matter, two things protect them:
  - Write the results at each pause point, so a restart loses one step at most.
  - Launch a run longer than an hour detached (`nohup`, or `tmux new -d`), and register it with a probe.

### Who notices what

Three parties can notice something about a run, and each sees only part of it:

| | Sees a run end | Sees a run stall | Sees a remote run | Knows the time |
|---|---|---|---|---|
| The model | only when woken | no | no | no, between turns |
| The harness | yes, for a background Bash run, when it exits | no | no | no |
| `session-watched` | yes | yes: ends a waited-on run, holds a registered one | only through its ssh output | yes, while the run lasts |
| The kit's watcher (new) | yes, from the status file | yes | yes, through a probe | yes, with a timer that survives reloads |

Today, a promise to "check back in 30 minutes" sits in the first row, which has no clock. Part B moves it to the last row.

### Pause points, explained

A pause point is a place in a long job where stopping loses nothing. In a benchmark of 14 models, that's between two models: stopping there keeps every finished result. Stopping in the middle of a model throws its partial run away.

Today, "stop at the next pause point" needs the model to watch the output and act at the right moment, and it can't watch.

`--pause-mark <pattern>` tells `session-watched` which output line marks a pause point. The pattern can match a line the job already prints, so the job needs no change:

```
session-watched --label "embed bench" --status .claude/runs/embed.json \
  --eta 5400 --pause-mark "^finished model " -- python bench.py
```

Each `finished model 6/14` line is recorded in the status file as the last pause point. When you say "stop at the next pause point", the session asks for it with `check_in({ label: "embed bench", stop_at_pause: true })`. The kit writes a stop request beside the status file, and `session-watched` ends the run at the next matching line, right after model 7 finishes. Nobody has to be watching at that moment.

### Worked examples

These use your own past runs.

#### 1. A long local run (the embedding benchmark)

- 20:10: The session starts the run, watched and in the background, and calls `check_in` with ETA 21:40 and a check every 10 minutes. Its reply shows the run card.
- 20:40, one of the 10-minute ticks: The kit's timer reads the status file: running, last progress 20 seconds ago, 5 of 14 models done. It updates the band to "embed bench · 30m · 5/14 · ETA 21:40". No model turn, no tokens.
- 21:05: The run has used no CPU and printed nothing for 10 minutes. `session-watched --hold` writes the diagnostics and `held` to the status file, and the run goes on.
- 21:05, seconds later: The kit notifies you ("embed bench shows no progress at model 7/14, still running") and wakes the session: "embed bench needs a decision: no progress for 10 min at 7/14. Record revise, wait, stop at pause, or ask."
- 21:07: The session reads the diagnostics. Model 7 is the 70B one, loading from disk. It records `wait`, "reading weights at 1.1 GB/s, check again 21:20".
- 21:40, the ETA: the run is at 11/14, and the measured ETA is 22:05. The kit notifies you and wakes the session. It records `revise`: "22:10, the last three models are the largest".

On Oct 12, the same failure left `galipc` idle for over an hour before you noticed.

#### 2. A detached run on another machine

- The session starts `ssh galipc 'nohup python bench.py > bench.log &'` and returns. Neither the harness nor `session-watched` can see that process.
- The session registers it: `check_in({ label: "llama sweep", probe: "ssh galipc tail -1 ~/llm/bench.log", stall_minutes: 20, every_minutes: 10, eta_minutes: 180 })`.
- Every 10 minutes, the kit runs the probe and compares its line with the previous one. The band shows the line.
- The same line for 20 minutes wakes the session with that line. So does a probe that fails three times, for example because `galipc` went off.
- If the session forgets to register it: the turn-end gate sees `nohup` in a command left running and sends one prompt: "You left `ssh galipc 'nohup …'` running with no check-in. Register one, or say why it needs none."

#### 3. You ask "Status?" anyway

The session answers from the status file in one line: "embed bench: 9/14, 1h05m, ETA 21:50 (10 min late)". It neither tails logs nor guesses.

#### 4. The dev stack

`scripts/stack up` is listed under `services` in `.claude/claude-kit.json`, so the gate lets it pass. If the session registers it as a `service`, the kit checks its health every tick and wakes the session only if it went down. It never wakes it for time.

#### 5. A short background run

(a 6-minute test suite in the background). The harness already reports its exit, and it ends within 30 minutes, so it needs no check-in. The turn-end gate lets it through.

### What it costs

- A tick costs one file read or one probe, and no tokens.
- A wake costs one model turn, and wakes come only on an event: ended, stalled, past ETA, a pause point you asked for, or a failing probe.
- A three-hour run that goes well costs one wake, at the end.

### 1. `session-watched` writes a status file

There are five new options:

- `--status <file>`: a JSON file rewritten on every sample. It holds the label, the command, the start time, the ETA, the last progress, the state (`running`, `stalled`, `ended`, `stopped`), the exit code and the last output line.
- `--hold`: on a stall, write the diagnostics and `held`, and keep the run going. For every registered run.
- `--progress <pattern>`: a pattern with two numbers, done and total, read from the output into the status file.
- `--eta <s>`: the expected duration. The `--check` lines then report against it, for example "40m in, ETA 21:40, on time" or "past ETA by 12m".
- `--pause-mark <pattern>`: the output line that marks a place where stopping loses nothing. With a stop requested, the run ends at the next such line. "Pause points, explained" below gives the detail.

The status file is also what a `Status?` answer reads, in place of tailing logs.

### 2. A `check_in` tool, registered by the kit

```
check_in({
  label: "embed bench on galipc",
  status: "<path from --status>",        // a watched local run
  probe: "ssh galipc tail -1 ~/llm/bench.log",  // or: a read-only command for a remote or detached run
  eta_minutes: 90,
  every_minutes: 10,                      // default 10
  stall_minutes: 10,
  stop: "ssh galipc pkill -f bench.py",
  kind: "run",                            // or "service" for a stack that should stay up
  stop_at_pause: false                    // true asks session-watched to end it at the next pause point
})
check_in({ label: "embed bench on galipc", decide: "revise", eta_minutes: 150,
           evidence: "7/14 in 92 min, 13 min a model; the first ETA assumed 6" })
check_in({ label: "embed bench on galipc", decide: "wait", until: "21:20",
           evidence: "loading 70B weights, disk read 1.1 GB/s in the sample" })
check_in({ label: "embed bench on galipc", decide: "stop at pause", evidence: "..." })
check_in({ label: "embed bench on galipc", decide: "ask", question: "Stop now? Model 9 has run 40 min with no output." })
check_in({ label: "embed bench on galipc", close: "finished, 14 models measured" })
```

### 3. The kit's watcher

On each tick (`$.clock.after(every)`, with its deadline stored as the cold-cache timer does), the watcher:

1. Reads the status file, or runs the probe with a 10-second limit.
2. Updates a band row, for example "embed bench · running 1h12m · ETA 21:40 · progress 40s ago". You see this without a model turn.
3. Wakes the model with `$.prompt.submit` only on one of these events:
   - `ended`, with the exit code
   - `stalled`, meaning no progress for `stall_minutes`, or the probe output unchanged that long, with the run left up
   - past its ETA, with the run left up
   - a pause point reached, when one was requested
   - the probe failing 3 times in a row

   The wake prompt carries the status line and the decision owed. "What \"the session must handle it\" means" above lists the decisions and the escalation.
4. Notifies you on `ended`, `stalled` and a passed ETA, on your desktop and on your phone:
   - The desktop notice is the kit's own: `$.ui.notify` goes through your notification channel.
   - The mod API has no push call. The wake prompt for `ended` and `stalled` therefore tells the session to send the push (`PushNotification`) as its first act. Whether `$.ui.notify` also reaches the mobile app has to be tried.

A wake that arrives during a turn waits until that turn completes. For a `service`, the watcher checks health only and wakes on a crash. It has no ETA and never wakes for time.

### 4. The turn-end gate

`tool.call` records what was left running. That covers background Bash runs and detached launches, matched by narrow patterns in the style `guard.py` already uses: `nohup`, `setsid`, `disown`, a trailing `&`, `docker run -d`, `docker compose up -d`, `tmux new -d`, `screen -dm`, `systemd-run`, and `ssh … nohup`.

On `turn.complete`, anything uncovered gets one automatic prompt, once per run: "You left `<command>` running with no check-in. Register one with `check_in`, or say why it needs none."

Two exemptions:

- A background Bash run whose exit the harness reports and that is expected to finish within 30 minutes.
- Commands a project lists as services in `.claude/claude-kit.json`, for example `{"services": ["scripts/stack up"]}`, alongside the `test_commands` list that already exists. Without this, every "Bring the stack up" would trip the gate.

### 5. The run card

When the session starts a long run, its reply states the run card in five lines. All times are local clock times, since "in 30 minutes" goes stale.

```
Running: embed bench, 14 models, on galipc (watched, status in .claude/runs/embed.json)
ETA: 21:40; nothing ends it on a clock, and a stall or a passed ETA notifies you and waits for a decision
Next check-in: 20:20, then every 10 min; a notice reaches your desktop and phone if it ends or stalls
Pause points: after each model; say "stop at the next pause point"
Stop: ssh galipc pkill -f bench.py
```

### Draft rule for `global/CLAUDE.md` (about 90 words)

This replaces the current "No run goes on without a decision" bullet and keeps its content.

```
- **No run goes on without a decision, and the owner never has to ask how it is going.**
  A run the session waits on goes through `session-watched`, which ends it after five minutes
  without progress. One that outlives the turn runs under `session-watched --hold`, is
  registered with `check_in`, and is announced with its card. No clock ends it: a stall or a
  passed ETA notifies the owner, and the session records a decision (a revised ETA with its
  evidence, a wait with its diagnosis, a stop at the next pause point, or a question to the
  owner). A stop that could lose work is the owner's.
```

The reason, for `RATIONALE.md`: a model has no clock between turns. A promise to check back is kept only by a timer the kit holds. A check costs no model tokens until something needs a decision. A run on another machine can fail with nobody seeing it, unless something probes it.

---

## For the intent record

You approve objectives. These are candidates, worded as changes seen from outside. Both sit under G2 (focus on the parts only you can do), next to the existing objective on clear communication between agent and human that the ID-naming rule came from:

- Candidate objective: for every line the owner sends, the owner can see what became of it.
- Candidate objective: the owner learns how a long run is going, and when it needs them, without asking.

The kit session decides the actions. The likely set:

- the tag rule and the closing block
- the turn-end item check
- `--status`, `--eta` and `--pause-mark` in `session-watched`
- the `check_in` tool and watcher
- the turn-end gate for detached runs
- the `services` key in `claude-kit.json`
- the metrics below

## Measuring it

`session-transcripts` can report these before and after, per session-hour of your messages:

| Measure | Baseline (live sessions) | Target |
|---|---|---|
| Polling messages ("Status?", "What's next?", "Is it done?") | 42 | down by half within two weeks |
| Lost-item messages ("Ask me that question again", "got lost", "you missed") | 5+ | 0 |
| Auto-prompts on items the reply did address (false positives) | n/a | under 1 in 20 |
| Model wakes per run, and tokens per wake | n/a | wakes only on events |

---

## Your decisions (2026-10-29)

1. Check-in cadence: every 10 minutes by default. `ended` and `stalled` reach your phone as well as your desktop.
2. An unanswered `Do` gets an auto-prompt and a band row.
3. English tags only, in every session.
4. Untagged lines in a tagged message: reading d. The session reads them as today, and the closing block shows each reading (`Read as Do: …`, `Read as FYI: …`). The pre-send check offers a tag for each untagged line. "Untagged lines, expanded" below has the options weighed.
5. The rulebook budget: left to the kit session to propose.
6. The pre-send check: `??` triggers it, and it runs on its own for messages with four or more bullets.
7. The clarify action: parked. You keep using side chats.
8. Stalls: a run the session waits on (tests, builds, installs) keeps today's five-minute end. Only a registered run runs under `--hold`, and no clock ends it.

## Untagged lines, expanded

A message can mix tagged and untagged lines:

```
Do: rename it to Verdict
The stats row doesn't fit on a laptop screen
Ask: why is this in the styleguide?
```

The middle line could be an order (fix the row), a note (I saw this), or the reason for the rename. There are four ways to read it:

| Reading | What happens to the middle line | Cost |
|---|---|---|
| a. As today | The session infers. It may fix the row, mention it, or skip it. | You can't tell which it chose, and the turn-end check can't track it. |
| b. As `FYI` | Never acted on. | An order you forgot to tag is dropped. You see that only when you notice the row still doesn't fit. |
| c. As part of the tag above | Becomes part of "rename it to Verdict". | A wrong attachment, with an odd closing line. |
| d. As today, with the reading shown | The session infers, and the closing block says what it decided: `Read as Do: fix the stats row (done)` or `Read as FYI: the stats row`. | One extra closing line per untagged line it acted on. |

You chose d, with the pre-send check helping:

- Under d, nothing you wrote is lost, and every inference is visible in the same place as the tagged items. A wrong reading costs one correction ("that was FYI").
- The pre-send check already runs on messages with four or more bullets. For a tagged message, it can flag each untagged line and offer a tag ("Line 2 has no tag: Do or FYI?"), so most untagged lines get a tag before the message is sent.
- Indented lines and nested bullets still belong to the tag above, as Part A says. That is c, kept only where the layout shows it.
