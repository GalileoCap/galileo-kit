# Memories, and how sessions cross a context boundary

Read on 2026-11-17, by the owner's ask: where every session's memory belongs, and whether sessions hand off and compact as the rules say. Nothing in the kit or any project was changed by this reading. The proposals at the end wait on the owner.

## Part 1: the memories

### What is there

Every project's memory sits in `~/.claude/projects/<folder>/memory/`, readable from any session. There are 82 memory files in 30 folders, about 20,000 words, plus each folder's `MEMORY.md` index, which the engine loads into every session of that project. Worktrees share their repository's folder: the tagents lanes all write to `tagents-main`.

The owner's suspicion holds. Of 82 files, none needs to be a memory:

| Where it belongs | Files | What to do |
| --- | --- | --- |
| Nowhere: the project is gone from disk, or the event is over | 18 | delete |
| Already in the project's CLAUDE.md, a skill or its docs | 18 | delete, after a glance at the copy |
| The project's CLAUDE.md, a skill or its docs, where it is missing | 35 | move, then delete |
| Every project: a rule of the owner's or a fact of this machine | 11 | a candidate for `global/CLAUDE.md` (by `O20`, a rule spreads beyond one project only once its trial shows it works), then delete |

Four things make memory the wrong home:

1. A memory is one folder's. A preference the owner states once ("tell me how, don't run it", "dry and blunt", "every diagram in mermaid", "batch the questions") lands in whichever project heard it and reaches no other. Eleven of these sit across six projects, and the Nix-only machine is stated three times (`os/main`, `slides`, `addictive_idle`).
2. Memory outlives the project. Eight folders point at a directory that is gone from disk (`budget_tracker`, `quiro`, `quicknote`, `git_organization/bots`, `gastainas/dev`, `twinlab/main`, and two scratch workspaces). Their 18 files load into no session.
3. Memory turns into a changelog. `budget-tracker`'s project memory is 5,212 words of release history, and its `MEMORY.md` index alone is 1,178 words, loaded into every session of that project before it did anything. The same history lived in its `PLAN.md`.
4. A memory can claim a copy that does not exist. `feedback_screenshots_of_changes` (tagents) says "the project rule is in the frontend skill §4": no skill in tagents mentions screenshots or light mode. The mermaid rule is in no CLAUDE.md or skill either. Those two rules exist only in memory.

Memories written in a scratch workspace (`scratch-2026-10-07`, `scratch-2026-09-07`, `scratch-2026-11-16`) are the worst case. No later session opens that folder, so `record-open-questions` and `watch-for-failure-idle`, both about `misc/llms`, are invisible to every session in `misc/llms`.

### Every file

Paths are under `~/devel` unless stated otherwise.

| Project | Memory | Where it belongs |
| --- | --- | --- |
| scratch 2026-11-16 | `tagents-worktree-names` | tagents docs: a fact about its worktrees |
| scratch 2026-11-16 | `transcript-copies` | this repo, `docs/session-tooling-design.md`: the reader de-duplicates by uuid, the message-id ownership is not in it yet |
| `~/.config/nix-darwin` | `push-after-commit` | already in its CLAUDE.md: delete |
| scratch 2026-09-07 | `llm-test-nginx-certbot` | an ops doc for the `llm` host, and the unrotated Ollama token as a plan item where it will be seen |
| scratch 2026-10-07 | `probe-surprises` | `galileo/misc/llms` CLAUDE.md |
| scratch 2026-10-07 | `record-open-questions` | `galileo/misc/llms` CLAUDE.md |
| scratch 2026-10-07 | `watch-for-failure-idle` | `galileo/misc/llms` CLAUDE.md, and its general form is `session-watched` |
| `galileo/ainas/dev` | `levantar-el-stack-para-revisar` | its CLAUDE.md (the stack is there, the "down after a prod deploy" rule is not) |
| `galileo/facu/alc` | `uni-archive-sync` | already in its CLAUDE.md: delete |
| `galileo/facu/ssoo` | `descargas-panel-browser` | every project: a technique for the browser pane (a kit doc or a skill) |
| `galileo/facu/ssoo` | `final-ssoo-contexto` | already in its CLAUDE.md, and the exam was 2026-09-14: delete |
| `galileo/facu/ssoo` | `fuentes-final-ssoo` | already in its CLAUDE.md: delete |
| `galileo/gamedev/card` | `test-runs-one-minute-cap` | its CLAUDE.md (no timeout line there) |
| `galileo/gamedev/one-must-imagine` | `push-every-commit` | already in its CLAUDE.md: delete |
| `galileo/games/addictive_idle` | `edge-game-design-decisions` | the project has no CLAUDE.md: a `docs/design.md` |
| `galileo/games/addictive_idle` | `edge-sim-corrections` | the same design doc |
| `galileo/games/addictive_idle` | `nix-flake-for-all-tooling` | its CLAUDE.md, and every project (see `galileo-nix-macos-setup`) |
| `galileo/games/onitama` | `how-to-means-explain` | every project: "a how-do-I question is answered with steps, nothing run" |
| `galileo/games/onitama` | `stop-emulator-when-done` | its CLAUDE.md, and its general form is `O21` (nothing a session starts is left running unseen) |
| `galileo/gastainas/dev` | `levantar-el-stack-para-revisar` | gone, a copy of ainas's: delete |
| `galileo/misc/brain-dumping` | `never-suspend-gui-processes` | its CLAUDE.md (no vmmap or lldb line there) |
| `galileo/misc/budget_tracker` | `code-quality-rules`, `project-budget-tracker`, `workflow-preferences` | gone: delete, with the 1,178-word index |
| `galileo/misc/galileo-kit` | `update-every-install` | this repo's `OWED.md` procedure, or better a script that reads `installed_plugins.json` and does it (`O5`) |
| `galileo/misc/generic-app` | `allowlists-kept-by-session` | its CLAUDE.md |
| `galileo/misc/generic-app` | `conventions-enforced-by-gates` | every project: "a convention shown by example is generalised and gated" |
| `galileo/misc/generic-app` | `example-names-are-suggestions` | every project: "a name in the owner's example is a suggestion" |
| `galileo/misc/git_organization/bots` | `genbot-lineage` | gone: delete, or a README where the bots now live |
| `galileo/misc/quicknote` | `test-runs-take-over-the-machine` | gone: delete |
| `galileo/misc/quiro` | six `feedback-*` and `user-oftalmologia` | gone: delete (one only restates "publishing is the owner's") |
| `galileo/os_concepts/main` | `deferred-failure-tests` | its `.claude/hidden-docs/plan.md` |
| `galileo/os_concepts/main` | `hidden-docs-location`, `user-implements-claude-reviews` | already in its `.claude/CLAUDE.md`: delete |
| `galileo/os/main` | `anti-overengineering-principle`, `collaboration-rules-os-project`, `hidden-docs-notebook`, `os-prototype-archive` | already in its CLAUDE.md §3 and hidden docs: delete |
| `galileo/os/main` | `os-from-scratch-rewrite`, `os-target-evaluation-2026-08` | stale ("zero commits", a bake-off from August) and in hidden docs: delete |
| `galileo/os/main` | `galileo-nix-macos-setup` | every project, as a machine fact, and stale (macOS 25.5, Nix 3.21): the nix-darwin repo or the global rules |
| `galileo/os/main` | `tone-dry-and-blunt` | every project: the owner's tone |
| `galileo/smplworks/logi/main` | `feedback_collaboration` | its CLAUDE.md |
| `galileo/sofi/gallery` | `cursiva-es-llm-ismo`, `estilo-propio-no-generico` | its CLAUDE.md, and both read as design rules for any UI the owner gets |
| `iquall/mat-lib` | `test-layer-workflow` | its CLAUDE.md (the layers are there, the run commands and `--durations=0` are not) |
| `iquall/misc/core5g` | `nix-is-local-only` | its CLAUDE.md, as "`local/` is the owner's and is never committed" |
| `iquall/misc/slides` | `typst-slides-library` | says itself the lib's CLAUDE.md is the authoritative copy: delete |
| `iquall/misc/slides` | `decks-are-english-only`, `prefers-reusable-over-pixel-match` | the decks' and the lib's CLAUDE.md |
| `iquall/misc/slides` | `pdf-to-pptx-libreoffice`, `typst-to-pptx-backend`, `tmforum-brand`, `asset-catalog-recreation` | the lib's docs: they are design notes |
| `iquall/misc/slides` | `agent-fabric-drive-folder` | the decks' docs, as a source |
| `iquall/misc/slides` | `hackathon-handover-port` | history, done: delete |
| `iquall/misc/slides` | `no-global-installs-use-uv` | every project: a machine rule |
| `iquall/misc/trustworthy_ai_hackhathon` | `never-run-submit-sh`, `trustworthy-ai-hackathon` | already RULE #2 of its CLAUDE.md, and the hackathon ended 2026-10-07: delete |
| `iquall/tagents` | `dev-pushes-without-asking`, `feedback-demo-lane-pushes-tagents-demos`, `user-profile` | already in its CLAUDE.md §4: delete |
| `iquall/tagents` | `feedback-everything-in-the-kit`, `every-page-and-table-basics` | already in the `/demo` and frontend skills: delete |
| `iquall/tagents` | `feedback-titles-not-numbers` | already a global rule ("an id carries its name"): delete |
| `iquall/tagents` | `feedback-screenshots-of-changes` | the frontend skill, where it claims to be and is not |
| `iquall/tagents` | `feedback-assign-lane-choice`, `feedback-desk-checks-assignment-fit` | the desk's skill or CLAUDE.md |
| `iquall/tagents` | `agents-prompt-knowledge-skills` | tagents docs, the guide to building an agent |
| `iquall/tagents` | `misc-lane-static-checks-yes-tests-no` | superseded by `/session-kit:iterate`: delete, or one line in CLAUDE.md |
| `iquall/tagents` | `targets-hold-on-a-busy-machine` | the intent entry it qualifies (tagents `O16`) |
| `iquall/tagents` | `feedback-diagrams-in-mermaid`, `feedback-batch-questions`, `user-company-spelling` | every project: the owner's words were general |
| `iquall/tagents` | `sweep-touch-no-tells` | every project: it amends the global tells rule, so it belongs beside it |
| `iquall/twinlab` | `twinlab-vm-deployment` | its docs, as the deploy procedure |
| `iquall/twinlab/main` | `twinlab-arm64-emulation-limits` | gone as a folder: twinlab's docs |

### Why sessions write memories

The global rules send them there: "Memory holds what crosses conversations: preferences and feedback." The engine's own instructions say the same, and a correction from the owner reads as feedback. So each correction becomes a memory of the project it happened in, and the owner's general preferences end up spread across folders, which is the opposite of `O3` (rules are written once in this repository).

## Part 2: handoff and compaction in the transcripts

Every session file under `~/.claude/projects` written since 2026-11-01: 316 sessions, 36,268 model requests, 1,630 of the owner's prompts, 544 contexts (a context runs from a session's start or a compaction to the next). Each record is counted once by uuid and only in its own session. The scanner and its output lived in the session's scratchpad and go with it.

### The two thresholds disagree

The global rule says: past 150,000 tokens, at a clear point, hand off and ask to compact. The kit warns at 250,000 (`thresholdTokens`, no project overrides it), grows firmer at 300,000 and says stop at 400,000. The cold-cache timer's floor defaults to the same 250,000.

Sessions mostly wait for the kit's warning:

| Context when `clear_point` was called | Calls |
| --- | --- |
| under 150k | 20 |
| 150k to 250k | 53 |
| 250k to 300k | 128 |
| 300k to 400k | 84 |
| 400k and over | 1 |

212 of the 286 calls came after a kit warning in the same context. The median is 274,551. 401 of the 544 contexts passed 150k and 217 passed 250k, and 68% of all requests (24,530) ran with more than 150k in context. Three calls in four wait for the kit's warning, so the 150k sentence in `global/CLAUDE.md` moves few sessions.

### Running cold

A cold return here is a request after an hour or more of silence, at 150k or more, where over half the context was written to the cache again. There were 51 since November 1, writing 10.35 million tokens to the cache that a handoff and compaction would have kept to a few tens of thousands each.

- 44 of the 51 (8.4 million tokens) were below 250k. There the kit neither warns nor arms its cold-cache timer, so nothing writes the handoff before the cache expires. This is the main cause.
- 2 show the timer firing late: its handoff ran after the hour was out, at 263k and 301k, most likely with the machine asleep, which holds a timer back.
- 3 were turns interrupted by the crash of November 4, which never ended the usual way, so no timer was armed.
- 2 were plain returns past 250k with no timer in sight (tagents lane3 after four days, lane4 after five hours). Either the chain option is off there or a reload dropped the timer, which `context.tsx` says can happen.

Beside the returns, 167 contexts passed 150k and ended with no compaction (the session closed or is still open), 49 of them past 250k, 41 of those with no handoff written after crossing 150k. Each of them starts cold if it is ever resumed.

### Asking for a new task right after the owner's handoff

`new_task` was called 23 times, 21 of them offering the handoff and a clear. The model's prose matches the calls: no session asked for a clear in words without the tool.

The pattern the owner sees comes from three things:

1. A compacted context is never fresh. `opensFreshContext` in `hooks/context.tsx` takes a context as fresh only when `turns()` is 0 and no assistant message is in it. After a compaction neither holds. So the first prompt after the owner's handoff and compaction, if it starts other work, is offered a clear. 7 of the 21 offers came on the very first prompt after a compaction, among them sofi-anki `c3572827`, four minutes after "Handoff and compact, and we'll discuss the next step", and sofi-guardias `e647a36f`, one second after the chain compacted. The others are tagents-demo-mat-porting `b3fbef9c`, the lane5 sessions `4aa841d4`, `17ae58c7` and `8ead005d`, and brain-dumping `2cbbb979`. Five more came two to four prompts after one.
2. There is no clear for the model to ask for. The owner said "Handoff and clear" three times (`a48aa79c`, `62ee29e2`, `8ead005d`). Each time the model called `clear_point`, which compacts, so the context kept the old task, and in `8ead005d` the next prompt drew a `new_task` offer for that reason.
3. The handoff is written twice. 145 of the 286 `clear_point` calls followed, within five minutes, the model's own handoff (the skill, or a write to `CLAUDE.local.md`), at a median 256k of context. Then the kit runs `/session-kit:handoff` again before compacting. Of the 48 times the owner asked for a handoff in words, 43 went this way. The global rule invites it: "commit, write `CLAUDE.local.md` (`/session-kit:handoff`) and end the turn asking to compact", while `clear_point`'s description says the kit writes the handoff.

The offer in a session that had just been cleared (`6322a28f`, `b3fbef9c` at 11:11) was answered "nothing to clear", as designed. The offer in this repository today (`dde26224`) was right: that context had held two other tasks.

## Proposals

Each is a change to the kit or the rules. None is made.

### Memories

1. Change the global rule "Memory holds what crosses conversations: preferences and feedback" to send each note to a file: a project's rule to its CLAUDE.md or skill, a general rule of the owner's to this repository as a candidate rule, and memory only for what fits nowhere else. The engine's memory instructions sit outside the kit, so this rule is what turns a session.
2. Have a kit check list the memory files per project, with the gone folders flagged, run in the week review, so the drift is seen.
3. Do the sweep in the tables above: one session per project moves and deletes its own, since each needs the project's CLAUDE.md read. The twelve general rules come here as candidates for the owner.

### Running cold

4. Bring the two thresholds together. Either the rule says 250k, or the kit's `thresholdTokens` and the timer's floor go to 150k. The data argues for the timer's floor lower than the warning: 44 of 51 cold returns sat between 150k and 250k, while warning earlier would mean more handoffs in contexts that end soon anyway.
5. Re-check the cold timer against wall-clock time when the machine wakes, so a sleep does not leave it running late.

### The redundant ask

6. Take the first prompt of the owner's after a compaction whose next step was theirs (the band's Handoff and compact, or `clear_point` with `next_step: owner`) as fresh: `new_task` answers "nothing to clear" there, as after a clear.
7. Give `clear_point` a clear: with `next_step: owner` the kit hands off and clears instead of compacting. The handoff carries the state and the owner's next prompt starts clean. It also makes "Handoff and clear" mean what it says.
8. Write the handoff once. Either `clear_point`'s description and the global rule say "do not write the handoff yourself", or the kit skips its own handoff when `CLAUDE.local.md` was written in the same turn.
