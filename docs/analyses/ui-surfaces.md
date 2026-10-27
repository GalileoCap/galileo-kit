# How the kit surfaces in the UI, and how to improve it

Read on 2026-10-26 from `plugins/session-kit/hooks/` (`context.tsx`, `checkout.ts`, `facts.ts`) and the engine's API types (build 2.1.308). Nothing was run: no band was seen on a screen in this pass, so every finding about looks comes from the code and the types. The owner's ask: the bands are lackluster. All seven proposals were built on 2026-10-26 as `A71` (the band draws by urgency and keeps only what needs a decision), `A72` (the band's buttons act and a press is the person's signal), `A73` (the kit's numbers always on a status line, a turn line and a pane) and `A74` (failures stay on the band and an unattended end is notified). The answers taken to its open questions: a press may start the chain, and the stage rows of the transcript keep their wording.

## What the kit draws today

| Surface | Where | What it carries | Drawn on |
| --- | --- | --- | --- |
| Band above the prompt | `context.tsx:986`, one `ui.render` hook on `AbovePrompt` | The new-task offer, the chain's stage, the context figure past its threshold, the cold-cache timer, one line per usage window at 80% or more | Terminal and desktop only |
| Toast | `context.tsx`, six failure sites and `moment()` | A failed handoff, clear, compaction or effort, and the band's moments on a surface with no band | Every surface |
| Transcript row (`$.ui.log`) | `context.tsx:514`, `checkout.ts:113`, `facts.ts:272` | `session-kit chain: <stage>` rows, the turn-end line on uncommitted work and the handoff, a failed facts block | Every surface |
| Model tools | `new_task`, `clear_point` | Not a UI: the model's signal, which raises the band | n/a |

Every row of the band has the same form: a `Box` holding `<Text dimColor>` with a sentence, then buttons. The figure's row reads like this: `Context 312,000 tokens (31% of 1,000,000), up 12,000 in the last turn: find a clear point, commit, write the handoff, ask to compact.` followed by `Dismiss`. Up to five rows stack: one of offer, chain or figure, then the cold timer, then one per window.

## What the engine offers and the kit does not use

- Color and weight. `Text` takes `color` (theme keys `success`, `warning`, `error`, `subtle`, `suggestion`, `claude`, and more), `bold`, `size`, `weight`, `tabular`, `mono`. The kit uses `dimColor` and nothing else.
- Buttons as actions. `Button` takes `variant: 'primary'`, `hotkey`, `action` (a chord the person binds), `plain`. Only the new-task offer has action buttons (A65, an effort for the new task carried by the offer). The figure, the chain, the cold timer and the windows have Dismiss alone.
- A status line. `$.ui.status(text)` pins one line per plugin under the prompt, on every surface, until replaced. The kit never calls it.
- A pane. `$.ui.open({ id })` plus a `Pane` render hook: a framed region, docked in fullscreen, drawn on every surface including the phone. Unused.
- Other render sites: `TurnDuration` (the `Baked for 3s` line, terminal), `PromptHint`, `InfoNotice`, `Spinner`. Unused.
- Native notifications: `$.ui.notify`, for a chain that ends while the person is elsewhere. Unused.
- Graphics: `Svg` on desktop, `Raster` on the terminal. A50 (the plan's usage windows and the growth per turn beside the context figure) rejected a sparkline for the cross-surface cost. A gauge made of `Text` cells avoids it.

## Findings

1. No hierarchy. The code knows three tiers of urgency (`advice()` tiers 0 to 2, `limitTier` 80 and 95) and draws all of them in one dim sentence. A window at 95% looks like a cache notice.
2. The kit is silent until there is trouble. The figure's row draws only past the threshold. Before that the person has no view of context, usage windows or cache age, which are the numbers they act on. The band is an alarm and there is no gauge.
3. The rows are prose for the person and the person is told to act by hand. "find a clear point, commit, write the handoff, ask to compact" is instruction text, with a Dismiss button as the only control. The offer row shows the better form: a sentence and the buttons that do it.
4. Stacking costs height for little. Five dim rows take transcript space (the band may take up to half the terminal) and each repeats a Dismiss. `AbovePrompt` carries `maxRows` and `scroll`, which the kit ignores.
5. Failures vanish. A handoff or compaction that did not run, which stops the chain, is a toast on a timer. The stage row in the transcript survives, but its wording is the kit's own (`session-kit chain: the handoff did not run (...), so the chain stops here`).
6. Dismiss is the only keyboard story. `hotkey` works only while the band holds focus (ctrl+x tab or a click), and the kit sets none. A band the person never focuses is mouse only.
7. The phone and VS Code get a toast and no band. A51 (the moments the band shows go out as a toast where no band is drawn) sends the text once, and there is no state to look at afterward. A `Pane` is drawn on every surface.
8. No place to ask what the kit is doing. Chain state, cold-timer age, handoff freshness, uncommitted work and the last test run are each visible only when their moment fires.

## Proposals, in the order I would build them

Each is small and independent except where noted. None adds a Protocol layer or an option.

- P1. Give the band a hierarchy. Keep the rows, change how they read. A bold label (`Context`, `Usage 5h`, `Cache`), the figures in `tabular`, a color by tier (`subtle` below the threshold, `warning` past it, `error` at 95% or a stopped chain), and the instruction sentence cut to the verb. Example, past the threshold: `Context 312k / 1M  31%  +12k last turn` with the buttons beside it. This is a rendering change in one hook and the existing engine tests keep their lines by text.
- P2. Buttons that act. On the figure row: `Handoff now` (the handoff command, as the offer does) and, with the chain on, `Start chain`. On the cold row: `Run chain now`. Dismiss stays last. This puts what the sentence tells the person to type behind a press. Needs a decision: whether a press from the band counts as the person's request for the chain (A19, one task per context: the rule, then the signal, and A49, the cold-cache timer runs the chain before the cache goes cold, say who signals).
- P3. An ambient status line. `$.ui.status('ctx 31% · 5h 62% · cache 4:10')`, always on, replaced as the figure moves, so the band can stay quiet until it must escalate and the person always has the numbers. One per plugin, every surface, which also gives the phone and VS Code something where they now get only toasts. To verify before building: how the status line sits beside the person's own `statusLine` setting, and the redraw cost of a call per tool call (the figure already updates at that rate).
- P4. One row for the quiet moments. Merge the cold timer and windows under 95% into the status line (P3), keep a band row only for what needs a decision: an offer, a running or stopped chain, a figure past threshold, a window at 95%. The band goes from up to five rows to usually zero or one.
- P5. Failures stay. A stopped chain becomes a band row in `error` that stays until dismissed, with the reason and, where it fits, a retry button. The toast stays for surfaces with no band. The transcript stage rows get plain wording.
- P6. A kit pane, last. A `Pane` opened by a slash command: gauge, windows, cache age, the chain's stage history, handoff freshness, uncommitted files, last test. It is the only surface every device draws, and it answers finding 8. It is also the largest piece: a command registration, a footprint entry, state, tests. Under the rule of no abstraction before its second use, build it only if P3 leaves the person asking for the detail.
- P7. Cheap extras, each on its own merit. `TurnDuration` appended with `· ctx 31%` (terminal only). `$.ui.notify` when an unattended chain ends or stops.

## What I would not do

- A sparkline or SVG gauge in the first pass: the numbers carry the decision (A50 reached the same view), and a `Text` bar gives the same thing on every surface.
- A color for every row. Color only the tiers. A band that is all colors is as flat as one that is none.
- Colors by hard-coded value. Theme keys follow the person's theme, light and dark.

## Open questions for the owner

- Which surface do you read the band on most, the desktop app or a terminal? Desktop allows `Svg` and the terminal does not.
- Do you want the numbers always on view (P3, the kit becomes a gauge) or only when they matter (today, but better drawn)? P3 and P4 are one answer and the rest of the list holds either way.
- Is "lackluster" how it looks (P1), what it does (P2, P5), or that it hides until trouble (P3, P4)? The three call for different first steps.
- P2: may a press on the band start the chain, or does that stay the model's signal?

## Cost

P1 and P2 are changes to `context.tsx`'s render hook and its engine tests. P3 adds a `$.ui.status` call, which `footprint.toml` (A60, the kit's reach held to a reviewed footprint) will list as a new `$` call with a reason. P6 adds a command and a pane to the footprint. All of it is subject to the owner's install gate (O2, what runs in my sessions changes only when I choose).

This also covers the `docs/PLAN.md` item 8 of the mod analysis: review and change the band's usage-window line (A50), and consider facts on the UI (the facts section of A63, facts from git and the session beside the model's prose in the handoff). The facts line fits P3 or P6.
