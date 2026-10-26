# What a restart is made of, and what can be cut (2026-10-26)

The question, from `kit-impact-on-three-projects.md`: after a compaction the context is 87k to 112k tokens against 44k to 47k in the June sessions. Where does it go, which part is the kit's, and what does cutting each part save. Read from the `api-request`, `api-request-blob` and `api-request-shape` records the engine (2.1.308) writes into the transcripts, for the first request after each of 53 compactions in mat-lib (13), lane1 (38) and demo-mat-porting (2). Reproduce with `python3 -I kit-impact-scripts/restart_sources.py <project dir>=<kit_scan.py output>`.

## The answer

A restart is two things: a prefix the engine sends with every request (the tool schemas and the system prompt, 55.5k to 55.8k tokens), and the messages the compaction leaves (32k to 56k). The kit's text is about a tenth of that, so the growth over June is not the kit's. The prefix alone is larger than an entire June restart.

| Tokens, median per restart | mat-lib | lane1 | Who controls it |
| --- | --- | --- | --- |
| Context after the compaction | 87,585 | 111,088 | |
| Artifact tool schema | 12,336 | 11,749 | the app, hidden by a deny rule |
| Tools the desktop app adds (Browser 7.6k, `ccd_turn` 2.7k, iOS simulator 2.2k, visualize 1.4k, `ccd_session` 1.2k, Docs 0.6k, terminal 0.4k) | 16,125 | 15,357 | the app, deny rules |
| Tools the engine ships (20 to 21, Bash, Read, Agent, Workflow, Monitor...) | 15,626 | 16,808 | the engine |
| System prompt | 11,034 | 11,217 | the engine |
| The kit: global rules, `CLAUDE.local.md`, compact command echo, continue prompt | 7,992 | 9,520 | the kit |
| The kit: its two tools, the handoff skill's body, its two skill-list lines | 1,773 | 1,748 | the kit |
| The compaction: summary, files the engine restores | 10,146 | 12,227 | engine, kit's compact instructions |
| Skill list, deferred tool list, agent list, MCP instructions, environment, git status | 11,182 | 12,029 | the owner's plugins and the engine |
| Project `CLAUDE.md` | 1,121 | 5,464 | the project |
| Skills the project invoked, re-attached whole | 261 | 15,273 | the project |

The kit is 9.8k tokens (11%) in mat-lib and 11.3k (10%) in lane1. The biggest single parts are the Artifact schema, the app's tools and, in lane1, the project's own skills.

## What a token costs

A token of prefix is read at every request, and the restart rewrites the messages to the cache. In the cost units of the first analysis (input 1, cache read 0.1, write 1.25):

- 1k tokens of prefix is 0.34% to 0.40% of a session's modeled cost, and 1k tokens of restart messages is 0.22% to 0.35%. The prefix is 19% to 22% of every request's cost.
- The cost of what the kit adds to the messages, about 10k tokens, is 3% of the session. The kit's hook text was 0.3% to 0.7% in the first analysis, so the loaded text is the larger part of the kit's footprint.

## What was found

1. The Artifact tool is 12.3k tokens in every request and the work never calls it. Its schema is 36k characters, with a paragraph of the system prompt beside it, the largest single item of the prefix. A deny rule removes it: with `{"permissions":{"deny":["Artifact"]}}` the request's tool schemas fell from 69,341 to 31,668 characters and its system prompt from 11,177 to 10,208 in four runs against four without (2.1.308, a one-line prompt to Haiku, read back from the request shape). That is about 13k tokens, 4.3% to 4.6% of a session's cost. The rules already forbid publishing an artifact and the guard refuses the call, so a deny rule holds the same rule at a cost of nothing.
2. The desktop app's other tools were called in two projects only. Over every live transcript on this machine the Browser tools were called 326 times in tagents-verifier and 198 in misc/git-organization, and never in lane1, demo-mat-porting or mat-lib. The iOS simulator tool was never called anywhere, `ccd_turn` (the plan and wrap-up tools) 322 times in the three projects, and visualize, `ccd_session`, Workflow and ScheduleWakeup not at all. The Browser tools are 7.6k tokens and a deny rule on them takes the model's means of opening the app's browser away in every session it covers, so it belongs in a project that never drives one and not in the user settings. A deny rule on an MCP server's name hid a connector's tools in my test (11 tools to 0), and I did not test it on the app's own servers. The engine can also hold an MCP server's tools back behind its tool search (`alwaysLoad` on the server's config, `ENABLE_TOOL_SEARCH`), which would keep them callable for a ToolSearch call. The app's servers are loaded in full, so it looks like the app sets `alwaysLoad`. Not tested.
3. lane1 carries 15.3k tokens of its own skills at every restart. After a compaction the engine re-attaches every skill invoked earlier in the session in full: `stack` 12.7k characters, `findings` 7.6k, `prove` 7.1k, `lane` 6.4k, `handoff` 4.1k, `bugfix` 2.4k, besides the kit's `session-kit:handoff` at 2.6k. That is 14% of lane1's restart and 4.9% of its session cost, from skills most of which were read once at the start. The project has a `handoff` skill beside the kit's. The fix is the project's: shorter skill bodies, or the long reference kept as a document the model reads when needed, which the engine does not re-attach.
4. The files the engine restores and the handoff's list do not overlap. The engine puts back the 2 to 4 most recently read files after a compaction (4.9k to 9.3k tokens). The model read again 0 of 161 of them in its next 15 requests. The handoff's document list directs a different set. The cost of the restore is in the restart, and whether the model uses those files is not measured.
5. The compaction's summary is 4.7k to 5.7k tokens and repeats the handoff. `CLAUDE.local.md` is loaded into the restart as well (2.2k to 3.2k), and holds the task, the decisions, where the work stands and the next step, which the summary restates, with the files, snippets and errors sections the engine's prompt asks for. The kit's compact instruction asks the summary to keep what the file says.
6. The skill list is 5.5k to 7.4k tokens and 6.7k characters of it are the Anthropic skills plugin's 12 entries. (docx, pptx, xlsx, pdf, docs, google-workspace and others), none of which was invoked in these projects. The kit's two entries are 388 characters.
7. The kit's tools are 0.65k tokens and not worth deferring. Deferring `new_task` and `clear_point` saves 0.2% of a session and costs a ToolSearch round trip at each use.

## The cuts, with what each saves

Savings are shares of a session's modeled cost, from the per-1k figures above. Sizes are measured except where marked.

| Cut | Tokens | Saves | Who | Status |
| --- | --- | --- | --- | --- |
| Deny the Artifact tool in the user settings | 13k | 4.3% to 4.6% | the owner | in the nix-darwin source on 2026-10-26, live after its rebuild (`OWED.md`) |
| Deny the iOS simulator server in the user settings | 2.2k | 0.8% | the owner | in the nix-darwin source with the rule above, unproven on the app's server |
| Deny the Browser tools in a project that never drives one (lane1, demo-mat-porting and mat-lib never did) | 7.6k | 2.7% | the owner, per project | not applied, and untested on the app's own server |
| lane1: shrink or move the project's skill bodies | 15.3k | 4.9% of lane1 | the project | analysed in `lane1-skills.md`, with no change made |
| Disable the Anthropic document skills in projects that do not use them | 2.5k | 0.8% to 0.9% | the owner | not tested |
| A shorter compaction summary: the compact instruction says the file holds the task, decisions and state, and the summary adds only what the file lacks | 2k to 3k (estimated) | 0.6% to 1.0% | the kit | an experiment on one project, where a handoff that loses something shows as a question or a re-run command |
| Cut the kit's handoff skill body in half | 0.5k | 0.2% | the kit | not started |

Together about 10% of a session's cost in mat-lib and 14% in lane1, which also has its skills to shrink, against the 7% to 9% the first analysis found for moving the threshold from 260k to 200k, and without that cut's 50% to 100% more compactions. The Artifact deny rule is most of it, for three lines of settings.

The kit has little to cut in the restart beyond the summary. Its global rules are 5.3k to 5.8k tokens (1.8% to 2.0% of a session) and are held by the rulebook's word budget. Lowering the 250k warning stays as the first analysis left it.

## Method and what limits it

- A restart request is the first request after a `compact_boundary` whose `keep` is 0, so all of its messages are in its blobs. Its usage gives the total, and the cache read of 52 of 53 restarts is the prefix (55.15k to 55.81k). The other one wrote everything cold (109k) and is measured against the same prefix.
- The messages' share is split by characters. The check: over the 52 warm restarts a least-squares fit of the messages' tokens against characters gives 2.69 characters a token for prose and rules and 2.57 for restored file text, with a median error of 0.7%. One density holds for all sources, so the shares are sound.
- The tool schemas are split by their JSON characters at the prefix's density (2.94 to 3.1 characters a token). The system prompt takes the rest of the prefix by the same method.
- The records exist only from engine 2.1.308, so there is no June breakdown. The statement that the growth is not the kit's rests on the prefix alone (55.5k) exceeding June's whole restart (44k to 47k), whatever June's prefix was.
- The tool counts of the init message vary from run to run (the connectors load while it is written), and the Artifact result rests on the request shape, which is stable across the 8 runs.
- Not measured: whether the model uses what the engine restores, and what a shorter summary loses. The saving of 2k to 3k tokens is an estimate from the summary's size and the file's overlap, with no run behind it.
- The three projects ran the desktop app. A terminal session has fewer tools (16 in the request against 54) and a smaller prefix.
