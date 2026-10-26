# Review: replay-theater

<!-- session-codeintel review -->
## What the program read

Written by `session-codeintel review` on 2026-10-26 with Claude Code 2.1.308, from the plugin at `~/devel/galileo/misc/mod-clones/claude-code-playground/claude-code/mods/replay-theater`. It ran the engine's validator and `plugin details`, read the plugin's files and git, and ran none of the plugin's code. Nothing here is a verdict: the hooks and the calls below are where the reading starts. The next run replaces this section and nothing around it.

| | |
| --- | --- |
| Plugin | `replay-theater` 0.1.0 |
| Commit | `569c5283d9a0a7ee7938df85bb32e4f48cbb8c86`, committed 2026-10-01 |
| Origin | `https://github.com/anthropics/claude-code-playground.git` |
| Working tree | clean |
| Engine | Claude Code 2.1.308 |
| Validator | passed, 0 errors, 0 warnings |
| Reach | L1, reads: reads files, draws. |
| Install | 422.7 KiB in 9 files, the plugin's folder, which an install copies |
| Marketplace | 824.2 KiB in 50 files, the repository, which adding it as a marketplace clones |

### What the validator found

- Nothing: no error and no warning.

### Calls on `$`, by reach

| Member | Through | Level |
| --- | --- | --- |
| `$.fs.exists` | stepsFor | L1, reads files |
| `$.fs.read` | stepsFor | L1, reads files |
| `$.ui.close` | replayView | L0, draws |
| `$.ui.invalidate` | the hook itself | L0, draws |
| `$.ui.open` | openReplay | L0, draws |
| `$.ui.resolve` | the hook itself | L0, draws |
| `$.clock.sleep` | openReplay | L0 |
| `$.command.register` | the hook itself | L0 |
| `$.session.cwd` | stepsFor | L0 |

### Hooks

| Event | Matcher | Gating | Hot | What to read |
| --- | --- | --- | --- | --- |
| `command.run` | `command=replay` | no |  | the slash commands it matches |
| `session.start` | none | no |  |  |
| `tool.call` | none | without .catch | hot | the tool calls it matches: read whether it approves, refuses or rewrites one |
| `turn.complete` | none | no |  |  |
| `turn.start` | none | no |  |  |
| `ui.close` | none | without .catch |  |  |
| `ui.render` | `component=AbovePrompt` | no | hot | what the surfaces draw: read whether it passes on what it does not draw |
| `ui.render` | `component=Pane` | no | hot | what the surfaces draw: read whether it passes on what it does not draw |

### Environment and state

- Environment read: nothing
- Environment written: nothing
- Telemetry hooked for: nothing
- Declares on `$`: nothing
- State: 0 keys written, 0 read, 0 declared
- `./replay-theater.mjs answers its own command`: `command.run{command=replay}`

### `claude plugin details`

```text
replay-theater 0.1.0
  Description: Replay Theater: step through the file edits Claude made in the last turn, one diff at a time.
  Source: replay-theater@inline

Component inventory
  Skills (0)
  Agents (0)
  Hooks (0)
  MCP servers (0)
  LSP servers (0)

Projected token cost
  Always-on:   ~0 tok   added to every session
```

### Control characters in source strings

Each line of the plugin's TypeScript and JavaScript whose strings hold a control character other than tab and newline, comments and regular expressions left out. A string built at run time (`String.fromCharCode(27)`) is not seen. The plugin hooks `ui.render`, where such a string can rewrite what a terminal draws.

None.

### Symbolic links

None.
<!-- end of session-codeintel review -->

| | |
| --- | --- |
| Upstream | https://github.com/anthropics/claude-code-playground, folder `claude-code/mods/replay-theater/` |
| Reviewed at | `569c5283d9a0a7ee7938df85bb32e4f48cbb8c86` (2026-10-01, the merge of PR #1). The mod's files came in with `e9ab132` (2026-09-30), and no commit has touched them since. Read from the clone at `~/devel/galileo/misc/mod-clones/claude-code-playground/`, which no session has loaded. |
| Served by | marketplace `claude-code-playground-mods` at `claude-code/mods/.claude-plugin/marketplace.json`, entry `{"name": "replay-theater", "source": "./replay-theater"}`. The repository root holds no marketplace file, so the README installs it by adding the folder of a local clone (`README.md:93-94`). |
| Version | `"version": "0.1.0"` in `plugin.json`. A folder marketplace with a relative entry is read in place, so the version gates nothing there: a `git pull` in the clone is an update (`docs/claude-code-mods-research.md:66`). |
| Reviewed on | 2026-10-25, Claude Code 2.1.308 (`claude plugin validate`, `plugin details`), API types and `reference.md` from the 2.1.308 bundle |
| Not run | `claude plugin test` and `tsc`, because both execute or build from the clone before this review existed (`A1`, review from a clone). The mod ships no tests to run. |

References: `mjs:N` is a line of `hooks/replay-theater.mjs`, `README.md:N` the mod's README unless named as the root's, `d.ts:N` a line of `plugin-authoring/types/claude-code.d.ts` in the 2.1.308 bundle, and `ref:N` a line of its `reference.md`.

## What it does

During a main-loop turn it records each Edit, Write and MultiEdit call as one or more steps: the file, the tool and a line diff (`mjs:78-102`, `196-204`). For Edit the diff is `old_string` against `new_string`. For Write it reads the file from disk first and diffs the old text against `content`. When a main-loop turn that made edits completes, its steps replace the previous replay (`mjs:212-221`), and a line appears above the prompt, `▶ Replay: 5 edits (press r)`, with a Replay button (`mjs:224-235`). `/replay` or the button opens a pane that shows one step at a time: the file, the tool, the added and removed counts, up to 12 diff rows, a strip of numbered cells, and Prev, Next and Close (`mjs:127-180`). Where no pane can be placed it draws the same view in the band (`mjs:120`, `225`).

It calls no model, runs no process, opens no connection and writes nothing. The README offers it as an example of a mod that records tool calls without changing them (`README.md:3`).

## Inventory

| Path | Lines | Role |
| --- | --- | --- |
| `.claude-plugin/plugin.json` | 8 | Name, version 0.1.0, author "Claude Code DevRel". No `dependencies`, no `userConfig`, no `license` field: the repository's Apache-2.0 `LICENSE` covers it. |
| `hooks/hooks.json` | 5 | `{"modules": ["./replay-theater.mjs"]}` only. No settings hooks. |
| `hooks/replay-theater.mjs` | 249 | The mod. Read in full. |
| `README.md` | 135 | Its claims are checked against the code below. |
| `.gitignore` | 2 | Ignores `.claude-plugin/types/`, where the engine lays the API types. |
| `screenshots/` | | Four PNGs, 408 kB, each with a valid PNG header (`file`). The mod never loads them. |

`claude --plugin-dir … plugin details replay-theater`: no skills, agents, settings hooks, MCP or LSP servers. Always-on context cost about 0 tokens. The same marketplace lists `token-weather` and `blast-radius`. Installing one entry installs nothing else.

### The copy in hamzafer/claude-code-mods

`~/devel/galileo/misc/mod-clones/hamzafer-claude-code-mods/mods/replay-theater/`, a shallow clone at `fd249d5e8dfd7f1094d741e42e0b1cca5f75311a` (2026-10-24), is a rewrite that shares no file with the Anthropic copy. The Anthropic copy is the upstream. It is three weeks older, and the rewrite keeps its name, its pane id and title, its `p` and `n` hotkeys, and the shape of its LCS diff with the same tie-break (`register.tsx:146-168` against `mjs:39-52`). The rewrite names no origin and carries its author's MIT license. A shallow clone has no history to show when it first appeared. This review covers the Anthropic copy.

| | Anthropic `0.1.0` | hamzafer `0.1.3` |
| --- | --- | --- |
| Form | One `.mjs`, no tests | `register.tsx`, a `types/index.d.ts` contract, three engine tests |
| When an edit is recorded | Before `next(e)`, so a denied or failed edit shows (`mjs:196-204`) | After `next(e)`, skipping `deny` and `isError` (`register.tsx:42-57`) |
| Where the hint shows | The band above the prompt, drawn without `next` (`mjs:224-235`) | A toast on the first editing turn, then the status line (`register.tsx:67-73`). No band. |
| State | Module variables (`mjs:16`) | `$.state` atoms, kept across a hot reload (`register.tsx:11-12`) |
| Pane matcher | Every `Pane`, filtered inside (`mjs:238-239`) | `{ component: 'Pane', requestId }` (`register.tsx:82`) |
| Close | `c`, a plain button (`mjs:176`) | `q`, `role="dismiss"` (`register.tsx:115`) |
| Diff | One line of context around each change, 12 rows shown (`mjs:58-69`, `136`) | Every line, and no diff drawn past 800 lines in all (`register.tsx:141-143`) |
| Subagent turns | `turn.start` skips them (`mjs:207`) | `turn.start` clears the pending edits on every turn, a subagent's too (`register.tsx:32-33`), so a subagent that starts mid-turn drops the main turn's edits so far |

Its `token-weather` and `blast-radius` are rewrites too (`register.tsx` with a shared `bands.ts` and tests) and share no file with the Anthropic copies.

## Checklist: malicious behaviour

| Item | Finding |
| --- | --- |
| `plugin.json` | `version` present. No `dependencies`, no `userConfig`, so it receives no secrets. |
| Settings hooks | None (`hooks/hooks.json:1-5`, and `plugin details` lists Hooks (0)). |
| `tool.call` / `tool.check` | `tool.call`, one hook with no matcher (`mjs:196-204`). On every path it returns `next(e)` with the event as it came and the result as it came back. It never approves, denies, rewrites or answers a call. The recording sits in a `try` with an empty `catch` (`mjs:198-201`), and `stepsFor` catches its own `cwd` and read failures (`mjs:80`, `93-98`). The registration has no `.catch`. A throw outside the `try`, or a run past the 10-second budget (`d.ts:5277`), makes the engine skip the hook and run the hooks beneath and the tool in its place (`d.ts:4063-4067`, `4079`), so it fails open, which suits an observer. No `tool.check`. It cannot override the `session-kit` `PreToolUse` guard on any login type. |
| `$.fs` | Reads only. For a Write, `$.fs.exists` then `$.fs.read` on the `file_path` the model gave (`mjs:94-95`), awaited before `next(e)` (`mjs:199`, `203`), so before the permission prompt and before the write (`d.ts:4072-4073`). The path is wherever the model names, inside the project or outside it, and the read runs with the user's privileges, outside the sandbox and outside `Read` permission rules. A Write the person then denies has still had its target read into the mod's memory. The text stays in module memory and is drawn only in the mod's own pane when the person opens it. No call in the module sends it anywhere. One read is capped at 4 MiB (`d.ts:3317`). |
| `prompt.compose`, `session.append`, `prompt.submit` | None. It never changes the system prompt, the stored transcript or a prompt. |
| Other gating hooks | `ui.close` (`mjs:244-248`), without `.catch`: it clears a flag, asks for a redraw and always calls `next(e)`, so it never keeps a pane open. `command.run` answers its own `/replay` (`mjs:190-193`), which `validate` lists as no gate. |
| `$.process`, network, `$.settings`, `$.model`, env | None. `validate` lists `$.clock.sleep`, `$.command.register`, `$.fs.exists`, `$.fs.read`, `$.session.cwd` and `$.ui.*` alone. |
| Telemetry hooks | None. |
| `$.store`, `$.state` | None. Module variables only (`mjs:16`), lost at a restart or a reload. |
| Timers | One `$.clock.sleep(200)` per pane opening (`mjs:116`). No `every` or `after`. |
| MCP, monitors, `bin/`, LSP | None. |
| `package.json`, lockfile | None. No dependencies (`README.md:123-127`). |
| Skills, agents, commands | One mod command, `/replay` (`mjs:186`), answered in-process with one line (`mjs:192`). That line is a row the model also reads (`ref:169`): a few words and a count. No injected instructions, no `allowedTools`. |
| UI | The band above the prompt and one pane. While it holds a replay, the band hook draws its own tree without calling `next(e)` (`mjs:226-235`), which hides whatever another plugin or the engine would draw there. Weighed under defects and in the overlap. |
| Update path | A folder marketplace in a local clone, read in place, so any `git pull` in that clone changes what runs (`docs/claude-code-mods-research.md:66`). Upstream is exported by hand from a private repository (root `README.md:56`) and takes no outside contributions (root `README.md:3`, `CONTRIBUTING.md:3`). |

Nothing malicious. The README says the mod only watches and never blocks, changes or delays an edit (`README.md:15`). It never blocks or changes one. It does delay each edit by a `cwd` call, and a Write by an exists check, a read and a diff as well, all awaited before `next(e)` (`mjs:78-102`, `199`): milliseconds.

## Checklist: inefficiency and defects

| Item | Finding | Weight |
| --- | --- | --- |
| Denied and failed edits shown as made | A step is recorded when the call arrives, before `next(e)` runs the permission prompt and the tool (`mjs:197-203`). An edit the person denies, one a `PreToolUse` hook blocks, and one that fails because `old_string` does not match all show in the replay as changes. The README discloses it (`README.md:116`). Recording after `next(e)` and skipping a result that carries `deny` or `isError` fixes it, as `session-kit`'s `test_log.ts:45-48` and the hamzafer rewrite (`register.tsx:43-46`) do. | Defect |
| The band hides every other band | From the first editing turn to the end of the session, except while its pane is open in a frame of its own, the band hook returns its own tree without `next(e)` (`mjs:224-235`). `state.replay` holds the last editing turn's steps, and nothing empties it (`mjs:215`). Whatever is seated beneath it in the band stays hidden all that time, `session-kit`'s three bands included (see the overlap). The README says only one band shows (`README.md:121`). The types let a hook wrap what `next(e)` drew (`d.ts:4101-4102`). | Defect, against `session-kit` |
| A survey is drawn over | `AbovePrompt` carries `hasSurvey`, and "a hook yields to it" (`d.ts:10798`). The hook never reads it (`mjs:224-226`). | Defect, minor |
| The replay and the tree differ | The replay holds what the model asked for. Bash edits (`sed -i`, a script, `git checkout`), NotebookEdit and a formatter's rewrite after the edit are missing. `session-kit` runs `format.py` after every Edit and Write (`plugins/session-kit/hooks/hooks.json:17-23`), so a formatted file differs from its step. An Edit with `replace_all` shows one replacement and a note, whatever the count (`mjs:83`). The README discloses that an Edit's diff is its strings alone (`README.md:114`). | Limit |
| Subagents | `tool.call` carries `agentId` in a subagent (`d.ts:13499`). The hook ignores it, so a subagent's edits join the running main turn with nothing marking them, as `README.md:118` discloses. A background agent's edits made between two main turns go to `pending` and are wiped at the next main `turn.start` (`mjs:207`), so they never show. | Defect, minor |
| A `/clear` keeps the replay | No `session.end` hook. After a clear the band still offers the previous context's edits until the next editing turn completes (`mjs:214-215`). | Defect, minor |
| Sizes read from the wrong place | `e.maxRows` and `e.bodyColumns` (`mjs:129`, `134`) live under `e.props` (`d.ts:10816`, `10825` and `10871`, with `ref:153`). At the top level both are undefined, so every diff line is cut at 96 columns and the in-band diff is always 12 rows. In the pane, `wrap: "truncate-end"` hides the first. In the band fallback the tree can outgrow `maxRows` and scroll. | Defect, minor |
| A pane the engine drops | When a pane's drawing throws, the engine closes it with origin `unload` and its opener's hooks do not run (`d.ts:7566-7567`). `state.isOpen` then stays true, and the band hint stays hidden (`mjs:226`) until `/replay` opens the pane again. | Defect, minor |
| The narrow-terminal fallback | `isPlaced: false` means the pane is open and undrawn (`d.ts:15058`). The mod draws in the band instead, and its Close skips `$.ui.close` while in the band (`mjs:153`), so the pane stays open and draws later if the terminal widens. An open that answers the person's input is placed at any width (`d.ts:7582-7584`), so this path runs only where no surface places panes. Untested upstream (`README.md:120`). | Minor |
| A Write over a file above 4 MiB | `$.fs.read` rejects it (`d.ts:3317`), the `catch` takes the file as missing (`mjs:98`), and the step reads "new file" with every line added. | Minor |
| Memory | Steps per turn are uncapped (`mjs:200`), and each keeps its whole diff while the pane shows 12 rows of it. Above 400 lines the diff skips the context trim and holds every old and new line (`mjs:36-38`). A long turn of large Writes holds up to 4 MiB of old text per step, until the next editing turn replaces it. | Minor |
| Hot events | `tool.call` has no matcher: a set lookup per call, then for an edit a `cwd` call, for a Write an exists check and a read, and a diff of at most 400 by 400 cells, all before the tool runs (`mjs:36-43`, `197-200`). `ui.render` on `AbovePrompt` runs again on a change of props or an invalidate, at most ten times a second (`d.ts:2387`), and builds one row, or 12 diff rows and one cell per step while replaying in the band. The `Pane` hook has no `requestId` matcher (`mjs:238`), so it runs for every plugin's pane and its invalidates redraw them all (`d.ts:2384-2396`). `ui.close` invalidates on every pane that closes (`mjs:246`). No spawn, no transcript read. | Fine |
| Focus by timing | To hand the pane the keyboard, the mod hides the band and sleeps 200 ms before `$.ui.open` (`mjs:113-118`). A pane's `focus` is refused while the band holds the keys (`d.ts:7605-7609`), so on a slower redraw the pane opens without the keyboard and the person presses ctrl+x tab. | Minor |
| The step strip | One cell per step in one row (`mjs:147-148`). Past a few dozen steps it runs wider than the 58 columns the pane asks for when docked (`mjs:118`). | Cosmetic |
| Dead code | `state.turns` is counted and never read (`mjs:16`, `218`). `e.requestId` in `ui.close` (`mjs:245`) is no field of `PaneCloseInput` (`d.ts:7551-7560`). The MultiEdit branch (`mjs:85-89`) matches no tool in the desktop session that wrote this review, whose tools hold no MultiEdit, and the README calls that path untested (`README.md:119`). The header names 2.1.280 and `--plugin-dir` (`mjs:7`). | Trivial |
| Hot reload | Module variables are lost at a reload (`ref:154`), and the replay with them. Disclosed (`README.md:117`). | Minor |
| Keys | `r` on the band's button (`mjs:232`), `p`, `n` and `c` in the pane (`mjs:174-176`), Escape through `closeOnEscape` (`mjs:118`). A hotkey acts only while the band or the pane holds the keyboard (`d.ts:1118-1121`), so typing at the prompt presses none, and the band draws alone, so none collides with another plugin's band. While the pane is open, Escape at an idle, empty prompt also closes it (`d.ts:7617`). | Fine |
| Install size | 408 kB of screenshots, unused at runtime. | Minor |

Three things are not verified. The first is whether `/replay` collides with another plugin's command. A refused registration throws after `next(e)` at `mjs:186`, so the session would start with the command missing. The second is which of `replay-theater` and `session-kit` the engine seats first in the band. The third is how the desktop app draws the band fallback.

## Overlap with `session-kit`

| | replay-theater | `session-kit` |
| --- | --- | --- |
| Question | What did the model ask to change in the last turn? | Did the tests pass, and where is their output (`A11`, the test log)? How full is the context, and where is the chain (`context.tsx`)? |
| Record | Module memory, the last editing turn, lost at a restart, a reload or the next editing turn | A file per session, replaced each run (`test_log.ts:58-64`), and the transcripts on disk, read by `session-transcripts` (`A22`, tooling over the transcripts and the hooks' effect) |
| When a call is read | Before `next(e)` (`mjs:199-203`) | After `next(e)`, with a denied call skipped (`test_log.ts:45-48`, `context.tsx:391-394`) |
| Subagents | Joined to the main turn (`mjs:196-204`) | The chain's `turn.complete` skips them (`context.tsx:567-569`) |
| Band | Draws alone and draws over a survey (`mjs:224-235`) | Draws alone and yields to a survey (`context.tsx:446`) |
| A hook that fails | No `.catch`: skipped, the call goes on | `.catch(($, e, next) => next(e))` on every hook (`context.tsx:418`, `test_log.ts:70`) |

### Where they collide

Both draw the band above the prompt without calling `next(e)` whenever they have something to show (`mjs:226-235`, `context.tsx:446-480`). The engine draws whichever it seats first, and the other stays hidden. The order of user-installed mods is an open question (`docs/PLAN.md:88`).

- `replay-theater` first: from the first turn that edits a file to the end of the session, the pane's open time aside, the person sees none of `session-kit`'s bands. Hidden with them are the new task's offer and its "Handoff and clear" and "Keep going here" buttons (`A19`, one task per context), the chain's stage line (`A17`, the model signals a clear point, the mod runs the chain), every Dismiss button (`A43`, the bands are dismissable), and the context figure. The `new_task` result tells the model that the band offers the choice (`context.tsx:543-546`), so the person would wait on an offer that is never drawn.
- `session-kit` first: the replay hint is hidden whenever the figure is past its threshold, a chain runs or an offer stands.

`tool.call` holds no collision. Both pass the call on unchanged, and neither reads what the other sets.

The fix on either side is the same: draw one's own row with what `next(e)` drew under it, in one column (`d.ts:4101-4102`). `session-kit` gains from that in its own band whatever else is installed, since today any band mod seated beneath it is hidden the same way.

### The four questions

1. Grouping by turn, for the test log or the `measure` module. The test log (`A11`, the test log) keeps the last run whole, and a run is one Bash call, so grouping by turn adds nothing there. The `measure` module (`docs/session-tooling-design.md:62-66`) should take the turn boundary and leave the buffer behind. `turn.start` mints a `turnId` that every `turn.step` and the `turn.complete` of that turn carry, and `tool.call` and the turn events carry `agentId` inside a subagent (`d.ts:13499`, `14274-14298`). A line per event, written as it happens and keyed by `turnId` and `agentId`, lets the reader group by turn and by loop afterwards. A buffer reset at the main `turn.start` (`mjs:207`) holds memory, loses a background agent's work and dies with the process. Skipping subagent turns at `turn.complete` (`mjs:214`) is already `session-kit`'s practice (`context.tsx:567`).
2. The pane and its band hint as the model for a test-log pane. The shape fits, and `docs/claude-code-mods-research.md:107` already names the test-run log as a pane. After a failed run, one band line names the failure and carries a button. The button or a command opens a pane with `focus`, `closeOnEscape` and `rows`, drawn from the log file, so the file stays the record `O6` (a session's word is not the proof) asks for. It comes with changes: state in `$.state` (`ref:154`), the `Pane` matcher narrowed by `requestId`, Close marked `role="dismiss"` as `A43` (the bands are dismissable) has it, the band composed with `next(e)` and yielding to a survey, and no timed sleep, so the pane opens with `focus` from the command and without it from the button. The line belongs in the kit's one band hook (`context.tsx:437`). The engine refused a second unmatched `turn.complete` hook in one module (`docs/PLAN.md:51`). Whether it refuses a second `ui.render` hook on `AbovePrompt` is unverified.
3. Whether watching edits helps the owner review a turn. It helps in part. A step-by-step view of a turn's edits reads faster than the transcript. Its record is the session's own word, which `O6` (a session's word is not the proof) sets aside as proof: a denied or failed edit shows, a Bash edit and a formatter's rewrite are missing, and the record is gone at a restart. What a turn changed is in the tree. Under the global rules a session commits each finished unit, so the commits a turn made, from `HEAD` at its `turn.start` to `HEAD` at its `turn.complete`, with `git diff` for what is left uncommitted, are the record a program wrote. A pane over that range would be the faithful form. `session-transcripts` could also print a turn's edits after the fact from the `tool_use` inputs and their `toolUseResult` rows (`docs/session-tooling-design.md:11-12`), denials included, across restarts.
4. Collisions: the band, above. Nothing else.

### What could move into `session-kit`

Each is a proposal for the owner, and none is built.

1. `session-kit`'s band composed with `next(e)` in `context.tsx:437-481`, so a band mod seated beneath it still shows. It stands on its own, with or without this mod.
2. A test-log band line and pane, shaped as in question 2, drawn from the file `A11` (the test log) writes.
3. `turnId` and `agentId` on every line of the `measure` module (`A22`, tooling over the transcripts and the hooks' effect).
4. A view of what a turn changed, from git over the range in question 3, as a pane a command opens. It needs `$.process.run` for read-only git commands, which widens the kit's reach and wants an entry of its own.

### What could go upstream

Upstream takes no outside contributions and may close them unread (root `README.md:3`, `CONTRIBUTING.md:3`), and it asks people to build on an entry in their own repository (`CONTRIBUTING.md:5`). Should the owner want to file issues anyway, four fixes would go in them.

- Record after `next(e)`, and skip a deny or an error.
- Compose the band with `next(e)`, and yield to a survey.
- Read the sizes from `e.props`.
- Reset the replay on `session.end` with reason `clear`.

## Verdict: reject

The code is safe to read and holds nothing malicious. It runs no process, opens no connection, calls no model and writes nothing, and its `tool.call` hook passes every call on unchanged and fails open. The reasons to reject lie in what it does beside `session-kit` and in what its record is worth.

- Installed beside `session-kit`, it can hide the kit's bands for the rest of a session after the first editing turn, the new task's offer and the chain's Dismiss among them, by an order of mods nobody controls yet. That works against `A19` (one task per context) and `A43` (the bands are dismissable).
- Its record is the model's request, kept in memory. For a review of what a turn changed, the commits and the tree are the record (`O6`, a session's word is not the proof).
- The fixes it needs (record after `next(e)`, compose the band, reset at a clear, read `e.props`, mark subagents) touch most of its 249 lines, and upstream takes no pull requests. The hamzafer copy shows where that road ends: a rewrite.
- Its install route is a clone read in place, which changes under any `git pull` (`O2`, what runs changes when I choose). Installing it as is therefore means keeping a pinned clone, a fork in all but name.

Its worth to the kit is its patterns, and they need no install: the four items under "What could move into `session-kit`".

If the owner wants the replay itself, the fallback is a fork per `A2` (a fork is pinned in galileo-kit): a separate plugin with a relative-path entry and `"version": "0.1.0-galileo.1"`, without `screenshots/`. Changes for its first release, each for the owner to confirm:

1. Record after `next(e)` resolves, and skip a result with `deny` or `isError`.
2. Draw the band as its own row above what `next(e)` drew, and yield while `e.props.hasSurvey`.
3. Clear the replay on `session.end` with reason `clear`.
4. Read `e.props.bodyColumns` and `e.props.maxRows`.
5. Keep the replay in `$.state`, narrow the `Pane` matcher by `requestId`, and mark Close `role="dismiss"`.
6. Mark each step with its `agentId`, and stop dropping a background agent's edits at the next `turn.start`.
7. Drop the 200 ms sleep: open with `focus` from `/replay`, and without it from the button.
