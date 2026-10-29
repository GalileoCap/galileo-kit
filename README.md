# galileo-kit

Everything its owner works with agents through: the rules every session follows (`global/`), the tools and plugins sessions use, and the vetting of each third-party piece before it is installed. It is a plugin marketplace of the same name holding one plugin, `session-kit`, which keeps its name since the plugin is one piece of the kit.

`CLAUDE.md` at the root holds the repository's intent and rules of engagement, and `docs/` the record behind them: `docs/intent/` (goals, objectives, constraints and actions, one file each), `docs/PLAN.md`, the research on plugins and mods, the reviews of candidates and the analysis behind the port of the hooks to a mod.

## What `session-kit` does

| Piece | Event | What it does |
| --- | --- | --- |
| `kit.tsx` | the hooks module | The module the engine loads for the plugin, one per plugin. It calls the register of each concern below, one file each. |
| `band.tsx` | `ui.render` (AbovePrompt, TurnDuration) | Through `kit.tsx`. The band above the prompt: failures, the offer, the chain, the context figure past its threshold, the cold-cache timer and a usage window at 95%, each a bold label, figures and buttons. The line that closes a turn gets the context percent that turn ended at. |
| `pane.tsx` | `command.run` (`/kit`), `ui.render` (Pane) | Through `kit.tsx`. A pane on every surface with the context, the usage windows, the cache timer, the chain and its last stages, the handoff, the uncommitted files and the last test run. |
| `status.ts`, `lines.ts`, `options.ts` | none | The status line under the prompt (`ui.status`, written when its text changes), the pure formatters of the band, pane and status line, and the plugin options with the warning's trigger. |
| `context.tsx` | `tool.call`, `session.measure`, `session.compact`, `turn.complete` | Through `kit.tsx`. After every tool call it reads the engine's own context figure and, once the context passes 250,000 tokens (or a percent of the window, whichever comes first), adds a warning to the tool result every 25k tokens, firmer at 1.2 times the threshold and at 1.6 times it, a tier that rises being said at once. Past the threshold a band above the prompt shows the count to the person, with buttons that write the handoff and compact. It never holds a tool call or the end of a turn, and a failure in it leaves the call as it ran. The engine's own compaction, the one at its threshold, gets instructions to keep what a handoff keeps. With the `chain` option on, the model gets a `clear_point` tool: at a clear point it calls it with who takes the next step, and when that turn ends the module runs the handoff skill, compacts the context and submits a continue prompt, or stops after the compaction when the next step is the owner's, which the band says. It also gets a `new_task` tool for a prompt unrelated to the task in hand: the band then offers the handoff and a clear, or to keep going here, and sends the person's prompt again either way. |
| `guard.py` | PreToolUse (Bash, Artifact) | Refuses `git commit --no-verify`, `git push --force` (not `--force-with-lease`), `git rebase -i`, `git reset --hard`, a bare `git stash` or `stash pop`, `-x` on a test run, shell `timeout` around a Bash call, test output piped inline to `grep`/`head`/`tail`, amending a commit already on a remote, and publishing an Artifact. |
| `checkout.ts` | `prompt.context`, `turn.complete` | Through `kit.tsx`. At the start of a conversation and after a compaction, a context block tells the model when `CLAUDE.local.md` is missing or older than the last commit, with the handoff command to run. At the end of a turn of the main loop, one dim line tells the person how many uncommitted changes the tree holds and whether the handoff predates the last commit. Silent outside a git repository. |
| `suppressions.ts` | `tool.call` on `Edit` and `Write` | Through `kit.tsx`. After an edit that puts a suppression or a type escape into a source file (`noqa`, `type: ignore`, `pyright: ignore`, `@ts-ignore`, `@ts-expect-error`, `eslint-disable`, `oxlint-disable`, `biome-ignore`, `as any`, `as unknown as`), the model is told to write its reason beside it, on its line or the line above, and to regenerate the index with `session-suppressions index`. A marker the edit only moves, and prose files, are left alone. |
| `nudge.ts` | `tool.call` (Bash) | A Python heredoc doing one read, one replace and one write is told to use the Edit tool. In-process, through `kit.tsx`. |
| `doc_length.ts` | `tool.call` (Edit, Write) | Tells the model when a `docs/*.md` file it edited is past the cap (`docLines`, 1500), to split it. In-process, through `kit.tsx`. |
| `session-tells hook` | PostToolUse (Edit, Write, Bash) | Lists the banned prose tells on the lines an edit wrote, each with its fix, and counts the rest of the file's. Never blocks. Bash edits are read from the `bashEditDiff` Claude Code reports. |
| `format.py` | PostToolUse (Edit, Write, Bash) | Formats the files an edit wrote with the project's own tools, chosen by its config: ruff (`uv run ruff` beside a `uv.lock`), oxlint and biome (from `node_modules/.bin`). Passes on the lint the fix could not clear. |
| `test_log.ts` | `tool.call` (Bash) | Keeps the last test run's whole output in `<tempdir>/claude-kit-last-test-<session>.log`, and on a failure says where it is. In-process, through `kit.tsx`. |
| `direnv_env.sh` | SessionStart, CwdChanged, FileChanged | Puts the project's direnv environment in front of every Bash command, with the plugin's `bin/` kept at the end of PATH. A project with no `.envrc` is left alone. |
| `pyright_env.py` | SessionStart | For a project whose `.claude/claude-kit.json` sets `"pyright_env": true`, writes the root `pyrightconfig.json` with `session-codeintel pyright-env`, one execution environment per uv package, and names any package it left out. Off by default, because it would replace a root config kept by hand. |
| `bin/session-tells`, `bin/session-codeintel` | Bash tool's PATH | The two packages below as commands, while the plugin is enabled. Each runs in the environment its hook uses, in `CLAUDE_PLUGIN_DATA`. |
| `bin/session-intent` | Bash tool's PATH | `session-intent index` writes `docs/intent/INDEX.md`, the entries waiting on the owner first, `session-intent check` reads the record and the `CLAUDE.md` Intent block, one line per problem, `session-intent names` prints each entry's id and name, and `session-intent next <level>` claims the next id of a level under a lock, from a counter kept outside every checkout under `~/.claude/session-kit/intent/`, one per clone, so an id is never given twice. Standard library Python. |
| `bin/session-docs` | Bash tool's PATH | `session-docs check` fails on a markdown file under `docs/` that `CLAUDE.md` does not name, by its path or by a directory's above it (`docs/intent/`), and on a path it names that does not exist, fenced code aside. The directory and the indexes are settable under `docs` in `.claude/claude-kit.json`. Standard library Python. |
| `bin/session-rulebook` | Bash tool's PATH | Counts the words of what every turn loads (the user's `~/.claude/CLAUDE.md` and the project's `CLAUDE.md` with their `@path` imports, `.claude/rules/`, `CLAUDE.local.md`) and, apart, of the skills, each file listed, and fails when a group is over its budget: 7,500 and 16,000 words, or the project's own under `rulebook` in `.claude/claude-kit.json`. Standard library Python. |
| `bin/session-suppressions` | Bash tool's PATH | `session-suppressions list` prints every suppression in the tree's source files with the reason written beside it, `index` writes `docs/suppressions.md` for the owner's review, and `check` fails on a marker that cites no row (on its line or the line above) or a row the ledger lacks. The ledger is `docs/decisions.md`, the citation `decisions.md, <n>`, both settable under `suppressions` in `.claude/claude-kit.json`. Standard library Python. |
| `bin/session-watched` | Bash tool's PATH | `session-watched [--stall S] [--check S] [--warn] -- <command>` runs a command and decides every few minutes whether to go on: a run with no progress (CPU, a process starting or ending, output growing into a file) for five minutes is ended with its diagnostics (the process tree and a stack sample, under a directory it names) and exit 125, no verdict on the code, and with `--warn` it writes the diagnostics and goes on. The command sees `SESSION_WATCHED=1`. Bash. |
| `bin/session-owed` | Bash tool's PATH | `session-owed --since <ref> [--until <ref>] [--section <name>]` prints the entries `OWED.md` gained across a range of history, by section, the working file standing for `--until`, and fails on an entry the range removed. Standard library Python. |
| `bin/session-transcripts` | Bash tool's PATH | Reads the sessions' transcripts under `~/.claude/projects/` and prints tables: `list`, `session <id>`, `warnings` (each context warning and what followed), `cache` (the share read from the prompt cache, the cold sends), `compactions`, `hooks`, and `report`, which writes them under `docs/measurements/`. `--archive <dir>` reads a backup beside them, one `<project>/<id>.tar.xz` per session, in a stream. Counts and sizes, with no prompt and no answer in its output. Standard library Python. |
| `handoff` skill | `/session-kit:handoff` | Writes `CLAUDE.local.md`, the working state a session reads first after a compaction. |
| `iterate` skill | `/session-kit:iterate` | Fast-working mode while the owner iterates: the project's static legs (`iterate.static` in `.claude/claude-kit.json`) after each change and no test run, every report ending with what did not run, the mode kept in `CLAUDE.local.md` through a compaction, and the tests run once when the owner ends it or work is handed back. |

## Configuration

- The context warnings are the plugin's options `thresholdTokens` (250000, where the warning starts, and 0 turns it off), `threshold` (percent of the window, 0, the alternative, and with both set the first reached warns) and `step` (tokens between warnings, 25000), set in `/config` under the plugin or in `settings.json` under `pluginConfigs`. The window is the engine's own figure for the session's model. The first transcript report put the owner's manual compactions at a median of 152,000 tokens over 39 sessions (`docs/measurements/sessions-2026-10-25.md`), a sample of the sessions kept, and the owner set the default above it, since a compaction costs the re-reads and the cache that follow it.
- `statusLine` (on) keeps a line under the prompt with the context figure, each usage window and when the cold-cache timer compacts. Off, the band draws a usage window from 80% instead of 95%.
- `chain` (off) turns on the two tools: `clear_point`, with the handoff, compaction and continue that run when the turn it was called in ends, and `new_task`, with the band's offer of the handoff and a clear. The continue prompt reaches the model as the plugin's, telling it to read again the documents `CLAUDE.local.md` lists and take its next step. An interrupted turn cancels the chain.
- `docLines` (1500) is the cap past which a `docs/*.md` file an edit touched is named to the model.
- A project names its suppressions index in `.claude/claude-kit.json` under `suppressions`: `index` (`docs/suppressions.md`) and `skip` (directories beyond the usual build and dependency ones). Its intent record goes under `intent`: `directory` (`docs/intent`) and `levels`, each with `letter`, `word`, `from`, `statuses`, `waiting` and `ask`, `fields`, `listed`, `place` and `needs_child_when`, the four levels of the process by default.
- A project sets its documents check in `.claude/claude-kit.json` under `docs`: `root` (`docs`) and `indexes`, the files that must each name every document (`CLAUDE.md`). Its looks check goes under `looks`: `src` (`src`), `skip` (`src/components/ui`) and `allowed`, the looks that repeat by coincidence, each with `look`, `files` and `reason`. Its layers go under `layers`: `python` (`core`, `shell`, `source`, `unwinds`), `typescript` (`core`, `effects`, `outside`) and `swift` (`core`, `shell`, `tests`, `core_module`, `source`), with `rules` and `tests` for the ast-grep directories. Its measured areas go under `measure.areas`, each with `name`, `path`, `skip` and `extensions`. Its quality gates go under `quality`: `areas` (each with `name`, `path` and `skip`), `ledger` (`quality-ledger.toml`), `max_code_lines` (500), `long` (a file whose cap is raised or lifted, each with `file`, `cap` and `reason`) and `protocols_from`. Its owed file goes under `owed` as `file` (`OWED.md`).
- A project sets its rulebook budgets in `.claude/claude-kit.json` under `rulebook`: `rules` and `skills` in words, and `skills_from`, globs from the root of further skill files (the kit names `plugins/*/skills/*/SKILL.md`).
- A project names its static legs in `.claude/claude-kit.json` under `iterate.static`, the commands the iterate skill runs after each change, each a gate that runs no test.
- A project names its own test runners in `.claude/claude-kit.json`, so the `-x` and piped-output rules and the test log cover them:

  ```json
  { "test_commands": ["scripts/test", "scripts/check"] }
  ```

- `"pyright_env": true` in the same file turns on the root `pyrightconfig.json` for a repository of several uv packages, each an immediate subdirectory with its own `.venv`.
- The prose tells read Markdown everywhere. The same file's `tells` key turns on the rest, every key optional (the full shape is in `tells/src/session_tells/config.py`):

  ```json
  {
    "tells": {
      "readers": ["python", "typescript", "rust"],
      "guide": ["docs/guide/"],
      "languages": {"es-419": "es", "pt-BR": "pt"},
      "history_codes": "\\bJIRA-\\d+\\b",
      "commands": [{"under": "web/", "run": ["node", "scripts/prose.ts"], "suffixes": [".ts"]}]
    }
  }
  ```

  `guide` names the pages a product's users read, which the guide's own rules hold. `languages` maps a directory name to the language of the files under it (English otherwise, and Spanish and Portuguese have their own rules). `history_codes` adds a project's own codes to the rule that treats an issue number in a comment as history. `commands` hands files to a reader of the project's own, which prints `{"units": [{"path", "text", "pieces"}]}`.

## The prose tells

`plugins/session-kit/tells/` is a Python package, `session-tells`: one rule per habit of machine-written prose (the em dash, `X, not Y`, negative parallelism, inflated vocabulary, intensifiers, signposting, history in comments and the rest), each with text it must fire on and a near miss it must leave alone. *Banned* rules are reported. *Rationed* ones (`rather than`, semicolons, bold lead-ins) are fine once and a habit in bulk, so `show` lists them and the hook does not. A line carrying `tells: allow <rule>` allows that rule there.

```bash
session-tells show docs/a.md src/b.py   # every tell, with its fix
session-tells check docs/a.md           # the banned ones; exits 1 on any
```

In a session the plugin's `bin/` puts the command on PATH. Elsewhere it is `uv run --project plugins/session-kit/tells session-tells`. The files are read against the current directory, or `--root`, whose `.claude/claude-kit.json` applies. A file outside it is refused.

The hook runs it with `uv` (silent without it), its environment kept in `CLAUDE_PLUGIN_DATA`. TypeScript and Rust are read through tree-sitter, so no Node or Rust toolchain is needed.

## Install

```bash
claude plugin marketplace add https://github.com/GalileoCap/galileo-kit.git
claude plugin install session-kit@galileo-kit
```

It defaults to user scope, so every project gets it. The install copies the plugin into `~/.claude/plugins/cache`, so a change reaches a machine only after a version bump in `plugin.json` and `claude plugin update session-kit@galileo-kit`, then the next session start or `/reload-plugins`.

A project that depends on the kit declares it in `.claude/settings.json`, so anyone opening it is asked to install it. The marketplace is added over HTTPS because Claude Code's own clone does not use SSH keys:

```json
{
  "extraKnownMarketplaces": {
    "galileo-kit": { "source": { "source": "git", "url": "https://github.com/GalileoCap/galileo-kit.git" } }
  },
  "enabledPlugins": { "session-kit@galileo-kit": true }
}
```

## Tests

```bash
python3 plugins/session-kit/hooks/test_guard.py
bash global/test_install.sh
bash plugins/session-kit/lib/test_uv_package.sh
bash plugins/session-kit/hooks/test_direnv_env.sh
python3 plugins/session-kit/hooks/test_format.py
plugins/session-kit/tells/scripts/check     # ruff ALL, basedpyright strict, zero warnings
plugins/session-kit/tells/scripts/test
claude plugin validate . && claude plugin validate plugins/session-kit --strict
claude plugin test plugins/session-kit            # the hooks module's tests, against the engine itself
python3 plugins/session-kit/intent/test_session_intent.py
python3 plugins/session-kit/transcripts/test_session_transcripts.py
python3 plugins/session-kit/rulebook/test_session_rulebook.py
python3 plugins/session-kit/docs_check/test_session_docs.py
python3 plugins/session-kit/owed/test_session_owed.py
bash plugins/session-kit/lib/test_watched.sh
plugins/session-kit/bin/session-intent check      # the record under docs/intent, and INDEX.md current
plugins/session-kit/bin/session-suppressions check   # every suppression in the kit's code has its reason, and docs/suppressions.md is current
plugins/session-kit/bin/session-rulebook             # the rules and the skills under their word budgets
plugins/session-kit/bin/session-docs check           # every document under docs/ named by CLAUDE.md
python3 plugins/session-kit/hooks/time_hooks.py   # what the settings hooks add to a tool call, see docs/measurements/hook-times.md
```

After the checkout is moved or renamed, `uv sync --reinstall` in each package rewrites its venv's scripts, whose first line carries the old path.

The hooks module is type-checked against the declarations the engine writes when it loads a mod (`.claude-plugin/types/`, ignored by git), or against the `claude-code.d.ts` the `plugin-authoring` skill lays out, with the `tsconfig.json` from that file's header kept outside the plugin:

```bash
nix-shell -p typescript --run "tsc -p <that tsconfig>"
```

The guard's cases live in a file because the guard matches the text of a command: a shell harness whose own arguments carry the patterns is denied by the rules it checks.

## Code intelligence

`plugins/session-kit/codeintel/` is a Python package, `session-codeintel`: pinned `ast-grep`, `ruff` and `import-linter`, tested rewrite recipes, `looks` (a class string written in two places under a frontend's source, with an allowlist that names each coincidence's files), `layers` (the pure-core gate written from the project's settings: eleven ast-grep rules with their tests (four of them for Swift) and the Python core's `ruff.toml`), `measure` (size, complexity and repeated looks per area and per git ref, written under `docs/measurements/`), `quality` (the duplicate gate, the fallback finder and the file-length lint over the project's Python, each site judged in `quality-ledger.toml`, a ledger that only shrinks), `template` (the quality bar as three base files a project's `pyproject.toml`, `pyrightconfig.json` and `scripts/check` extend, with `new`, `refresh` and `check`, which the kit's own two packages take), `pyright-env` (a root `pyrightconfig.json` that lets a language server see every package of a multi-package repository), and a shim that starts a project's own language server through direnv. A project runs it from git at a pinned commit through a small wrapper. [Its README](plugins/session-kit/codeintel/docs/README.md) has the wrapper and the rest.

```bash
plugins/session-kit/codeintel/shims/install.sh    # the shim, linked into ~/.local/bin under both servers' names; run it from a checkout, such as ~/.claude/plugins/marketplaces/galileo-kit
plugins/session-kit/codeintel/scripts/check       # its gate
plugins/session-kit/codeintel/scripts/test        # its tests
```

## Global instructions

`global/CODE.md` holds the rules about the shape of code, for a project that takes the pure-core shape: it names the file in its `CLAUDE.md` with an `@` line, and `session-codeintel layers` writes the gate behind the first rule.

A plugin cannot ship a `CLAUDE.md`, so the rules that belong in every project live in `global/CLAUDE.md`, and a script adds the line that imports them, `@<path>/global/CLAUDE.md`, to `~/.claude/CLAUDE.md`:

```bash
global/install.sh          # add the import (config dir: $CLAUDE_CONFIG_DIR, else ~/.claude)
global/install.sh --check  # say what the state is, change nothing
```

The file stays yours: a missing one is written with the line alone, an existing one gains the line at its end, and the rest of it holds this machine's own rules. Where the file is a link to `global/CLAUDE.md`, the script swaps it for a file holding the line, and a link to anything else is left alone with the line printed. The import names the working copy, so `git pull` there updates the rules. The cases are in `global/test_install.sh`.

`global/RATIONALE.md` holds the reason behind each rule, under the same headings. It is not linked or loaded: a session opens it when a rule looks arbitrary, and the rules work without it.

`global/goals-objectives-actions.md` is the process behind the rule that every kept decision has an entry under a project's `docs/intent/`, and `global/goals-objectives-actions-prior-art.md` sets it against the ideas it borrows from. Both are read on demand, like `RATIONALE.md`.
