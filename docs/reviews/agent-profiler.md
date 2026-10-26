# Review: agent-profiler

<!-- session-codeintel review -->
## What the program read

Written by `session-codeintel review` on 2026-10-26 with Claude Code 2.1.308, from the plugin at `~/devel/galileo/misc/mod-clones/my-claude-code-mods/agent-profiler`. It ran the engine's validator and `plugin details`, read the plugin's files and git, and ran none of the plugin's code. Nothing here is a verdict: the hooks and the calls below are where the reading starts. The next run replaces this section and nothing around it.

| | |
| --- | --- |
| Plugin | `agent-profiler` 0.1.7 |
| Commit | `93fa0f7e84e37705da049ef2727530ec01af3dd9`, committed 2026-10-24 |
| Origin | `https://github.com/YeonwooSung/my-claude-code-mods.git` |
| Working tree | clean |
| Engine | Claude Code 2.1.308 |
| Validator | passed, 0 errors, 0 warnings |
| Reach | L3, reaches the network: network, writes files, reads env vars, runs a timer, draws. |
| Install | 161.1 KiB in 33 files, the plugin's folder, which an install copies |
| Marketplace | 1.7 MiB in 342 files, the repository, which adding it as a marketplace clones |

### What the validator found

- Nothing: no error and no warning.

### Calls on `$`, by reach

| Member | Through | Level |
| --- | --- | --- |
| `$.http.fetch` | post | L3, network |
| `$.fs.write` | exportTrace | L2, writes files |
| `$.env.get` | outputDir | L1, reads env vars |
| `$.clock.every` | the hook itself | L0, runs a timer |
| `$.ui.invalidate` | paintNow | L0, draws |
| `$.ui.open` | the hook itself | L0, draws |
| `$.ui.resolve` | the hook itself | L0, draws |
| `$.ui.status` | paintNow | L0, draws |
| `$.ui.toast` | warn | L0, draws |
| `$.clock.after` | the hook itself | L0 |
| `$.clock.sleep` | post | L0 |
| `$.command.register` | the hook itself | L0 |
| `$.session.id` | the hook itself | L0 |

### Hooks

| Event | Matcher | Gating | Hot | What to read |
| --- | --- | --- | --- | --- |
| `classic.PostToolUse` | none | without .catch | hot | the settings hooks' event of that name |
| `classic.PostToolUseFailure` | none | without .catch | hot | the settings hooks' event of that name |
| `classic.StopFailure` | none | without .catch |  | the settings hooks' event of that name |
| `classic.SubagentStart` | none | without .catch |  | the settings hooks' event of that name |
| `classic.SubagentStop` | none | without .catch |  | the settings hooks' event of that name |
| `command.run` | `command=profile-export` | without .catch |  | the slash commands it matches |
| `command.run` | `command=profile-pane` | without .catch |  | the slash commands it matches |
| `command.run` | `command=profile` | without .catch |  | the slash commands it matches |
| `session.end` | none | no |  |  |
| `session.start` | none | no |  |  |
| `telemetry.log` | `to=collector` | without .catch |  | the telemetry records it matches |
| `tool.call` | none | with .catch | hot | the tool calls it matches: read whether it approves, refuses or rewrites one |
| `turn.complete` | none | no |  |  |
| `turn.start` | none | no |  |  |
| `turn.step` | none | no | hot | every model request: read whether it changes the model, the effort or the stream |
| `ui.render` | `component=Pane, requestId=agent-profiler` | no | hot | what the surfaces draw: read whether it passes on what it does not draw |

### Environment and state

- Environment read: `HOME`
- Environment written: nothing
- Telemetry hooked for: `collector`
- Declares on `$`: nothing
- State: 0 keys written, 0 read, 0 declared

### `claude plugin details`

```text
agent-profiler 0.1.7
  Description: Execution profiler for Claude Code: model wait vs tools vs subagents, live, with OTLP export
  Source: agent-profiler@inline

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

- `hooks/core/redact.ts:12`: `\b \r`
- `hooks/core/redact.ts:19`: `\b`

### Symbolic links

None.
<!-- end of session-codeintel review -->

| | |
| --- | --- |
| Upstream | https://github.com/YeonwooSung/my-claude-code-mods, folder `agent-profiler/`, Apache-2.0 by the repository's `LICENSE` (the folder has none of its own) |
| Reviewed at | `93fa0f7e84e37705da049ef2727530ec01af3dd9` (2026-10-24), cloned at `~/devel/galileo/misc/mod-clones/my-claude-code-mods/` |
| Served by | marketplace `my-claude-code-mods` (the repository's own `.claude-plugin/marketplace.json`), entry `{"name": "agent-profiler", "source": "./agent-profiler"}`, one of the 17 mods it lists |
| Version | `"version": "0.1.7"` in `plugin.json`, matched by `VERSION` at `hooks/register.tsx:10`, so installed copies change only on a bump |
| Reviewed on | 2026-10-25, Claude Code 2.1.308 (`claude plugin validate`, `plugin details`), API types from the 2.1.308 bundle |
| Not run | `claude plugin test`, `tsc`, `qa/permission_smoke.py` and the Jaeger `docker compose`, because each executes or builds from the clone, which `A1` (review from a clone) forbids before this review exists |

## What it does

agent-profiler records where a session's time goes. It keeps an in-memory timeline of turns (`turn.start` to `turn.complete`), model requests (`turn.step`, with the time to first chunk, the thinking stream and the output stream), tool calls (`tool.call` entry to return, split into execution and wait by the engine's `duration_ms`), and subagents (`classic.SubagentStart` to `SubagentStop`). A sweep over each main turn gives every moment to one category, model first, then a blocking subagent, then a tool, and names the remainder engine time (`hooks/core/analyze.ts:89-112`).

1. Live display. A status-line entry with the model and tool shares and the longest call in flight, repainted at most twice a second and every second while something runs, and a pane that `/profile-pane` opens.
2. Reports. `/profile` (or `/profile turn`) answers with a text report: the split, model and token figures, tool counts and the slowest calls, Bash time by category, files read more than once, subagents, and findings such as "Tests took 40% of agent time".
3. Export. After every turn it writes the records finished since the last batch as OTLP/JSON under `~/.claude/agent-profiler/<session id>/`, and POSTs each batch to `<otlpEndpoint>/v1/traces` when that option is set. `/profile-export` writes a full snapshot. Prompts, Bash command lines and search patterns stay out of the export unless `exportCommandText` is on. File paths are always in it.

It also reads the engine's `tool_decision` records from the collector telemetry stream, to estimate how much of a tool call's wait was an approval.

## Inventory

| Path | Lines | Role |
| --- | --- | --- |
| `.claude-plugin/plugin.json` | 26 | Name, version 0.1.7, three `userConfig` fields, none `sensitive`. No `dependencies`. |
| `.claude-plugin/icon.svg` | 7 | A rect and two paths. No script, link or external reference. |
| `hooks/hooks.json` | 1 | `{"modules": ["./register.tsx"]}` only. No settings hooks. |
| `hooks/register.tsx` | 363 | The adapter: every hook and every `$` call. Read in full. |
| `hooks/core/*.ts` | 1,517 in 12 files | Logic with no `$`: the `Profiler` state machine (`profiler.ts`, 407), the attribution and findings (`analyze.ts`, 343), OTLP encoding (`otlp.ts`, 221), Bash classification (`classify.ts`, 181), the report text (`report.ts`, 108), batching under the write cap (`export.ts`, 53), secret masking (`redact.ts`, 30), permission timing (`permission.ts`, 31), ids, formatting, a summary cache and the types. Read in full. Every import is relative, plus types from `claude-code`. |
| `tests/*.ts` | 1,151 in 13 files | Engine-kit tests and a fixtures file. They import only `claude-code/testing`, `claude-code` types and the mod's own files. File writes and env reads go to the kit's mocks (`on('fs.write', …)`, `mock.env`). No network or process call. |
| `qa/permission_smoke.py` | 198 | The maintainer's check, which the mod does not load. It copies the mod into a temporary folder, patches its default output path, and runs the `claude` binary it is given headless, with a placeholder API key against a refused loopback URL (`127.0.0.1:1`) and the telemetry exporters off. |
| `examples/jaeger/docker-compose.yml` | 8 | `jaegertracing/all-in-one:latest`, ports 16686 and 4318 published. Never loaded. |
| `README.md`, `tsconfig.json` | 223, 18 | Docs, and a tsc config that expects the engine's types under the git-ignored `.claude-plugin/types/`. |

An install copies the 240 KB `agent-profiler/` folder, tests and QA script included. Adding the marketplace clones all 3.5 MB of the repository with its 16 other mods and installs none of them.

`claude --plugin-dir … plugin details agent-profiler`: no skills, agents, settings hooks, MCP or LSP servers. Always-on context cost about 0 tokens.

## Checklist: malicious behaviour

| Item | Finding |
| --- | --- |
| `plugin.json` | `version` present. No `dependencies`. `userConfig`: `otlpEndpoint` (string, default `""`, which turns HTTP off), `outputDir` (string, default `""`, read as `~/.claude/agent-profiler`), `exportCommandText` (boolean, default `false`). None is `sensitive`, so it receives no secrets. |
| Settings hooks | None. |
| `tool.call` | One hook with no matcher, an observer (`register.tsx:272-288`). It calls `next(e)` once with the event as received and returns the answer unchanged (`:279-281`). A rejection beneath is recorded and thrown again (`:282-284`). Every bookkeeping step sits inside `safe()` (`:32-38`), so nothing before `next` can throw. Its `.catch` is `next(e)` (`:288`), which replays the call already settled and runs nothing twice (`reference.md:79`). It never answers `{ deny }`, `{ result }` or a rewritten input, so it cannot approve, refuse or change a call, and it cannot override the `session-kit` `PreToolUse` guard on any login type. |
| `tool.check` | None. An earlier revision observed it the same pass-through way, removed by `306fd21` on 2026-10-23. |
| `prompt.compose`, `session.append`, `prompt.submit` | None. It never changes the system prompt, the stored transcript or a prompt. |
| `turn.step` | An async generator (`register.tsx:252-270`). It calls `next(e)` with the event unchanged, so the model and effort stand, yields every chunk as received, and returns nothing, which lets the result beneath stand (`claude-code.d.ts:12937`). It reads each chunk's `kind`, and `usage` and `stopReason` from the `stop` chunk. It never reads the text, the thinking or the tool arguments. A throw mid-stream would leave the rest of the stream to the hooks beneath (`reference.md:31`). |
| Other gating hooks | `classic.PostToolUse`, `classic.PostToolUseFailure`, `classic.SubagentStart`, `classic.SubagentStop` and `classic.StopFailure` (`register.tsx:245-250, 297-317`) each record under `safe()` and `return next(e)` with the event as received. Modules sit above the user's settings hooks in those chains (`claude-code.d.ts:1280`), so `session-kit`'s settings hooks beneath see what they would have seen without the mod. None of the five has a `.catch`, and none can throw outside `safe()`. A skipped one loses only the mod's own record, so each fails open. The three `command.run` hooks (`:331-348`) answer only `profile`, `profile-pane` and `profile-export`, by matcher, with text. The validator lists them as gates, most likely because the names reach `$.command.register` through the `COMMANDS` array (`:12-16`) and it counts only names registered by a literal (`reference.md:66`). |
| `telemetry.*` | `telemetry.log` on `{ to: 'collector' }` (`register.tsx:290-295`). A synchronous hook that returns `next(e)` with the record as received, so it cannot alter or drop a record, and it never denies one. It sees every collector record the engine raises and keeps only `tool_decision` ones: the tool-use id, `accept` or `reject`, the source and the classifier verdict as fixed enums, and the timestamp, with every other attribute discarded (`core/permission.ts:7-16`). It logs nothing to telemetry itself. The README says the engine raises these records with every exporter off (`README.md:178`), which this review did not verify. |
| `$.fs` | Writes only, through `exportTrace` (`register.tsx:164`): `<outputDir>/<session id>/<load id>-<seq>.otlp.json` per batch and `<load id>-full-<n>.otlp.json` for `/profile-export`. No read, list or delete. The session id is the engine's. A relative `outputDir` resolves under the session's working directory (`claude-code.d.ts:3305-3306`), so a relative value would put trace files inside the project. |
| `$.process`, `$.model`, `$.settings`, `$.store`, `$.state` | None. All state is module variables. |
| Network | `$.http.fetch` once, in `post` (`register.tsx:103-121`): `POST <otlpEndpoint>/v1/traces` with `content-type: application/json` and the body the file holds, only when `otlpEndpoint` is set (`:174-186`). Off by default. No `auth` and no other header, and of the answer only `ok` and `status` are read. `http:` is accepted, so a remote collector over plain HTTP receives paths and timings in clear. Redirects follow the engine's policy. |
| What leaves memory | Always, in files and in POSTs: the session id, span timings, models, effort, token counts, stop reasons, tool names and call ids, file paths and Read ranges (`core/otlp.ts:188-189`), the Bash category, the permission enums and wait estimates, subagent ids and types. With `exportCommandText` alone: the first 120 characters of each prompt, Bash commands up to 512 characters, and Grep and Glob patterns (`core/otlp.ts:66, 105, 190-191`), each masked first. Never: model text, tool results, Bash descriptions. |
| Masking | `core/redact.ts:7-20` masks a value beside a keyword: `Authorization:` and `*-key`/`*-token`/`*-secret` headers, `Bearer`, `password:`-style JSON keys, `--password`, `--token`, `--api-key` and `--secret` flags, URL passwords, `-u user:pass`, `mysql -p`, and `NAME=value` where the name holds KEY, TOKEN, SECRET or PASSWORD. It masks before it truncates (`core/profiler.ts:22-24`). It misses any secret with no keyword beside it: a bare `sk-ant-…`, `ghp_…`, `AKIA…` or JWT, a flag outside its four (`--access-token xyz`, `--api_key xyz`), and free text in a prompt ("the password is hunter2"). The in-memory copy, the status line, the pane and `/profile` show the masked text whatever the export setting. |
| Env | Reads `HOME` to expand `~` in `outputDir` (`register.tsx:95`). Writes nothing. |
| `$.ui` | A status entry, a toast once per distinct failure message, and a pane of text rows opened only by `/profile-pane`. No band. |
| MCP, monitors, `bin/`, LSP | None. |
| `package.json`, lockfile | At the repository root, outside the plugin folder: devDependencies `expect` 30.2.0 and `typescript` 5.9.3, 48 locked packages, every one marked `dev`, for the maintainer's tests and `tsc`. The mod imports none of them and has no runtime dependency. |
| Skills, agents, commands | Three mod commands answered in-process with text. No injected instructions, no `allowedTools`. |
| Files never loaded | `qa/permission_smoke.py` writes a throwaway driver mod and runs whatever `--claude-bin` names, isolated from the user's settings. `examples/jaeger/docker-compose.yml` pins no image (`:latest`) and publishes 4318 and 16686 on every interface, so the README's Jaeger steps (`README.md:111-118`) open an unauthenticated collector and trace UI to the local network. |
| Update path | Third-party marketplace, so auto-update is off by default. The entry is a relative path inside a GitHub-hosted marketplace and follows the repository's default branch, and `"version"` gates it. The repository is busy: 176 commits, 32 of them to this mod since 2026-10-09, three on 2026-10-24. |

Nothing malicious. The mod observes every event it hooks and passes each on unchanged. The README's own account of its reach (`README.md:176-223`) matches the code.

## Checklist: inefficiency and defects

| Item | Finding | Weight |
| --- | --- | --- |
| Hot hooks | Up to three hooks per tool call: `tool.call` with no matcher, `classic.PostToolUse` (which hands the mod all of the payload, `tool_response` included, for its `duration_ms`), and the collector's `tool_decision`. One `turn.step` per model request, with a few map lookups per chunk (`core/profiler.ts:167-179`). Each is in-process and cheap on its own. | Fine |
| Ticker | `$.clock.every(1_000)` from `session.start` for the session's life (`register.tsx:215-217`): one host dispatch a second, idle or not, which repaints whenever a request, tool or agent is open. | Minor |
| Summary on every paint | A paint (at most two a second, plus the ticker) recomputes `summarize` over a fresh snapshot of every record in the session whenever anything changed or anything is live, since the cache keys on the profiler's version and, while live, a 500 ms bucket (`core/cache.ts:10`). The mod's own test bounds one summarize at 20,000 spans under 200 ms (`tests/perf.test.ts:36`). A module's environment is one JavaScript thread, and the same thread forwards every `turn.step` chunk and runs the `tool.call` hook, so in a long session a summarize can hold a chunk or a tool call for as long as it runs. The owner's longest archived session, 3,222 requests (`docs/measurements/sessions-2026-10-25-with-archive.md`), sits at about a third of the cap. | Cost that grows with the session |
| No retention | Nothing deletes a trace. A batch adds about 4 KB per model request with its tool call (estimated from the span shapes at `core/otlp.ts:135-211`), so a session of 3,222 requests leaves about 12 MiB, one file per turn, in a folder per session, kept forever. | Minor, grows |
| Batch POST | A per-turn POST has no deadline (`register.tsx:115`), so a collector that accepts and never answers keeps one request pending per turn, each holding its body. A failed POST is never sent again: the records were claimed before the write (`:147-149`) and are released only when the write fails (`:169`). The loop stops at the first failed part (`:182`), and only the first toast per distinct message shows (`:76-80`). The files keep every batch. | Minor (HTTP off by default) |
| Bash categories for this owner | The classifier strips a fixed list of wrappers (`core/classify.ts:68`) and matches each command segment from its start (`:120-150`). `session-watched -- uv run pytest`, the form `A37` (the watched run) prescribes for every long run, falls to `other`, and so does `"<desktop binary path>" plugin test`, the kit's engine tests, because the quoted path is blanked before matching. Test time and the "Tests took" finding never appear for this owner. `session-kit`'s `test_log.ts:19-21` matches a runner anywhere in the line and sees the first. | Defect here, fork-local |
| "exec [measured]" | A call with no `duration_ms` counts its whole wall time as execution (`core/permission.ts:24`), and the report sums every call's figure into the line it labels `[measured]` (`core/analyze.ts:209`, `core/report.ts:46`). | Minor, upstreamable |
| Memory | Records are capped at 20,000 requests and tool calls, evicted a whole finished turn at a time (`core/profiler.ts:88, 347-406`). The `exported` set of record keys (`register.tsx:27`) and the `toasted` set (`:28`) are never pruned, one short string per record. | Minor |
| Dropped turns | The report says dropped turns were "already exported" (`core/report.ts:26`) whether or not their batch was written. | Minor |
| `/profile` in context | A `command.run` answer's `text` is a row the model reads (`reference.md:169`), so each `/profile` puts a report of a few dozen lines into the transcript for the rest of the session. | Note |
| README | It names 0.1.6 as the verified version (`README.md:5`) while the manifest is 0.1.7, and says `turn.start` fires only for main-loop turns (`README.md:152`), where 2.1.308 raises it for subagent loops too (`claude-code.d.ts:4581-4588`). | Minor |

Three things this review could not determine without running the engine. Whether `PostToolUse` settings hooks run inside the `tool.call` chain, which puts their time in a call's wait, or after it, which puts it in engine time. Whether `$.http.fetch` carries an engine-side timeout. Whether the engine raises collector records only while a hook listens to them.

### Where the timing model misleads

The report labels its sources (`observed`, `measured`, `reported`, `inferred`, at `core/report.ts:75-76`), and its categories still carry more than their names say.

- "Model response wait" is the `turn.step` hook's own span, from entry before `next(e)` to the end of the stream (`register.tsx:252-270`). It holds every `turn.step` hook beneath the mod, the engine's request building, retries with their backoff, network, queueing, prefill and decoding. It also holds the time the reader of the stream above takes between chunks, since the generator waits at each `yield` (`:264`). The finding "Waiting for the model is 70% … tools are not the bottleneck" (`core/analyze.ts:322`) reads that sum as the model's speed.
- The sweep gives overlapping time to the higher category, model first (`core/analyze.ts:54, 101`). Where a tool runs while a response still streams, or a tool call runs beside a blocking subagent, the time counts as model or subagent time.
- "Engine/other" is the remainder of each turn's window. It holds compaction, context building and `session.append`, and also every hook that sits above the mod in the `tool.call` and `turn.step` chains, since those run outside its intervals. Where the mod lands in the plugin order moves time between "tools", "model" and "engine", and that order is the open question in `docs/PLAN.md:88`.
- A tool call's wait is its wall time minus `duration_ms`, which excludes the permission prompt and hook time (`claude-code.d.ts:8062, 8075`). The wait therefore holds the `PreToolUse` settings hooks (`session-kit`'s guard costs about 26 ms per Bash call, `docs/measurements/hook-times.md:51`), the `tool.call` hooks beneath the mod and the prompt. The "approval/check wait" runs from tool entry to the decision's timestamp (`core/permission.ts:28-29`), so it includes the guard's time ahead of the prompt.
- Token "in" sums input, cache reads and cache writes over every request (`core/analyze.ts:187`). It is the context resent with each request, summed, which reaches millions in a long session and says nothing of how full the context is.
- A subagent's `turn.start` is filed on the main stack (`register.tsx:233` passes no loop) until its first request moves it (`core/profiler.ts:147-154`). A subagent turn that makes no request stays a main turn and adds its window to agent time beside its parent's. In the rare gap before a background agent's first request, a main tool call is filed under the subagent's turn and drops out of the split.

## Overlap with session-kit's measure module

agent-profiler is the closest outside work to the `measure` module that `A22` (tooling over the sessions' transcripts and the hooks' effect) plans under `O17` (the system is observed, analysed and improved over time). They aim at different things. agent-profiler explains a session's wall time. `measure` is meant to record what the kit's own hooks did and cost, for the reader to join to the transcript (`docs/session-tooling-design.md:62-66`).

| | agent-profiler | `measure`, as designed | `session-transcripts`, built |
| --- | --- | --- | --- |
| Question | Where did this session's time go? | What did each of the kit's hooks do, and at what cost? | What do the stored sessions show? |
| Events | `turn.start`, `turn.step`, `turn.complete`, `tool.call`, `classic.PostToolUse(Failure)`, `classic.Subagent*`, `classic.StopFailure`, collector `tool_decision`, `session.end` | `turn.complete`, `tool.call`, `session.compact`, `session.measure`, and each kit hook around its `next` | The JSONL transcripts, after the fact |
| Record | OTLP/JSON batches per turn under `~/.claude/agent-profiler/`, and an optional POST | One JSON line per event under `<CLAUDE_PLUGIN_DATA>/measure/<session id>.jsonl` | Markdown tables under `docs/measurements/` |
| Computes | In the module, on every paint | In the reader | In the reader |
| Sees the kit's hooks | Only as unnamed wait or engine time | By name | The settings hooks' attachments, the Stop hooks' durations |

By the design's questions (`docs/session-tooling-design.md:29-43`):

- 7, each module's effect and cost: no. It times the chain beneath one hook as a single span and never knows which of the kit's hooks fired or what each added.
- 8, the hooks' time per call, live: in sum. A call's wait is the live total of every hook and the prompt around it, and a Bash call's wait set against an Edit's shows the guard's share. It cannot split one hook from another.
- 9, what a compaction or a clear is worth: in part. Its repeated-read count (`core/analyze.ts:232-246`) is the re-read signal, and it records no compaction boundary to count from. The transcript holds both the `Read` calls and `compact_boundary`, so the reader can answer this alone.
- 10, the sessions the reader cannot see: in kind. It writes each turn to disk as the turn ends, so a cleared or deleted transcript leaves its timing behind. It keeps no context figure and no cost.
- 1 to 6: no. Its per-request usage repeats what the transcript's `assistant` records already hold for question 3.

What it measures that no question asks: time to first chunk, stream rates, tool execution against wait, parallelism, subagent wall time.

### The event model as a base for measure

The timeline half is the right base. Turn windows from `turn.start` to `turn.complete`, a tool's wall time around `next`, its execution from `classic.PostToolUse`'s `duration_ms`, the approval split from collector `tool_decision` records, and subagent start and stop are the events `measure` needs for question 8, and agent-profiler shows that they compose. Two parts are missing for `measure`'s own questions: `session.measure` and `session.compact`, for the context and cost figures, and a wrapper on each concern's `on` in `kit.tsx` that times the kit's hooks from inside, which no outer hook can do.

The chunk stream is optional. It buys the time to first chunk, which no question asks for, at the price of code on every chunk. A `turn.step` hook that times `yield* next(e)` and reads the returned `usage` gives a request's duration and cost with no work per chunk.

agent-profiler reads `Date.now()` inside the module, which costs nothing on a hot path. `await $.clock.now()`, as `test_log.ts:59` reads the time, is a host dispatch per read. Its core takes the time as a parameter (`t` on every `Profiler` method), so its tests pass the time in and need no clock.

### OTLP or a local JSONL

A local JSONL line per event is enough for `measure`. The reader is standard-library Python that joins by session id and writes tables, and the design rules out telemetry to anywhere and a dashboard (`docs/session-tooling-design.md:68-72`). OTLP's attribute encoding wraps every value in `{"key": …, "value": {"stringValue": …}}` and adds a child span per phase: by hand-built examples, a Read call takes about 1.7 KB as OTLP and about 300 bytes as one flat line holding the same facts. Its one gain is a waterfall in Jaeger or Tempo. If that view is ever wanted, a reader command can convert the JSONL offline, with `core/otlp.ts` and its GenAI span names as the model.

### What its core split teaches

- `hooks/core/` is pure TypeScript with no `$` and no clock: events and times go in as arguments, and summaries come out. Only `register.tsx` touches the engine. That is the shape `global/CODE.md` asks for ("Code is pure by default, and an effect names itself"), and it lets 11 of its 12 test files run on plain data.
- Every bookkeeping step goes through `safe()` (`register.tsx:32-38`), so recording never fails a session: `C1` (the kit is never the reason a session fails), held in one place.
- Work leaves the hook's path. A paint is queued behind the event with `$.clock.after(0)`, one at a time and throttled (`register.tsx:55-68`), and the export runs the same way after `turn.complete` (`:241`).
- Its weak points teach as much. Recomputing the summary from every record on each paint costs in proportion to the session, where `measure` appends a line and leaves the arithmetic to the reader. Module variables vanish on a reload (`README.md:150`), where the reference keeps drawn state in `$.state`.

### If both were installed

- Both hook `tool.call` with no matcher (`context.tsx:390` in `session-kit`). Neither changes what the other sees. The plugin order decides whether `session-kit`'s per-call work (the context read, the test log write, the document cap, the suppression and nudge checks) falls inside agent-profiler's tool interval or in its engine remainder.
- The chain of `A17` (the model signals a clear point, the mod runs the chain) and the resend of `A19` (one task per context: the rule now, the signal with the port) start turns through `$.prompt.submit` and `$.session.compact`. agent-profiler records them as turns of the session, which they are.
- `session-kit`'s own tools (`clear_point`, `new_task`) appear among its tool calls.
- The two test detectors disagree: `test_log.ts` counts a `session-watched` run as a test, and agent-profiler files it under `other`.
- UI, commands and files stay apart: bands against a status entry and a pane, `/profile*` against the kit's skills, `~/.claude/agent-profiler/` against the plugin data directory and `TMPDIR`.
- In the work instance `cc-plugin-sec-default` sits ahead of the user's plugins and has skipped `session-kit`'s hooks (`docs/PLAN.md:88`). It would skip agent-profiler's the same way and leave holes in its timeline.

## What could move into session-kit

1. The timeline for `measure`, as JSONL lines: a turn's start and end, a tool's entry and return with its `tool_use_id`, `duration_ms` from `classic.PostToolUse` and `PostToolUseFailure`, the `tool_decision` fields `core/permission.ts` keeps, and subagent start and stop. The module writes lines. The sweep (`core/analyze.ts:89-112`) and the findings belong in the reader, in Python.
2. The pure core apart from the adapter, with time passed in, for `measure` and for the reader's arithmetic.
3. `safe()` and the `$.clock.after(0)` deferral as the module's rules for every write.
4. The repeated-read count as a `session-transcripts` query for question 9, counted from each `compact_boundary`, with no module needed.

Left out: the OTLP export and its POST, the status entry, the pane, the one-second ticker, the chunk stream, and the Bash classifier, which `test_log.ts` already covers for this owner.

## What could go upstream

- A configurable wrapper list for the classifier, or stripping any `<word> --` prefix, so `session-watched -- pytest` counts as a test run.
- A deadline on per-turn POSTs, and a failed batch's body sent again with the next one.
- A retention setting: trace folders older than N days removed at `session.start`.
- The `[measured]` execution figure summed over the measured calls alone.
- The `exported` set pruned with each eviction.
- The README's version line and its `turn.start` statement.
- The Jaeger example pinned to a version and bound to `127.0.0.1`.

## Verdict: reject

The code is safe. It observes every event it hooks and passes each on unchanged, it cannot approve or refuse a tool call, its one network call is off by default, and its README's account of its reach is accurate. The reasons to leave it uninstalled are fit and cost.

- It answers few of the questions `A22` (tooling over the sessions' transcripts and the hooks' effect) asks, and misses the question `measure` exists for: the kit's own hooks, by name.
- Installed at user scope it runs in every session: up to three hooks per tool call, one per model request with code on every chunk, a timer every second, a whole-session recompute per paint, and trace files nothing deletes. That spends against `O13` (one-off tasks are not slowed) and `G4` (optimize time and reduce costs) for a report the owner would read rarely.
- Its test detection is blind for this owner, whose runs all go through `session-watched`.
- Its upstream is a busy third-party repository of 17 mods, so keeping it means reviewing diffs every few days.

The parts worth having are the event model, the core split and the deferral pattern, and `measure` takes them as the section above lists. Lifting code from it needs the Apache-2.0 notice. Lifting the design needs nothing.

If the owner wants a figure for question 8 before `measure` exists, "install as is" for one session is a sound fallback: add the marketplace (auto-update stays off), install `agent-profiler` at project scope in one project, leave `otlpEndpoint` empty, read `/profile` at the end, then uninstall it and delete `~/.claude/agent-profiler/`. A Bash call's wait set against an Edit's then shows what the guard and the formatter cost, live.

If the owner would rather keep the live pane, a fork follows `A2` (a fork is pinned in galileo-kit): a separate plugin at `"version": "0.1.7-galileo.1"`, without `qa/` and `examples/`. Changes for its first release, each for the owner to confirm:

1. The classifier strips `session-watched --` and reads a quoted binary path's last component, so the kit's test runs count as tests.
2. Retention: trace folders older than a set number of days removed at `session.start`.
3. The POST removed, with `otlpEndpoint` dropped from `userConfig`, so nothing leaves the machine.
4. `exportCommandText` removed, so prompts and commands never leave memory.
