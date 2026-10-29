# Owed

What a change leaves to do outside the code, one entry per change, under the moment it is due. Entries are only ever added. `session-owed --since <ref>` lists what a range of history owes.

## At the install of session-kit 0.35.0

### main, b9b49e7 and before: the terminal's engine at 2.1.308

From 0.28.0 on, the hooks module shares `gitOutput` across files (`e7c005e`), which the terminal's `claude` 2.1.296 refuses, so a terminal session would load none of the kit's in-process hooks. The nix-darwin repository moves `nixpkgs-unstable` to a revision carrying claude-code 2.1.308 in its commit `73b6118`, built and checked: the kit validates and its 67 engine tests pass on that binary. The switch needs the owner's password:

```bash
sudo darwin-rebuild switch --flake ~/.config/nix-darwin
```

Then `command claude --version` prints 2.1.308. The `chain` option in `~/.config/nix-darwin/claude/settings.json` is the owner's uncommitted change there, and with it on the chain and the cold-cache timer (`A49`) run after the install.

### main, b9b49e7: pushed

The marketplace clone under `~/.claude/plugins/marketplaces/galileo-kit` pulls from GitHub, so the nineteen commits from 0.22.0 to 0.35.0 reach it only once `main` is pushed (`git push origin main`), on the owner's word.

### main, b9b49e7: the plugin updated in every scope

The kit is installed at user scope and at project scope in ten projects, each recorded at 0.21.1 in `~/.claude/plugins/installed_plugins.json`. Run with `command`, past the shell's alias:

```bash
command claude plugin marketplace update galileo-kit
command claude plugin update session-kit@galileo-kit --scope user
```

Then from each project that records a project-scope install, `command claude plugin update session-kit@galileo-kit --scope project`. Whether the user-scope update moves the project entries too is unverified, so `installed_plugins.json` is read after it. Running sessions keep 0.21.1 until `/reload-plugins` or a restart, the desktop app's included.

## After the install of session-kit 0.35.0

### main, b9b49e7: what only a real session proves

Each of these ran in the engine's tests alone: the facts section after a handoff (`A63`), the projected context figure (`A62`), a chain in a terminal session, the cold-cache timer (`A49`), the Haiku judge's verdicts (`A54`), and `/effort` run by the new-task offer's press in the desktop app (`A65`). `docs/PLAN.md`, Next item 8, holds the owner's two reviews: the usage-window line (`A50`) and facts on the UI.

## At the install of session-kit 0.35.1

### main, A66: the test log's fix pushed and updated

`A66` (a test run is what the guard calls one, and a stale run is said once) reaches a session only through the marketplace: `main` pushed on the owner's word, then the marketplace and the plugin updated as for 0.35.0. This repository's runner entry is now `claude plugin test`, so its engine tests are logged once the terminal's `claude` is 2.1.308.

## At the install of session-kit 0.35.2

### main, C2 and A67: the hooks the security default skips removed

The kit hooks neither `classic.PostToolUse`, `classic.PostToolUseFailure`, `classic.PostModelSwitch` nor `session.compact`, events the organization's security default sends past it (`C2`, `A67` the kit hooks no event the security default sends past it). It reaches a session only after `main` is pushed on the owner's word and the plugin is updated at user scope and in each project install, as for 0.35.1. Until then every session on 0.35.1 shows a skip notice once for each of those events it meets.

## At the install of session-kit 0.35.3

### main, A68: the warning firms at 300,000 tokens

The context warning's second tier moves from 500,000 to 300,000 tokens and its third from 750,000 to 400,000, and a tier that rises is said at once (`A68`, the warning firms at 300,000 tokens and stops at 400,000). It reaches a session only after `main` is pushed on the owner's word and the plugin is updated at user scope and in each project install, as for 0.35.2. `global/CLAUDE.md` says "firmer from 300,000", so the link at `~/.claude/CLAUDE.md` carries the sentence at once and the sessions on 0.35.2 warn later than it says until they update. Only a real session proves the second tier: the check is a long run that crosses 300,000 tokens.

## At the next rebuild of the nix-darwin configuration

### ~/.config/nix-darwin, the deny rules for Artifact and the iOS simulator

`claude/settings.json` in the configuration now denies the `Artifact` tool and the `mcp__Claude_Code_iOS_Simulator` server (`docs/analyses/restart-size.md`). `~/.claude/settings.json` is a link into the nix store, so the rules reach a session only after the owner runs the configuration's rebuild, and the file holds the owner's other uncommitted change (the `chain` option) beside them. The check after the rebuild: the next desktop session's `api-request-shape` record, which should hold no `Artifact` tool and no `mcp__Claude_Code_iOS_Simulator__control` (about 14.5k tokens fewer in the prefix). Only the Artifact rule was shown to work, in a terminal session. The simulator rule is unproven on the app's own server.

## At the install of read-aloud 0.1.0

### main, A69: the final answer read aloud

A new plugin of the marketplace (`A69`, the final answer read aloud by its own plugin). It reaches a session only after `main` is pushed on the owner's word and `claude plugin install read-aloud@galileo-kit` is run, at user scope for every project. A session that also loads it from the mods folder for the live check would draw its row twice: remove the link `~/.claude/dev-mods/<session id>/read-aloud` before the install. The check: in the desktop app, an answer read from its first sentence after the tool calls, the stop button ending it after the paragraph, and `/read-aloud auto` reading the next answer as its turn ends.

## At the install of read-aloud 0.2.0

### main, A69: the stop is immediate

read-aloud speaks each paragraph through a `/usr/bin/say` it spawns, and a stop kills it (`A69`, the final answer read aloud by its own plugin), by the owner's ask. It replaces the 0.1.0 install above, which never ran: the same command and the same removal of the mods-folder link, and in the check the stop button ends the voice at once, mid-sentence.

## At the removal of read-aloud

### main, A70: nothing is owed

read-aloud was parked and removed (`A70`, read-aloud parked and removed from the kit), so the two entries above are void: `claude plugin install read-aloud@galileo-kit` is not to be run, and the desktop check of the immediate stop is not owed. Optional: delete `~/.local/share/read-aloud/` (about 1.1 GB of Kokoro and Piper environments, weights and samples).

## At the install of session-kit 0.36.0

### main, A71 to A74: the band, the status line, the pane and the failures

The new band, the status line, `/kit`, the turn line, the failure rows and the notices (`A71` the band draws by urgency, `A72` the band's buttons act, `A73` the kit's numbers on a status line, a turn line and a pane, `A74` failures stay on the band) reach a session only after `main` is pushed on the owner's word and the plugin is updated at user scope and in each project install, as for 0.35.3. Only a real session proves how they look and act, and none has been seen yet: the colours in the desktop theme and the terminal's, the status line beside the person's own `statusLine` command, `Handoff and compact` and `Run chain now` running the handoff and `/compact` from a press, the turn line finding its turn by duration, `$.ui.notify` reaching the OS, `/kit` opening the pane on each surface, and the failed row's `Try again`. The `statusLine` option turns the status line off if it collides.

## At the install of session-kit 0.37.0

### A75: Swift projects regenerate their layers

`A75` (the layers pack holds Swift) reaches a project only through the marketplace: `main` pushed on the owner's word, then the plugin updated as for 0.36.0. brain-dumping then adds a `swift` block under `layers` in its `.claude/claude-kit.json` (`core`, `shell`, `tests`, `core_module`), runs `session-codeintel layers`, and retires its hand-written `lint/ast-grep/` rules and tests, which the generated files replace (the command refuses a file it did not write, so the old ones are removed first).

## At the install of session-kit 0.37.1

### The band's rows: a row gap, centred rows, and a small ✕ at the right

The band's rows drew into each other on the desktop (the Context row's buttons ran into the Cache row), so the column has a row gap, each row centres its children, `Run chain now` is a primary button like `Handoff and compact`, and each Dismiss is a plain ✕ at the row's right edge. It reaches a session as 0.36.0 does. Only the desktop proves the spacing and the ✕: `rowGap` and `flexGrow` there are known only from the engine's declarations.

## At the install of session-kit 0.37.2

### The status line gives the time since your last message

The status line's `ctx` part ends with `you 12m`, the time since the last prompt that is the person's own words (an automatic handoff, a notification or a continue does not reset it), redrawn when the minute turns. It reaches a session as 0.36.0 does. Only a real surface shows it: the engine's stand-in clock proves the text and the reset, and the redraw on the desktop's and the terminal's status line is unproven.

## At the install of session-kit 0.37.3

### One context row when the cold timer is set, and a shorter status line

The Context row and the Cache row offered the same chain (`Handoff and compact`, `Run chain now`), so with the `chain` option on the context row ends "runs itself at <hh:mm>" and the Cache row is drawn only when no context row is. The context row's ✕ stops the timer as well. The status line drops the parentheses and "ago" (`ctx 30% 302k +5k · you 12m · 5h 31%`) and writes the timer as `compacts <hh:mm>`, so the usage window should fit on the desktop. It reaches a session as 0.36.0 does. Only the desktop proves that the usage window now fits and that one row reads clearly.

## At the install of session-kit 0.38.0

### main, A82 and A83: tagged lines, their ids and the turn-end check

A prompt of the person's with `Do:`, `Decide:`, `Ask:` or `Later:` lines reaches the model with the items' ids (`Do-1`) and the closing-line forms beside it, and a reply that leaves an item without a line draws a "No line" row on the band and sends one prompt per item (`A83`, tagged items get ids from the kit and a turn-end check). It reaches a session as 0.36.0 does. The engine's tests prove the parsing, the ids, the closing and the single prompt. Only a real session proves three things: that the turn's `answer` holds the closing lines when the reply ends after a tool call (the desktop's wrap-up), that the desktop marks pasted text as `<pasted_content>` in the prompt the hook reads, and that the work instance lets the tagged prompt's hook through, as it does the checkout's.

## At the install of session-kit 0.39.0

### main, A84 and A85: the ids in the message, and the pre-send check

A tagged message reaches the model with `Do-1:` where the person typed `Do:` (`A84`, the ids stand in the owner's message), and a message that starts with `??` or holds four bullets or more is read by Haiku first and held on the band when it finds something (`A85`, a pre-send check by Haiku, held on the band). It reaches a session as 0.36.0 does. Only a real session proves whether the desktop draws the rewritten message or the typed one, how long the owner waits on Haiku, whether `$.prompt.fill` puts the held message back in the desktop's box, and whether `session-intent` is on the PATH the engine runs it with.

## At the install of session-kit 0.39.1

### main: a press of Send as is passes its own text alone

Seen in this session's trial on 2026-10-29: a `??` message was held, the person sent the refilled text, and their next `??` message went through unchecked, since the pass Send as is set waited for a message the check's matcher would show it. The pass now holds the exact text the press sent or prepared, and the next message the hook sees spends it. The same trial showed the desktop drawing the text the person typed, with the `??` still in it, while the model read the text the hook wrote: the ids of `A84` (the ids stand in the owner's message) reach the model and never the person's bubble. It reaches a session as 0.36.0 does.

### Seen in the owner's trials on 2026-10-29, on the desktop

On 0.38.0 to 0.39.1 in this repository's session, five things were seen. A tagged message reached the model with its ids and the closing-line forms (`A83`). The reply's closing lines closed their items, so the turn's `answer` holds the text after the desktop's wrap-up. A reply left without `Do-3`'s line drew the kit's single prompt naming it. A `??` message with a bare id was held, and the Held row drew on the desktop with its finding, Send as is and Use the rewrite (`A85`). A `??` message asking the checker to reject it was let through, Haiku saying it found nothing. Not seen: the No line row itself (the owner did not say), pasted text in a tagged message, and the work instance.

## At the install of session-kit 0.40.0

### main: the band is a ledger, and the context row joins it at its firmer tier

`A86` (the band is a ledger, and the context row joins it at its higher tier). Every row draws a label in a fixed column, its text, then its buttons and its ✕ at the right, and only the leading row has a coloured label and a filled button. The context row draws from 300k by default, and below that only the status line shows the figure. To see on the desktop: whether the label column's width of 8 lines the rows up there as it does in the terminal, and how the plain labels read beside the coloured one. It reaches a session as 0.36.0 does.

## At the install of session-kit 0.40.1

### main: the band's spacing and alignment on the desktop

Seen by the owner on 2026-10-29 on 0.40.0's Held row: a wide gap after the label, the buttons centred on the first line with the finding hanging below, more space under the row than above it, and a smaller inset on the left than on the right. The label column is now as wide as the longest label shown, the buttons centre against all the row's lines, the gap under the kit's rows goes when nothing follows them, and the rows are inset by one on the left. To see on the desktop: whether the four are gone. It reaches a session as 0.36.0 does.

Seen by the owner on 2026-10-29 on the desktop, on the Held row alone: "It looks better". Not yet seen: a band of two rows or more, and the terminal.

## At the install of session-kit 0.40.2

### main: the pre-send check keeps what the person has in the box

`C3` (a hook that writes to the owner's input loses none of it), by the owner's word on 2026-10-29: the check replaced the box when it put a held message back, on Use the rewrite and on Send as is, losing messages the owner had prepared there. The held message now goes back above the box's text, the rewrite takes its place alone, and Send as is sends the message as it was held and takes only it out. An edit made to the held message in the box is sent by sending the box, since Send as is sends the held text. To see on the desktop: a hold with a prepared message in the box, then each button. It reaches a session as 0.36.0 does.

Seen by the owner on 2026-10-29 on the desktop: "It worked".

## At the install of session-kit 0.41.0

### main: the kit's pane shown and hidden by a chip

`A87` (the kit's pane is shown and hidden by a chip, and kept across sessions), by the owner's word on 2026-10-29. A `kit` chip beside the footer's mode labels shows and hides the pane, as `/kit` now does, and the next session starts with the pane as the last press left it. To see on the desktop: the chip at the right of the prompt's footer, a press each way, then a new session after leaving it open. If the desktop draws no chip there, the chip moves to the hint line. It reaches a session as 0.36.0 does.

## At the install of session-kit 0.42.0

### main: the kit's pane is the session's dashboard

`A89` (the kit's pane is the session's dashboard), by the owner's word on 2026-10-29: six sections (Items, Session, Next, Context, Usage, Chain), each left out when empty, with SVG gauges on the desktop. To see on the desktop: the pane opened from the `kit` chip, in a session with commits, uncommitted files and a handoff. It reaches a session as 0.36.0 does.

## At the install of session-kit 0.42.1

### main: the pane's sections are cards

`A89` (the kit's pane is the session's dashboard), by the owner's look at 0.42.0 on the desktop: each section a bordered card with its title and summing figure on the first line, the relevant text in full weight and its context dim, long lines truncated at the card's edge. To see on the desktop: the borders, the alignment of the titles with their figures, and the truncation. It reaches a session as 0.36.0 does.

## On each machine whose ~/.claude/CLAUDE.md links to the kit

### main, A80: the global rules imported into the user's file

`~/.claude/CLAUDE.md` becomes the machine's own file importing `global/CLAUDE.md` (`A80`, the global rules imported into the user's own CLAUDE.md). On each machine installed by the old link, run `global/install.sh` from the kit's working copy once: it replaces the link with a file holding the `@` line. This machine was converted on 2026-10-29. The check: a session started after it names `global/CLAUDE.md` among its loaded memory files (`/memory` in a terminal session).
