# Memory sweep: the plan, for the owner's review

Prepared on 2026-11-17 and 2026-11-18 from proposal 3 of [memories-and-context-boundaries.md](memories-and-context-boundaries.md). It says, for each of the 82 memory files under `~/.claude/projects/<folder>/memory/`, what happens to it, where its content goes and in which words. Every verdict was checked by reading the memory and its target as they stand today. The owner approved it on 2026-11-18 with four changes: rule 11 is not adopted, core5g's text goes into an untracked `.claude/CLAUDE.md`, tagents' moves are made in its `dev` worktree, and twinlab waits for later. The Ollama token is dropped. Rules 1 to 9 are `A108`.

## Counts

| Action | Files |
| --- | --- |
| Delete: the project, the event or the workflow it describes is gone, and nothing of it is kept | 11 |
| Delete: its content is already in a project file, quoted below | 34 |
| Move: the content goes into a project file, then the memory is deleted | 26 |
| General rule: a candidate for `global/CLAUDE.md`, then the memory is deleted | 11 |
| Total | 82 |

The report's table had 18, 18, 35 and 11. The difference comes from the verdicts below, read again against the targets.

Every folder's `MEMORY.md` is deleted once its last file goes, since no file stays a memory. That is 31 indexes: the 30 folders that hold memories and `misc/guardias`, whose index is already empty.

### Verdicts of the report found wrong

- `quiro` is not gone. The project lives at `~/devel/galileo/sofi/checklist` under the same name, and its CLAUDE.md already holds five of the six memories. The sixth, explaining a rule before closing the work, moves there.
- `one-must-imagine/push-every-commit` is not in its CLAUDE.md. It is only in `CLAUDE.local.md`, which the next handoff rewrites. It moves.
- `addictive_idle/edge-sim-corrections` is already in `README.md`, "What the simulation found", all five findings and a sixth. Delete.
- `generic-app/allowlists-kept-by-session` is already in CLAUDE.md (`A27`). Delete.
- `smplworks/logi/feedback_collaboration` is already in CLAUDE.md, "Collaboration". Delete.
- `sofi/gallery/cursiva-es-llm-ismo` and `estilo-propio-no-generico` are already in `docs/architecture.md`, "El aspecto". Delete, and the general form is offered as an optional rule.
- `iquall/mat-lib/test-layer-workflow` is stale. The package was rewritten as `abstract-mat`: there are no `tests/unit`, `tests/component` or `tests/live`, no `--run-live`, no `modeling_batch` and no `mat_cleanup`. `scripts/test` runs `pytest --timeout=10`. Delete.
- `misc/slides/decks-are-english-only`, `prefers-reusable-over-pixel-match`, `agent-fabric-drive-folder` and `asset-catalog-recreation` are already in the decks' and the library's CLAUDE.md and README. Delete.
- `misc/llms` (from scratch 2026-10-07): `record-open-questions` and `watch-for-failure-idle` are already in its CLAUDE.md and `doom-prep/PROCESS.md`. Delete. Of `probe-surprises` only the `user-leads.md` line is missing.
- `os_concepts/hidden-docs-location` is not in `.claude/CLAUDE.md`, which names only `real-world-context.md`. The list of notes moves.
- `tagents/feedback-assign-lane-choice` and `feedback-desk-checks-assignment-fit` are stale. The desk orders objectives and assigns nothing: "It starts no lane: the owner starts a lane on an objective" (`.claude/skills/desk/SKILL.md`, after `P0145`). The `work*`, `studio*` and `work-misc` lanes they name do not exist. Delete.
- `tagents-worktree-names` (scratch 2026-11-16) is a fact for whoever reads transcripts, so it goes to this repository's transcript tooling.
- `ainas/levantar-el-stack-para-revisar` moves as the report said, but its `./dev.sh` commands are stale: `dev.sh` is absent from the repository. The text below uses `docker compose` from `deploy/`.

## Apply order

1. Archive, in this repository's session. One `tar` of every `memory/` folder into `~/claude-archive/memory-sweep-2026-11-18.tar.gz`, so each deletion below can be undone. Then the deletions are permanent.
2. Folders that need nothing, in this repository's session. Delete `budget_tracker` (3), `gastainas/dev` (1), `quicknote` (1) and the empty `misc/guardias` index, with their `memory/` folders. No project is touched.
3. This repository. The general rules the owner picks, each with its paragraph in `global/RATIONALE.md`, an action entry and the rulebook checked. Then `update-every-install`, `transcript-copies` and `tagents-worktree-names`. The memory rule of proposal 1 is already in `global/CLAUDE.md` (`A103`, memory holds only what no file can), so the general rules join it there.
4. Deletions only, already verified, in one session: `nix-darwin`, `facu/alc`, `os/main`, `smplworks/logi`, `sofi/gallery`, `iquall/mat-lib`, `trustworthy_ai_hackhathon`, and `generic-app` once its two general rules are in. No project file changes, so no CLAUDE.md needs reading again.
5. One session per project with a move, in its own folder, reading its CLAUDE.md first, as each needs its own voice and gates: `galileo/ainas/dev`, `facu/ssoo`, `gamedev/card`, `gamedev/one-must-imagine`, `games/addictive_idle/main`, `games/onitama`, `misc/brain-dumping`, `misc/git_organization`, `misc/llms`, `os_concepts/main`, `sofi/checklist`, `iquall/misc/core5g`, `iquall/misc/slides`, `iquall/tagents/main`, `iquall/twinlab`. Each commits under its project's rules (several push on commit) and deletes the memories it absorbed, which may sit in another folder (a scratch workspace, `quiro`, `git_organization/bots`, `twinlab/main`).

After each step, `MEMORY.md` of every emptied folder is deleted with its `memory/` folder.

## General rules for `global/CLAUDE.md`

Eleven memory files make nine rules once the three statements of the Nix-only machine are one. Two more are offered and not recommended. By `O20`, a rule spreads beyond one project once its trial shows it works: each names the project where it held. Each one adopted gets its reason under the same heading in `global/RATIONALE.md` and an action entry under `docs/intent/`.

Word counts are by whitespace, the bullet's leading dash excluded. The bold lead-ins in the proposed texts follow the form of the file each one joins.

| # | From | Section | Words |
| --- | --- | --- | --- |
| 1 | `os/main/galileo-nix-macos-setup`, `slides/no-global-installs-use-uv`, the general part of `addictive_idle/nix-flake-for-all-tooling` | How to work | 44 |
| 2 | `onitama/how-to-means-explain` | How to work, a sentence added to the tagged-line rule | 19 |
| 3 | `generic-app/conventions-enforced-by-gates` | How to work | 40 |
| 4 | `generic-app/example-names-are-suggestions` | How to work | 32 |
| 5 | `os/main/tone-dry-and-blunt` | How to work | 26 |
| 6 | `tagents/feedback_diagrams_in_mermaid` | How to work | 18 |
| 7 | `tagents/feedback_batch_questions` | How to work | 24 |
| 8 | `tagents/user_company_spelling` | How to work, a sentence added to the typo rule | 7 |
| 9 | `tagents/feedback_sweep_touch_no_tells` | How to work, a sentence added to the tells rule | 10 |
| 10 | `facu/ssoo/descargas-panel-browser` | not recommended | 41 |
| 11 | `sofi/gallery/cursiva-es-llm-ismo`, `estilo-propio-no-generico` | optional, How to work | 25 |

Budget: `session-rulebook` reads 3,437 of 7,500 words today (`global/CLAUDE.md` 1,580, this repository's CLAUDE.md 1,245, `CLAUDE.local.md` 611). Rules 1 to 9 add 220 words: the rulebook goes to about 3,657 and `global/CLAUDE.md` to about 1,800. With rule 11, 245 words and about 3,682. All eleven, 286 words and about 3,723. Every project's rulebook carries `global/CLAUDE.md`, so each gains the same.

### 1. The Nix-only machine

Tried in `os/main` (2026-08-19), `misc/slides` (2026-07-30) and `addictive_idle` (2026-09-08). The memory's versions are stale: it says macOS 25.5 and Determinate Nix 3.21, and the machine runs macOS 27.2.1 and Determinate Nix 3.24.1. The rule names no version.

> - **This machine is Nix-managed.** A tool comes from the project's flake devShell or the nix-darwin configuration. Nothing is installed with brew, which is absent, or globally or per user (`pip install --user`, `npm i -g`). A Python one-off runs as `uv run --with <package>`.

### 2. A "how do I" question

Tried in `onitama` (2026-11-14). It is the `Ask:` tag's behaviour reached without the tag, so it joins that rule as one sentence, after "`Ask:` is a question, answered with no edits and no runs that write.":

> An untagged "how do I" is an `Ask:`, answered with the steps and nothing run on the owner's devices.

### 3. A convention shown by example

Tried in `generic-app` (2026-10-22, the frontend components and the backend's `Err` ladders). `CODE.md` holds the narrower "A structural rule is held by a tested gate", for pure-core projects only.

> - **A convention the owner shows by example is generalised and gated.** It reaches every case of its kind, the unnamed ones too, and a gate with a planted case fails on the next drift. Prose alone does not hold it.

### 4. Names in an example

Tried in `generic-app` (2026-10-22).

> - **A name in the owner's example is a suggestion.** Apply the pattern as shown, rename in the same pass where a better name fits the code's words, and say what was renamed.

### 5. Tone

Tried in `os/main` (2026-08-19), where its copy stays in CLAUDE.md §8. The owner said it of reviews in one project, so whether it holds for every project is the owner's call.

> - **Dry and blunt.** Lead with the verdict, one line per finding where one does. No hedges, no praise that carries nothing, no restating the owner's question.

### 6. Diagrams

The owner's `Decide:` in tagents `demo-misc`, 2026-11-03: "From now I want every diagram in mermaid, no ascii". It is in no CLAUDE.md or skill today.

> - **Every diagram is a mermaid block**, in documents and replies alike, rendered once to check that it parses.

### 7. Questions together

Tried in tagents (2026-10-24).

> - **The owner's open questions go together**, up to four in one ask. A question waits alone only when its answer changes the next one.

### 8. The company's name

Tried in tagents (2026-08-25). It joins the typo rule as its last sentence:

> The company is Iquall, capital I only.

### 9. A sweep and the tells

The owner's ruling in tagents, 2026-10-27, which amends the global rule itself. It joins "A file you touch leaves with fewer prose tells" after its first sentence:

> A file only a mechanical sweep touched keeps its tells.

### 10. Downloads behind a login: not recommended

A technique used once, in `facu/ssoo`, whose CLAUDE.md keeps it ("Restricciones"). It would cost 41 words on every turn of every project. Recommended: leave it in `facu/ssoo` and add nothing. The wording, if the owner wants it:

> - **A file behind a login is fetched from the logged-in page.** In the Browser pane: `fetch(url, {credentials: 'include'})`, a blob, an `<a download>` click, about six per call since the page tool stops at 45 s. The owner confirms each download.

### 11. Visual design: optional

The owner's words in `sofi/gallery` (2026-10-27) were about one app ("muy AI y básicos", italics as "un LLM-ismo muy fuerte"), and the report read them as the owner's taste in any interface. Its project copy stays in `docs/architecture.md`.

> - **A visual design starts from its domain.** No generic grey palette with one blue or teal accent, and italics only for the user's own writing.

### Rules found already global

These memories hold nothing the global rules lack, and are counted as deletions with a copy:

- `tagents/user_profile`: "Be critical" and "Say what you are about to do, then do it" (record the assumptions).
- `tagents/feedback_titles_not_numbers`: "An id carries its name". The memory asks for the title at every mention, the rule at the first mention in a reply and in each section. The owner may want the rule tightened.
- `onitama/stop-emulator-when-done` has a general form in `O21` (nothing a session starts is left running unseen). Its project text moves to onitama.

## This repository: `galileo/misc/galileo-kit`

| Memory | Folder | Action | Target |
| --- | --- | --- | --- |
| `update-every-install` | `misc/galileo-kit` | move | `OWED.md`, its opening paragraphs |
| `transcript-copies` | scratch 2026-11-16 | move | `docs/PLAN.md`, Deferred |
| `tagents-worktree-names` | scratch 2026-11-16 | move | `docs/session-tooling-design.md`, "`session-transcripts`, a reader" |

`OWED.md` is append-only by entry, and its opening paragraphs are no entry. Added after "`session-owed --since <ref>` lists what a range of history owes.":

> An install reaches every scope: the user scope, then every project that `~/.claude/plugins/installed_plugins.json` lists, read at each install, none skipped and none asked about. In a worktree (the tagents installs), `update` answers "already at the latest" and leaves it old: `uninstall`, then `install --scope project`, brings it up. Read the versions back after. After each project install, `git status` its `.claude/settings.json` and restore it with `git checkout` when its parsed JSON matches HEAD (demo-nuvem's is rewritten with its `\u` escapes as characters).

By `O5`, the better home is a program: a `session-install` command that reads `installed_plugins.json` and does all of it. Offered for `docs/PLAN.md`, Candidates.

`docs/PLAN.md`, Deferred:

> - The reader counts a request once across files. `records.py` counts a record once by uuid and drops a fork's copy of its parent, but some session files hold only another session's requests, at times under their own `sessionId`. Giving each assistant message id one owning file removed an overcount of 15 to 20% in the transcript analysis of 2026-11-16.

`docs/session-tooling-design.md`, at the end of "`session-transcripts`, a reader":

> In tagents, the `work*` worktrees (work6, work9) were renamed `lane*` around late October 2026, so a cut by worktree takes them as one kind.

`MEMORY.md` of `misc/galileo-kit` and of scratch 2026-11-16: deleted.

## No target: folders gone

| Memory | Folder | Action | Why |
| --- | --- | --- | --- |
| `code-quality-rules` | `misc/budget_tracker` | delete | project gone. No defaults or fallbacks and no early abstraction are `CODE.md`'s and the global rules' |
| `project-budget-tracker` | `misc/budget_tracker` | delete | project gone. 5,212 words of release history |
| `workflow-preferences` | `misc/budget_tracker` | delete | project gone. Planning, test first, small commits and decisions written down are global rules, and "make a note means a file" is proposal 1's |
| `levantar-el-stack-para-revisar` | `gastainas/dev` | delete | folder gone. The same file as ainas's, which moves |
| `test-runs-take-over-the-machine` | `misc/quicknote` | delete | project gone. Brain-dumping's "No test of the core creates a window" holds its successor |

`MEMORY.md` of all three, and the empty one of `misc/guardias`: deleted.

## Deletions only

| Memory | Project | Action | The line that holds it |
| --- | --- | --- | --- |
| `push-after-commit` | `~/.config/nix-darwin` | delete (copy verified at `CLAUDE.md`: Remote) | "Push `main` after every commit without asking: the owner's standing order (2026-11-17), which overrides the global rule that publishing is the owner's." |
| `uni-archive-sync` | `galileo/facu/alc` | delete (copy verified at `CLAUDE.md`, line 30) | "Cada commit en `main` se espeja en uni-archive como `GalileoCap__alc/main`, con `facu-archivar`" |
| `collaboration-rules-os-project` | `galileo/os/main` | delete (copy verified at `CLAUDE.md`: §2 Collaboration rules) | "I do NOT" and "Where the line falls" |
| `anti-overengineering-principle` | `galileo/os/main` | delete (copy verified at `CLAUDE.md`: §3) | the memory itself says "Canonical statement is in the project's `CLAUDE.md` §3" |
| `hidden-docs-notebook` | `galileo/os/main` | delete (copy verified at `CLAUDE.md`: §6) | "**Read `INDEX.md` at the start of every session on this project.**" |
| `os-prototype-archive` | `galileo/os/main` | delete (copy verified at `CLAUDE.md`: §5 and §7) | "Prior prototypes: `~/devel/galileo/misc/git_organization/os/`, read-only reference." |
| `os-target-evaluation-2026-08` | `galileo/os/main` | delete (copy verified at `CLAUDE.md`: §4) | "The **language will be decided from these tests.**" |
| `os-from-scratch-rewrite` | `galileo/os/main` | delete | stale: "zero commits" in August, 17 commits today |
| `galileo-nix-macos-setup` | `galileo/os/main` | general rule 1 | |
| `tone-dry-and-blunt` | `galileo/os/main` | general rule 5 (copy also at `CLAUDE.md`: §8) | "**Dry, blunt, concise.**" |
| `feedback_collaboration` | `galileo/smplworks/logi/main` | delete (copy verified at `CLAUDE.md`: Collaboration) | "Do not propose changes or refactors unless explicitly asked." |
| `cursiva-es-llm-ismo` | `galileo/sofi/gallery` | delete (copy verified at `docs/architecture.md`: El aspecto) | "Libre Caslon en cursiva solo para lo que escribe ella, las notas (`A34`); las ayudas, los contadores y los avisos van en Jost derecha" |
| `estilo-propio-no-generico` | `galileo/sofi/gallery` | delete (copy verified at `docs/architecture.md`: El aspecto) | "Se descartaron, mirándolas en maquetas, una paleta gris con un solo color de acento (se ve como cualquier app)" |
| `test-layer-workflow` | `iquall/mat-lib` | delete | stale: the layers, `--run-live` and the live fixtures are gone |
| `never-run-submit-sh` | `iquall/misc/trustworthy_ai_hackhathon` | delete (copy verified at `CLAUDE.md`: RULE #2) | "**RULE #2: NEVER RUN `submit.sh` (hand-in).**" The hackathon ended on 2026-10-07. |
| `trustworthy-ai-hackathon` | `iquall/misc/trustworthy_ai_hackhathon` | delete (copy verified at `CLAUDE.md`) | the memory points at CLAUDE.md as "Master context + file index", and the event is over |
| `allowlists-kept-by-session` | `galileo/misc/generic-app` | delete (copy verified at `CLAUDE.md`: The frontend's names) | "The looks allowlist is `looks.allowed` in `.claude/claude-kit.json`. The session keeps it without asking, and whenever it grows looks again at every entry for one that can go. (`A27`)" |
| `conventions-enforced-by-gates` | `galileo/misc/generic-app` | general rule 3 | |
| `example-names-are-suggestions` | `galileo/misc/generic-app` | general rule 4 | |

`MEMORY.md` of each of these eight folders: deleted.

## `galileo/ainas/dev`

| Memory | Action | Target |
| --- | --- | --- |
| `levantar-el-stack-para-revisar` | move | `CLAUDE.md`, "Reglas duras", as rule 13 |

> 13. **El stack local, arriba solo si hay algo para probar** (Galileo, 2026-09-22). Al terminar un trabajo que Galileo todavía no vio andar, el stack queda arriba (`docker compose up -d --build` desde `deploy/`, que reconstruye los bundles) y el mensaje final dice su URL. Apenas ese cambio está en prod y verificado, se apaga (`docker compose down` desde `deploy/`, que guarda el volumen) sin esperar a que lo pida. Lo que sigue sin desplegar lo deja arriba.

`MEMORY.md`: deleted.

## `galileo/facu/ssoo`

| Memory | Action | Target |
| --- | --- | --- |
| `final-ssoo-contexto` | delete (copy verified at `CLAUDE.md`: Estado del examen) | "Toma Baader." and "El plan viejo y el nuevo son idénticos salvo la 5.ª pregunta" |
| `fuentes-final-ssoo` | move | `CLAUDE.md`, "Estado del examen", one bullet. The two Telegram exports are already in the file map (`telegram_all.json`, `telegram_final_all.json`) |
| `descargas-panel-browser` | general rule 10 (copy verified at `CLAUDE.md`: Restricciones) | "Para bajar del campus: `fetch(url,{credentials:'include'})` → blob → `<a download>`, en tandas de ~6" |

> - Fuera del repo: Cubawiki (resúmenes y finales resueltos, sobre todo del plan viejo) y el doc de preguntas armado para Baader, <https://docs.google.com/document/d/1p6beQ6HlFan6sx12KixHVo5e6kxGDFmupdvDK4lDqY8/edit>.

`MEMORY.md`: deleted.

## `galileo/gamedev/card`

| Memory | Action | Target |
| --- | --- | --- |
| `test-runs-one-minute-cap` | move | `CLAUDE.md`, "Gates", after the `session-watched` sentence |

> A test or Godot run takes the Bash tool's `timeout` at 60,000 ms at most: the suite runs in seconds, so a run that lasts a minute is a hang, most often a script that failed to parse (`just scripts` shows it). A timeout is told to the owner at once (owner, 2026-11-14).

`MEMORY.md`: deleted.

## `galileo/gamedev/one-must-imagine`

| Memory | Action | Target |
| --- | --- | --- |
| `push-every-commit` | move | `CLAUDE.md`, a new "## Git" after "## Gates", in the words card uses |

> ## Git
>
> Every commit on `main` is pushed to `origin` (`GalileoCap/one-must-imagine`) at once, without asking: the owner's standing order of 2026-11-17, where the kit leaves publishing to the owner. No force-push, and no other branch or pull request unless asked.

`MEMORY.md`: deleted.

## `galileo/games/addictive_idle/main`

The repository has no commit yet and no CLAUDE.md. Its `README.md` holds the theme and the simulation's findings.

| Memory | Action | Target |
| --- | --- | --- |
| `edge-sim-corrections` | delete (copy verified at `README.md`: What the simulation found) | "Six things the design got wrong, in the order they were caught." |
| `edge-game-design-decisions` | move | a new `CLAUDE.md` |
| `nix-flake-for-all-tooling` | move, and general rule 1 | the same `CLAUDE.md` |

The new `CLAUDE.md`, whole:

> # EDGE
>
> What the game is, the simulation and the prototypes are in `README.md`. `sim/src/core/` is the game model, and it outranks any prose design where they disagree.
>
> ## Locked decisions (owner, 2026-09-08)
>
> - Theme: from mark to house. The player starts as a broke gambler and ends owning probability itself, and every upgrade is a rig.
> - Losses: banked wealth is never lost. Wagers are placed against flow (future income, Heat, time), never against stock.
> - Platform: a web prototype, then native mobile in Godot. A rewrite between the two is accepted.
> - The signature mechanic is the wedge economy: every game is a visible, editable probability distribution (wheel wedges, reel strips, pachinko pegs), and upgrades change those lists instead of granting a flat percentage.
>
> They hold until the owner reopens one.
>
> ## Tooling
>
> Every tool and setup step goes into the devShell of `flake.nix`, the Godot toolchain included when the port starts. Nothing is installed with brew, `npm i -g` or by hand. A project's `node_modules` from its lockfile is fine.

`MEMORY.md`: deleted.

## `galileo/games/onitama`

| Memory | Action | Target |
| --- | --- | --- |
| `stop-emulator-when-done` | move | `CLAUDE.md`, a new "## The emulator" after "## Branches and pushing" |
| `how-to-means-explain` | general rule 2 | |

> ## The emulator
>
> A task that started or used the Android emulator stops it before it ends, a failed or cut-short check included: `adb emu kill`, a check that no `qemu-system` process is left, then `adb kill-server`. It holds 2 GB of RAM and two cores of the owner's Mac (owner, 2026-11-14).

`MEMORY.md`: deleted.

## `galileo/misc/brain-dumping`

| Memory | Action | Target |
| --- | --- | --- |
| `never-suspend-gui-processes` | move | `CLAUDE.md`, "Rules of engagement", after the first bullet |

> - `vmmap`, `heap`, `footprint` and `lldb` pause their target, and each froze the machine once on 2026-10-28. They run on a process that owns a window only after the owner has said in this conversation that the machine is quiet, and only on a copy this session launched, found by its pid. A hung probe is never killed with its target left paused: end the target. An in-process reading (`task_info` in a driven step) comes first when it answers the question.

`MEMORY.md`: deleted.

## `galileo/misc/git_organization`

| Memory | Folder | Action | Target |
| --- | --- | --- | --- |
| `genbot-lineage` | `misc/git_organization/bots` (gone, folded into `bots-meta`) | move | `STATUS.md`, after the paragraph listing the nine meta repositories |

> In `bots-meta`, `GalileoCap__GenBot/dev` is the latest of eight restarts of the Telegram bot generator (Lua plugins, hot reload). Its `main` is six commits behind and lacks `telegram/`. The older ones keep the only sqlite and cache2go persistence (`tgGenBot_old/api/db.go`) and the FoodDO and IP designs (`GaliBot`).

`MEMORY.md` of `misc/git_organization/bots`: deleted.

## `galileo/misc/llms`

All three come from scratch 2026-10-07, which no `misc/llms` session opens.

| Memory | Action | Target |
| --- | --- | --- |
| `record-open-questions` | delete (copy verified at `CLAUDE.md`, line 14) | "**Standing rule (user, 2026-10-09): record every question, decision or confirmation the user has to make in `doom-prep/open-questions.md` (old and new), and ask them back when the user is ready to answer.**" |
| `watch-for-failure-idle` | delete (copy verified at `doom-prep/PROCESS.md`: Long-job discipline) | "Smoke-test every new probe on 2-3 items before the long run" and "the assistant's wait uses `galipc/bin/watch-job.sh`" |
| `probe-surprises` | move (the rule is at `doom-prep/PROCESS.md`: "Surprise rule (user, 2026-10-11)") | `doom-prep/PROCESS.md`, after the Surprise rule |

> - A mid-turn note the user marks as a note, without a priority, goes to `doom-prep/user-leads.md`.

`MEMORY.md` of scratch 2026-10-07: deleted.

## `galileo/os_concepts/main`

| Memory | Action | Target |
| --- | --- | --- |
| `user-implements-claude-reviews` | delete (copy verified at `.claude/CLAUDE.md`: Global rules that don't apply here) | "Implementing: don't write or finish the owner's code or prose (`src/`, `doc/`) unless asked" and "Committing: the owner commits." |
| `hidden-docs-location` | move | `.claude/CLAUDE.md`, a new "## Claude's notes" before "## How Claude helps here" |
| `deferred-failure-tests` | move | `.claude/hidden-docs/plan.md`, a new section after "Cache concurrency: deferred optimizations" |

> ## Claude's notes
>
> `.claude/hidden-docs/` holds Claude's notes, updated in place and copied nowhere else: `plan.md` (the series plan, the owner's roadmap of 2026-10-04 at the top), `review-NNNN-*.md` (a checklist per post: `[ ]` open, `[x]` done with its commit, `[~]` deferred), `real-world-context.md`, `workloads.md`, `design-notes.md` and `asides.md`.

> ## Cache flush: tests deferred until failure injection (user's decision, 2026-10-12)
>
> `Disk` cannot fail a valid request and its `flush` does nothing, so these wait for a test device that fails on demand and counts flushes. Offer them when it exists:
> - A write-back that fails during `flush` leaves the entry dirty, so a retry writes it.
> - `flush` reaches the device's `flush`.
> - A failed write-through leaves the entry dirty.
> - A request waiting on a `Busy` entry is woken when that entry's IO fails (beside the `concurrent` and `cancel` test modules in `cache.rs`).

`MEMORY.md`: deleted.

## `galileo/sofi/checklist` (Quiro)

The six memories sit in the folder of `~/devel/galileo/misc/quiro`, the project's old path. The project's own memory folder is empty.

| Memory | Action | Target or the line that holds it |
| --- | --- | --- |
| `user-oftalmologia` | delete (copy verified at `CLAUDE.md`, opening) | "Ayuda para las tareas de una residente/un residente de oftalmología." and "Las respuestas a la persona que usa Quiro también." |
| `feedback-publicar-es-del-dueno` | delete (copy verified at `CLAUDE.md`: Deploy, and `.claude/skills/deploy/SKILL.md`) | "Solo se deploya cuando el dueño lo pide" and "Entre deploys se commitea pero no se pushea." |
| `feedback-backup-before-deploy` | delete (copy verified at `.claude/skills/deploy/SKILL.md`) | "el \"backup antes de deployar\" es el JSON de Datos (Exportar JSON)" |
| `feedback-no-pisar-lo-cargado` | delete (copy verified at `CLAUDE.md`: Volver a cargar) | "Nunca se pisa nada sin confirmar." |
| `feedback-poder-confiar` | delete (copy verified at `CLAUDE.md`: Volver a cargar, and `docs/origen.md`) | "de dónde sale cada dato. El panel \"Origen\", la pestaña \"Originales\" y `origin` en cada fila." |
| `feedback-explicar-reglas-antes-de-commitear` | move | `CLAUDE.md`, "Cruce", after its first paragraph |

> Una regla del cruce nueva o cambiada (a quién va cada fila, qué se excluye, qué se avisa) se prueba contra los archivos de `samples/`, se explica lo que no es obvio y se muestra en pantalla antes de dar el trabajo por cerrado. El dueño da el visto bueno sobre la regla, y una corrección suya va en un commit nuevo.

`MEMORY.md` of `misc/quiro`: deleted.

## `iquall/misc/core5g`

| Memory | Action | Target |
| --- | --- | --- |
| `nix-is-local-only` | move | `CLAUDE.md`, "Publicar y operar sin romper nada", after "Dependencias" |

> - **Nix es de esta computadora.** El flake vive en `local/nix/` (gitignorado) y `.claude/launch.json` en `.git/info/exclude`. Se corre con `nix run path:./local/nix`, y nunca se commitea ni se pushea. Una dependencia nueva va a `viewer/requirements.txt`, que es lo que usa el equipo, y al flake local, con Python 3.13: con 3.12, al nixpkgs fijado, las dependencias de fastmcp no tienen caché binaria.

`MEMORY.md`: deleted.

## `iquall/misc/slides`

Two repositories: `typst-slides-lib` (the library, pushed to `gitlab.iquall.net`) and `typst-slides-decks` (the decks, the library as a submodule at `lib/`).

| Memory | Action | Target or the line that holds it |
| --- | --- | --- |
| `typst-slides-library` | delete (copy verified at `typst-slides-lib/CLAUDE.md`: Layout facts, and `typst-slides-decks/README.md`) | the memory says "it is the authoritative copy and this memory is the backup". Roboto Slab, `header-height`, python-pptx, `qlmanage` and `bullets(spacing:)` are all there |
| `decks-are-english-only` | delete (copy verified at `typst-slides-decks/CLAUDE.md`: Hard rules 2) | "**Decks are written in English.** Another language is a special case" |
| `prefers-reusable-over-pixel-match` | delete (copy verified at both CLAUDE.md: Hard rules 3) | "**Prefer a reusable component over a pixel-match.**" |
| `agent-fabric-drive-folder` | delete (copy verified at `typst-slides-decks/CLAUDE.md`, line 244) | the Drive URL, the connector calls, and Iquall's one row, "*Design-time Eval · pre-deployment validation · Trust Gateway*" |
| `asset-catalog-recreation` | delete (copy verified at `typst-slides-decks/README.md`: The asset catalog, and `typst-slides-lib/CLAUDE.md`: Gotchas) | "**Never name a component after a Typst built-in.**" and the promotion candidates `disc`, `wire` |
| `hackathon-handover-port` | delete | history. The library remote it records is in `typst-slides-lib/CLAUDE.md`: Repo state |
| `pdf-to-pptx-libreoffice` | move | `typst-slides-lib/export/README.md`, "Results", after the table, whose LibreOffice column it explains |
| `typst-to-pptx-backend` | move (the rest verified at `typst-slides-lib/CLAUDE.md`: The PPTX backend, and `export/README.md`: Limits) | `typst-slides-lib/export/README.md`, "Environment", one bullet |
| `tmforum-brand` | move (the brand verified at `typst-slides-lib/README.md`: TM Forum, Aptos, the 0.75 scale and sRGB) | `typst-slides-decks/CLAUDE.md`, "Repo state" |
| `no-global-installs-use-uv` | general rule 1 | |

`export/README.md`, "Results":

> The LibreOffice column is the PDF route, tried on 2026-07-31 on the 61-page DTW deck and rejected. LibreOffice opens a PDF only as a Draw document, which has no PPTX export, so it takes three hops: `--infilter=draw_pdf_import --convert-to odg`, the ODG made an ODP by hand (`mimetype` and `office:drawing` turned to presentation), then `--convert-to pptx`, and a pass setting `wrap="none"` and `<a:noAutofit/>` on every text body. The gradients shatter at the import, where nothing can fix them.

`export/README.md`, "Environment":

> - **The LibreOffice render check runs in Docker**, in the image `lo-impress-iquall`, whose Dockerfile sits outside the repository in `~/.cache/lo-impress-iquall`. It needs `colima start`, and colima is stopped afterwards. Colima does not mount `/private/tmp`, so files are staged under `$HOME`.

A Dockerfile the check depends on belongs in the repository, so moving it to `export/` is offered to the slides session.

`typst-slides-decks/CLAUDE.md`, "Repo state", after the sentence on bumping `lib/`:

> Before a bump, `git -C lib log` shows whether the checkout holds commits the library's `main` lacks (the PPTX export once did). Those go into the library first.

The same paragraph says "**No remote**, nothing has been pushed, on this repo or the library's", while the library's CLAUDE.md says it was pushed to `gitlab.iquall.net` on 2026-10-06. The slides session fixes the decks' sentence in the same commit.

`MEMORY.md`: deleted.

## `iquall/tagents/main`

| Memory | Action | Target or the line that holds it |
| --- | --- | --- |
| `feedback_dev_pushes_without_asking` | delete (copy verified at `CLAUDE.md`: §4 Rules in every worktree) | "The exceptions to the publishing rule: `dev` pushes its branch after every commit" |
| `feedback_demo_lane_pushes_tagents_demos` | delete (copy verified at the same line) | "`dev` and a demo lane commit to and push `tagents-demos` freely (owner, 2026-10-23 and 2026-11-04)" |
| `user_profile` | delete (copy verified at the global rules) | "Be critical" and "record the assumptions you made", and the memory itself defers to CLAUDE.md §4 |
| `feedback_titles_not_numbers` | delete (copy verified at the global rules) | "An id carries its name" |
| `feedback_every_page_and_table_basics` | delete (copy verified at `.claude/skills/frontend/SKILL.md`: §2 Every list, every record) | "A list has a `FilterBar`" and "Its `DataTable` carries `more={20}`" |
| `feedback_everything_in_the_kit` | delete (copy verified at `.claude/skills/demo/SKILL.md`: step 3) | "**Everything the demo needs goes into the kit as it is needed** (owner, 2026-10-28)" |
| `feedback_misc_lane_static_checks_yes_tests_no` | delete | the `work-misc` lane is gone, and `/session-kit:iterate` is the general form |
| `feedback_assign_lane_choice` | delete | stale: the desk assigns nothing |
| `feedback_desk_checks_assignment_fit` | delete | stale: the desk assigns nothing, and its step 2 names conflicts between objectives |
| `feedback_screenshots_of_changes` | move | `.claude/skills/frontend/SKILL.md`, §4 How the change is made, after the "Look at the page yourself" bullet |
| `feedback_agents_prompt_knowledge_skills` | move | `.claude/skills/demo/SKILL.md`, step 3, after the "Everything the demo needs" sentence |
| `feedback_targets_hold_on_a_busy_machine` | move | `docs/intent/O16-the-full-suite-fits-its-ten-minutes.md`, after "Known met when" |
| `feedback_diagrams_in_mermaid` | general rule 6 | |
| `feedback_batch_questions` | general rule 7 | |
| `user_company_spelling` | general rule 8 | |
| `feedback_sweep_touch_no_tells` | general rule 9 | |

Frontend skill, §4:

> - Every mocked or built change the owner can see goes to them unasked as screenshots of each place it touches, sent as files. They are taken in light mode (`resize_window` with `colorScheme: "light"`, and the console's own theme where it overrides the system's). Dark mode is looked at too when colours changed (owner, 2026-11-13 and 2026-11-17).

Demo skill, step 3:

> An agent's content has three homes, checked before its prompt grows: the prompt holds who it is and what holds on every turn, knowledge holds what it looks up, and a skill holds how one kind of task is done, shared when several agents need it (owner, 2026-10-16, after a 43 KB prompt broke a platform limit). A run shows the agent read what it was pointed at (its tool calls), and its answer is checked against the source.

`O16`, after "Known met when the verifier's full run on `dev` reports under 300 s with no test over its timeout.":

> The run counts on the machine as it is, with the lanes working: a run over target is reported unmet by its margin, whatever the load (owner, 2026-10-27).

`O16` is the owner's objective and tagents adds a rule on the owner's word alone, so approving this plan is that word for these three texts.

`MEMORY.md`: deleted.

## `iquall/twinlab`

`origin` is `gitlab.iquall.net:Iquall/innovation/twinlab-internal`, read by the team. The texts leave out the owner's own machine (its address and key), which stay out of a shared repository.

| Memory | Folder | Action | Target |
| --- | --- | --- | --- |
| `twinlab-vm-deployment` | `iquall/twinlab` | move | a new `docs/hosts.md`, "twinlab.iquall.net" |
| `llm-test-nginx-certbot` | scratch 2026-09-07 | move, and a decision for the owner | the same `docs/hosts.md`, "llm-test.iquall.net" |
| `twinlab-arm64-emulation-limits` | `iquall/twinlab/main` (gone as a folder) | move | `docs/dev-on-apple-silicon.md`, a new section at its end |

The new `docs/hosts.md`, whole:

> # Hosts
>
> ## twinlab.iquall.net (`ssh twinlab`)
>
> It runs the internal `mat` branch from `~/projects/twinlab/dev` (the directory's name is a leftover). OIDC (Google, slug `google`, limited to `iquall.net`) and the MCP server are on. The TAgents assistant and MAT sync stay unconfigured.
>
> The VM has about 8 GB of RAM, no swap and other people's labs, so it never builds an image. An upgrade:
>
> 1. Build on an x86_64 host with room: `docker compose -p twinlabvm build` from a `git archive origin/mat` export.
> 2. Ship the images with `docker save | gzip | ssh twinlab 'gunzip | docker load'`, then retag `twinlabvm-*` to `twinlab-*`. A binary stream is never filtered through grep.
> 3. Push the code under a new ref, since `origin/mat` is force-updated and the VM's branch is checked out: `git push twinlab-dev refs/remotes/origin/mat:refs/heads/mat-<sha>`, then `git checkout -B mat mat-<sha>` on the VM.
> 4. Before the restart, `select count(*) from jobs where status='running'` (a backend restart fails running jobs, while lab nodes are sibling containers and survive), and a `pg_dump` into `~/backups/`.
>
> A script that needs sudo is run by a person. `~/twinlab-upgrade2.sh` on the VM is the last upgrade script.
>
> The gateway in front of the VM passes HTTPS through to port 443, so nginx on the VM always listens on 443 (the snakeoil certificate is enough), or every request answers 502. No certbot runs there, and its nginx config is the host's, apart from the compose branch.
>
> ## llm-test.iquall.net (`ssh llm`)
>
> Debian 13. One HTTPS vhost, `sites-available/ollama.conf`, includes a fragment per app (`snippets/twinlab.conf`, `snippets/lab.conf`) and reads the `/api/ollama/` bearer token as a `map` from `secrets/ollama-token.conf` (root:root 0640). Certificates renew through `certbot-renew.timer`. Certbot lives in a pip venv at `/opt/certbot`, so its upgrades are manual.

`docs/dev-on-apple-silicon.md`, at its end:

> ## Measured: amd64 under qemu-user on colima
>
> With amd64 emulation from `tonistiigi/binfmt --install amd64`:
>
> - Cisco IOL (`vrnetlab/cisco_iol`) runs as `qemu-x86_64 /iol/iol.bin`. IOS-XE boots and its CLI works, but no packet crosses the data or management plane, so SSH, published ports and links between nodes fail. Only the console works: `docker attach clab-<lab>-<node>`, left with Ctrl-P Ctrl-Q, as Ctrl-C reaches the node.
> - The QEMU/KVM vrnetlab kinds (XRv9k, CSR, c8000v) run qemu-system in TCG inside an emulated container, which makes them unusable.
> - The VyOS amd64 container boots slowly, and its systemd stalls.
>
> This Mac builds images and checks a topology's syntax. A lab that passes traffic runs on an amd64 Linux host, where the bridge is routable, KVM is there and `ssh admin@clab-<lab>-<node>` works.

A line in twinlab's `CLAUDE.md` names `docs/hosts.md`, under "Working conventions".

For the owner, the Ollama token: the memory records that the `/api/ollama/` bearer token was moved on 2026-09-07 and never rotated, after it had been world-readable and had appeared in a session's transcript that day. It was held back because rotating it means updating every client of `/api/ollama/` at once. The memory's advice is to check the host first, as it may have been rotated since. This is a security item, and it is left out of the team's repository: where it is tracked is the owner's choice.

`MEMORY.md` of `iquall/twinlab`, `iquall/twinlab/main` and scratch 2026-09-07: deleted.
