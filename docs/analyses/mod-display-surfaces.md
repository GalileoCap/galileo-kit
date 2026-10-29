# Every way a mod can show information

Read from the engine's own contract for Claude Code 2.1.308: the `plugin-authoring` skill's `reference.md` and its `types/claude-code.d.ts` (about 22,500 lines). Where this note and those files disagree, the files win, since the API moves between releases. Two claims below were checked under the engine's own test runner on 2.1.308, and each names that check. The rest is the contract's word alone, and none of it has been seen drawn.

The owner's question: the band is not enough for some of what the kit needs. How the kit draws today, and the proposals built from it, are in `ui-surfaces.md` beside this file. This note lists every place a mod can put something in front of the person or the model, what each holds, and which need each answers.

## The four surfaces

A drawing hook is told which surface draws it, `e.surface`, and draws with that surface's element table, `$.ui.resolve(e)`.

| Surface | What it is | Elements beyond the six every surface has |
| --- | --- | --- |
| `terminal` | the CLI (Ink) | `Input`, `Select`, `Client`, `Raster`, `Image` |
| `desktop` | the Code tab of the desktop app, where the owner works | `Input`, `Select`, `Svg`, `Client` |
| `vscode` | the VS Code extension | `Input`, `Select`, `Svg` |
| `mobile` | the mobile app | `Svg` only: no field, no select |

The six every surface has: `Box`, `Text`, `Button`, `Link`, `Code`, `Markdown`. Under `claude -p` or an SDK host no surface attaches, and nothing drawn shows.

## Places a mod draws into: `ui.render`

A `ui.render` hook answers for one component instance: it returns its own tree, rewrites the props the engine draws from (`next({ ...e, props })`), or passes (`next(e)`). The engine's drawing is a tree too, so a hook can draw `next(e)`'s result inside its own. The kit's band keeps other plugins' rows that way.

### Sites the mod owns

| Site | Where | Size | Interactive | Surfaces |
| --- | --- | --- | --- | --- |
| `Pane` | a framed region the surface places: docked beside the transcript (terminal fullscreen from 110 columns), else inline above the prompt, and on the desktop where the app places it | the dock up to 45% of the width, or `rows` asked inline, with several panes as tabs of one frame | buttons, fields, selects, focus ring, hotkeys, scroll | all four |
| `AbovePrompt` (the band) | directly above the prompt | in fullscreen, up to half the terminal less the prompt, and a taller tree scrolls | buttons, fields, hotkeys once focused, and the person collapses it with `[-]` | terminal, desktop |

A pane is opened by `$.ui.open({ id, title })` and drawn by a hook on `{ component: 'Pane', requestId: id }`. It stays until closed by the plugin (`$.ui.close`) or the person (its mark, ctrl+x x), and `ui.close` tells the plugin which. Options: `focus` (take the keys), `closeOnEscape` and `holdToasts` (a dialog), `rows` and `columns` (the size wanted). Opened at the person's word it is placed at any width. Opened unasked, a terminal places it from 144 columns (110 for an id the person once opened). `$.ui.panes()` lists the plugin's open panes, which survive a reload of the module.

### Engine sites a mod can rewrite or replace

| Site | What it is | Typical use | Surfaces |
| --- | --- | --- | --- |
| `SessionMode` | the dim mode labels at the right of the prompt footer | add a label or a chip, a `Button` included (checked under the test runner, terminal and desktop) | terminal, desktop |
| `PromptHint` | the hint line under the prompt (`? for shortcuts`) | `tail` adds dim text at its end (terminal only so far), or a whole tree | terminal, desktop |
| `Spinner` | the line that animates while a turn runs, and on the desktop the row with the turn's mark | rewrite the word or message (`Compacting`), or draw a tree | terminal, desktop, vscode |
| `TurnDuration` | the line closing a turn (`Baked for 3s`) | the kit adds `ctx 31%` here | terminal |
| `UserMessage`, `AssistantMessage` | each message row of the transcript | annotate or redraw a message, knowing from `onScreen` which of its rows are visible | all |
| `ToolUse`, `ToolResult`, `ToolGroup` | a tool call's row, its result, a collapsed group | badges, a summary, a custom view of the kit's own tools' results | all |
| `ToolProgress` | the run-in-background pill under a running call | rewrite the hint | terminal |
| `CommandOutput` | the row a slash command printed | draw a command's answer as a tree | all |
| `InfoNotice` | the dim lines under the logo | rewrite or hide a startup notice | terminal |
| `AskUserQuestion` | the engine's question dialog | redraw the dialog | all |

### Elements of note

- `Markdown`: model-style text (headings, lists, tables, code, links), drawn as a reply is. Link clicks can come back to the plugin as `ui.press`.
- `Raster` (terminal): a grid of coloured cells in one element, for a sparkline or a heat map. `$.ui.blit` repaints it without a render pass.
- `Image` (terminal): a PNG or RGBA picture where the terminal can draw one (kitty, Ghostty, iTerm2 3.5), its `alt` text elsewhere.
- `Svg` (desktop, vscode, mobile): vector drawing, so a chart in a pane on the desktop.
- `Client` (terminal, desktop): a region drawn by a surface module of the plugin's own, on the drawing thread, with local state, its own timers, pointer and key events, and a message port back to the hooks (`ui.message`). It is the escape hatch when a tree redrawn from `$.state` is too slow or too coarse: a live chart, a drag, a custom list.
- `Button`: `variant="primary"` for the main action, `plain` for a bare label, `hotkey` for one key, `action` to bind it to one of the engine's keybinding actions so the person's chord presses it from the prompt.

## Calls that show something without a drawing hook

| Call | What the person sees | Stays | Reaches the model |
| --- | --- | --- | --- |
| `$.ui.status(text)` | one pinned line under the prompt, the plugin's own | until replaced or cleared | no |
| `$.ui.toast(text)` | a small box over the transcript's top right, under the plugin's name | a few seconds (`timeoutMs`), or until clicked | no |
| `$.ui.notify(text)` | a native notification through the person's channel (the OS, the terminal bell) | as the OS keeps it | no |
| `$.ui.log(text)` | a dim notice line in the transcript, or the debug log with `to: 'debug'` | in the transcript | no |
| `$.ui.notice(tool_use_id, text)` | one line under an open permission dialog | until the call resolves | no |
| `$.ui.ask(question, options)` | the engine's question dialog, resolving to the choice | until answered | no |
| `$.session.append({ message })` | a `system` row is a notice in the transcript, and a `user` row is hidden from the person | kept in the transcript file | `user` yes, `system` no |
| `command.run` answer `{ text }` | the output row of a slash command, markdown | in the transcript | yes, as the command's record |
| `$.audio.play({ asset })` | a sound from a file of the mod's | the sound's length | no |
| `$.ui.copy`, `$.ui.view`, `$.ui.scroll`, `$.ui.focus` | put text on the clipboard, show an agent's transcript, scroll a site, move the focus ring | | no |

The model's side, for completeness: a `prompt.compose` hook adds a section to the system prompt, a `prompt.submit` hook rewrites the person's prompt, and a tool's result or a hook's added context is what the model reads after a call.

## What the band cannot do, and where it goes instead

| Need | Why the band falls short | Where it fits |
| --- | --- | --- |
| A view kept open beside the work (context, usage, chain, checks) | the band sits over the prompt and takes rows from it, and holds what needs a decision | a `Pane`, kept open, with a chip to hide and show it (the kit's pane from 0.41.0) |
| A one-click control that is always there | the band shows only when it has a row | a `Button` in `SessionMode`, the footer's mode labels |
| History or a list longer than a few rows | the band is capped at half the screen less the prompt | a `Pane`, which scrolls, or several panes as tabs |
| A chart or a trend (context over the session, usage windows) | text rows only read as numbers | `Svg` in a pane on the desktop, `Raster` on the terminal, `Client` for a live one |
| Something tied to one message or one tool call | the band is one place for all of the session | `UserMessage`, `AssistantMessage`, `ToolUse` or `ToolResult` rows |
| Telling the owner while away from the screen | the band is seen only when looked at | `$.ui.notify`, and a sound |
| A short-lived confirmation | a band row waits for its ✕ | `$.ui.toast` |
| What the turn is doing right now | the band does not move with the turn | the `Spinner`'s word or message |

## Open on the desktop

Seen on 2.1.308 only under the test runner, which checks a tree against the element table and not where a surface draws it: whether the desktop draws a `Button` in `SessionMode`, how the desktop places a `Pane`, and whether it places one opened unasked at the session's start. The owner's look decides these.
