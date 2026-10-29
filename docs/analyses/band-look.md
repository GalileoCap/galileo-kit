# How the band looks, and three layouts to choose from

Read on 2026-10-29 from `plugins/session-kit/hooks/band.tsx`, `hooks/lines.ts` and the owner's screenshot of the desktop band, the Held row above the Context row. The owner's ask: "I don't like the way the bands are looking (not just this new one, all of ours)". `docs/analyses/ui-surfaces.md` built the band's content (`A71`, the band draws by urgency and keeps only what needs a decision; `A72`, the band's buttons act). This read is about its look alone, and changes no row's content or trigger.

## What the screenshot shows

```
Held     Your message is back in the box. Haiku found: [Send as is] [Use the rewrite]                    ✕
  · Do M27 before installing: the id M27 appears without its name
Context  292k / 1M  29%  +2k last turn  [Handoff] (Handoff and compact)  runs itself at 10:49           ✕
```

Both labels are bold orange, `Handoff and compact` is a filled white pill, and each ✕ sits at the far right edge.

## Findings

1. Two rows, one colour. Held needs the owner now, and Context at 29% does not, yet both labels are the same bold `warning`. The colour says nothing about which row to read first. Every row of the kit has its own label colour rule (Failed `error`, Held and No line `warning`, Context by tier, Chain and Cache `subtle`, the windows by percent), so on a band of three rows the colours are noise.
2. The loudest thing on the band is the least urgent. The only filled button is `Handoff and compact`, on the Context row. The eye goes there before the held message. `primary` is set per row, so two rows can each have one.
3. Nothing lines up. Each row is a `Box` with `gap={1}`, so the text starts wherever its label ends: `Held` and `Context` differ by three cells, and with Failed, No line, Chain and Cache every row starts at a different column. The buttons fall wherever the sentence ends.
4. Buttons sit in the middle of sentences. On the Held row the text ends "Haiku found:" and the colon points at two buttons, while the findings it introduces are on the lines below. On the Context row the dim "runs itself at 10:49" comes after the buttons and reads as a caption of `Handoff and compact`, though it is the cold-cache timer.
5. The ✕ is far from its row. The spacer pushes it to the window's edge, so on a wide desktop it is a lone glyph a long way from the row it closes, and the eye has to travel to pair them.
6. The percent fights the colour. Context draws once the tokens pass the kit's threshold, which on a 1M window is 29%. An orange label beside "29%" looks like a false alarm. The figure that tripped the row (tokens against the threshold) is not the one shown.
7. The rows speak in different grammars. Held, No line, Failed are states, Context and Cache are topics, Chain is a mechanism, the offer row and the window rows have no label at all. The window row is a whole sentence in colour ("The 5-hour usage window is at 96% and resets at 14:30.").
8. Tight and flat. `rowGap="xs"` packs the rows against each other and against the engine's own band beneath, with nothing marking where the kit's part ends.

## Three layouts

Each keeps every row's content and buttons; only the drawing changes. All three use only what `band.tsx` already uses (`Box` with `gap`, `flexDirection`, `justifyContent`; `Text` with `bold`, `color`, `dimColor`, `tabular`; `Button` with `variant` and `plain`), except where marked.

### A. A ledger

One grid for all the band. A fixed label column (eight cells), the text, then the buttons at the right, the ✕ right after them. Colour goes to the label of the most urgent row alone, and the others are `subtle`. One `primary` button on the band, on the most urgent row. Detail lines (the findings) indent to the text column.

```
Held     Your message is back in the box.          [Send as is] [Use the rewrite]  ✕
         · Do M27 before installing: the id M27 appears without its name
Context  292k / 1M · 29% · +2k last turn           [Handoff] [Handoff and compact]  ✕
         Compacts by itself at 10:49 if left.
```

Cost: small, one helper that draws a row from (label, text, buttons, details), and a rank to pick the coloured row. The closest to today.

### B. Cards

Each row becomes two lines: a headline (label and one sentence) and, beneath it, the buttons and any note, indented. A thin rule (`─`, dim) between the kit's rows and the engine's band. Taller (about twice the lines), but nothing is mid-sentence and each card reads top to bottom.

```
● Held · your message is back in the box                                             ✕
    Do M27 before installing: the id M27 appears without its name
    [Use the rewrite]  [Send as is]
● Context · 292k of 1M (29%), +2k last turn · compacts by itself at 10:49            ✕
    [Handoff and compact]  [Handoff]
────────────────────────────────────────────────────────────────────────────────────
```

The `●` takes the tier colour and the label stays plain bold, so the colour is a small dot beside a plain word. Cost: as A, plus the rule. Height grows against `maxRows`, which the kit ignores today.

### C. One line, the rest on demand

The band shows the most urgent row only, in the ledger form of A, and a dim count of the others ("+1 more"), a press of which shows them. The Context row leaves the band unless it is past tier 1 (the figure stays on the status line, `A73`). The quietest band. The cost is a press to see a second row, and a new piece of state (expanded or not).

```
Held     Your message is back in the box.          [Send as is] [Use the rewrite]  ✕  +1 more
         · Do M27 before installing: the id M27 appears without its name
```

## What I would pick

A, with one change from C: Context leaves the band below its higher tier, since 29% is not a decision. A fixes findings 1 to 5 and 7 by one rule each (one grid, one colour, one primary, buttons together at the end), and is the smallest change. B is the better read if the band often holds two or more rows. I have seen it hold one or two. Finding 6 is answered either by C's change or by showing the row's trigger ("292k, past 250k", the default threshold).

## Open questions for the owner

- Which of A, B or C, or which parts of each.
- What you dislike most: the colours, the buttons, the alignment, the wording, the ✕, or the density. The findings above are my reading of the screenshot, and yours may differ.
- Whether the Context row should leave the band until its higher tier, with the figure kept on the status line.
- Whether the `primary` button may move between rows by urgency, so the filled button is always the next thing to do.
