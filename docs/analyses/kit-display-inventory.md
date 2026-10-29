# Everything session-kit shows, and what the pane should hold

Read on 2026-10-29 from `plugins/session-kit/hooks/` at session-kit 0.41.0; the band is unchanged through 0.42.4. The first part lists every place the kit puts something in front of the person, by surface. The second part reads the pane against that list and proposes its new content. What reaches the model is listed in `docs/what-reaches-the-model.md`, and only summed up here.

## 1. What the person sees

### The band above the prompt (terminal and desktop)

A ledger (`A86`, the band is a ledger, and the context row joins it at its higher tier): one row per item, a label, its text, its buttons and a ✕. Only the leading row has a coloured label and a filled button. Drawn only while a row exists, in this order.

| Label | When | Text | Buttons |
| --- | --- | --- | --- |
| `Failed` | a handoff, compaction, clear or effort change did not run | the failure in one sentence | `Try again` for a chain's step |
| `Held` | the pre-send check held a message | "Your message is back in the box." and one `·` line per finding | `Send as is`, `Use the rewrite` when there is one |
| `No line` | a reply left one of the owner's tagged items without its closing line | `Do-2 "…" · Ask-1 "…"` | none |
| `New task` | the model called `new_task` | the task, and "Proposed effort <level>: <reason>" | `Handoff, clear, effort <level>`, `Handoff and clear`, `Keep going here` |
| `Chain` | a chain runs or stopped | "Clear point: the handoff, the compaction and the continue run when this turn ends.", "session-kit is writing the handoff.", "session-kit is compacting the context.", "Compacted. The next step is yours: <note>", with "The chain stopped since <why>" | none |
| `Context` | the context past 1.2 times the trigger (300k by default) | `412k / 1M  41%` and `+12k last turn`, with "Handoff and compact run by themselves at <hh:mm>." under it while the cold timer is set | `Handoff`, `Handoff and compact` (chain on), hidden while a turn runs |
| `Cache` | the cold timer is set and no context row shows | "handoff and compact at <hh:mm>, before it goes cold" | `Run chain now` |
| `Usage` | a usage window at 95% (80% with the status line off) | `5-hour window 96% · resets 14:30` | none |

### The status line under the prompt (every surface)

One line, rewritten when its text changes: `ctx 41% 412k +12k · you 12m · 5h 62% · 7d 20% · compacts 14:30`. The context, its growth in the last turn, the time since the person's own last message, each usage window (with " resets <when>" from 80%), and the cold timer. Off with the `statusLine` option.

### The footer chip (terminal and desktop)

`kit`, beside the footer's mode labels: shows and hides the pane (`A87`, the kit's pane is shown and hidden by a chip, and kept across sessions).

### The pane (every surface, opened by the chip or `/kit`)

Five headings over plain lines (`A73`, the kit's numbers always on a status line, a turn line and a pane):

- Context: `412,000 / 1,000,000 tokens (41%)`, a text bar, `+12,000 tokens in the last turn`.
- Usage: one row per window, `5h  62%  ██████░░░░ resets 14:30`.
- Cache: `Compacts at 14:30`, or `No timer`.
- Chain: `Idle`, the stage, the failure or the offer, then up to eight journal lines `14:02  <stage>`.
- Checks: `Handoff: <fresh, stale, missing>`, `Uncommitted: <n> files`, `Last test: PASS <command>, 14:05`.

### The line that closes a turn (terminal)

The engine's `Baked for 3s` gets ` · ctx 41%`, the context the turn ended at.

### Lines in the transcript (every surface)

- `session-kit chain: <stage>`, one per stage of a chain.
- At a main-loop turn's end, when it applies: "session-kit: 3 uncommitted changes at the end of the turn. CLAUDE.local.md predates the last commit (/session-kit:handoff)."
- When the last test run failed, or passed on a tree that changed since: "session-kit: the last test run (<command>, <hh:mm>) failed, and none has passed since." or "… passed on a different tree: files have changed since it ran."
- "session-kit: the pre-send check found nothing, so the message went on."
- "session-kit: the facts were not added to CLAUDE.local.md (<error>)."
- The answer to `/kit`: "The session-kit pane is open.", "… is hidden.", or "… waits for room: <why>".

### Toasts (only where no band is drawn: the phone, VS Code)

The band's moments in a sentence: the context warning, a usage window at 80% and 95%, the new-task offer, the chain's stages, a failure.

### Native notifications (the OS)

"session-kit: compacted, the next step is yours: <note>" when a chain ends with the owner's step, and a chain's failure.

### Prompts the kit sends as the person

The continue after a compaction, the re-sent prompt after a clear, the prompt about a missed tagged item, and a held message sent as is. Each shows as a prompt in the transcript.

### What the model reads, in short

The context advice beside tool results, the checkout's facts beside a prompt, the tagged items' instructions, the guard's refusals, the formatters' and the tells' notes after an edit, the two tools `clear_point` and `new_task`, and the instructions to a compaction. All in `docs/what-reaches-the-model.md`.

## 2. The pane today, read against that list

1. It repeats the status line. Context, usage and cache are the same numbers the status line already shows, in longer words.
2. It holds nothing the person acts on. No button: every action is on the band, and the pane only describes.
3. The parts that are the pane's alone are the weakest. The chain journal is a list of stage sentences, and the checks are three bare lines with words such as `fresh` and `UNKNOWN`.
4. It has no hierarchy. Five bold headings of equal weight, plain text under each, no colour, and a text bar drawn in block characters on a surface that can draw a real one.
5. It ignores the surfaces. The desktop has `Svg` and a real layout, and the pane draws as on a terminal.
6. What a session most often wants to know is absent: the owner's open tagged items, what the session committed, what is owed, and the next step the handoff records.

## 3. A proposal for the pane

The pane becomes the session's dashboard: where this session stands with the owner, and a place to act on it. The band keeps what needs a decision now, the status line keeps the numbers, and the pane holds the rest.

In order, each section drawn only when it has something:

1. Your items: The owner's open tagged items (`Do-4 "…"`, `Ask-1 "…"`), from `openItems`, each until a reply gives its closing line. The review behind `A82` (a tagged line is handled as its tag says) found five asks to put the open questions to the owner again.
2. This session: The commits made since the session started (short hash and first words), the uncommitted files by name, and the last test run with its verdict in colour.
3. Next: The next step and the open questions from `CLAUDE.local.md`, and the `OWED.md` entries not yet seen by the owner.
4. Context: One gauge (an `Svg` bar on the desktop, a text bar elsewhere) with the trigger and the firmer tier marked on it, growth per turn as a small sparkline, and the cold timer. The buttons `Handoff` and `Handoff and compact`, so the pane can act where the band is not drawn.
5. Usage: One gauge per window with its reset.
6. Chain: Only while one runs or its last run failed: the stage and its journal.

Built with the kit's ledger look (`A86`), a label column and the text beside it, so the band and the pane read as one design.

## Open for the owner

- Which of the six sections earn their place, and in what order.
- Whether the pane should carry buttons, or stay a view and leave every action to the band.
- Whether the numbers the status line shows belong in the pane at all.
- Whether the desktop should get real graphics (`Svg` gauges and a sparkline), at the cost of a second drawing path beside the terminal's text.
