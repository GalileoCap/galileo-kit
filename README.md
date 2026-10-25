# galileo-kit

Everything its owner works with agents through: the rules every session follows (`global/`), the tools and plugins sessions use, and the vetting of each third-party piece before it is installed. It is a plugin marketplace of the same name holding one plugin, `session-kit`, which keeps its name: the plugin is one piece of the kit.

`CLAUDE.md` at the root holds the repository's intent and rules of engagement, and `docs/` the record behind them: `docs/intent/` (goals, objectives, constraints and actions, one file each), `docs/PLAN.md`, the research on plugins and mods, the reviews of candidates and the analysis behind the port of the hooks to a mod.

## What `session-kit` does

| Piece | Event | What it does |
| --- | --- | --- |
| `kit.tsx` | the hooks module | The module the engine loads for the plugin, one per plugin. It calls the register of each concern below, one file each. |
| `context.tsx` | `tool.call`, `session.measure`, `session.compact`, `turn.complete`, `ui.render` | Through `kit.tsx`. After every tool call it reads the engine's own context figure and, once the context passes half the window, adds a warning to the tool result every 25k tokens, firmer past 65% and 80%. Past the threshold a band above the prompt shows the figure to the person. It never holds a tool call or the end of a turn, and a failure in it leaves the call as it ran. The engine's own compaction, the one at its threshold, gets instructions to keep what a handoff keeps. With the `chain` option on, the model gets a `clear_point` tool: at a clear point it calls it with who takes the next step, and when that turn ends the module runs the handoff skill, compacts the context and submits a continue prompt, or stops after the compaction when the next step is the owner's, which the band says. It also gets a `new_task` tool for a prompt unrelated to the task in hand: the band then offers the handoff and a clear, or to keep going here, and sends the person's prompt again either way. |
| `guard.py` | PreToolUse (Bash, Artifact) | Refuses `git commit --no-verify`, `git push --force` (not `--force-with-lease`), `git rebase -i`, `git reset --hard`, a bare `git stash` or `stash pop`, `-x` on a test run, shell `timeout` around a Bash call, test output piped inline to `grep`/`head`/`tail`, amending a commit already on a remote, and publishing an Artifact. |
| `nudge.ts` | `tool.call` (Bash) | A Python heredoc doing one read, one replace and one write is told to use the Edit tool. In-process, through `kit.tsx`. |
| `doc_length.ts` | `tool.call` (Edit, Write) | Tells the model when a `docs/*.md` file it edited is past the cap (`docLines`, 1500), to split it. In-process, through `kit.tsx`. |
| `session-tells hook` | PostToolUse (Edit, Write, Bash) | Lists the banned prose tells on the lines an edit wrote, each with its fix, and counts the rest of the file's. Never blocks. Bash edits are read from the `bashEditDiff` Claude Code reports. |
| `format.py` | PostToolUse (Edit, Write, Bash) | Formats the files an edit wrote with the project's own tools, chosen by its config: ruff (`uv run ruff` beside a `uv.lock`), oxlint and biome (from `node_modules/.bin`). Passes on the lint the fix could not clear. |
| `test_log.ts` | `tool.call` (Bash) | Keeps the last test run's whole output in `<tempdir>/claude-kit-last-test-<session>.log`, and on a failure says where it is. In-process, through `kit.tsx`. |
| `direnv_env.sh` | SessionStart, CwdChanged, FileChanged | Puts the project's direnv environment in front of every Bash command, with the plugin's `bin/` kept at the end of PATH. A project with no `.envrc` is left alone. |
| `pyright_env.py` | SessionStart | For a project whose `.claude/claude-kit.json` sets `"pyright_env": true`, writes the root `pyrightconfig.json` with `session-codeintel pyright-env`, one execution environment per uv package, and names any package it left out. Off by default, because it would replace a root config kept by hand. |
| `bin/session-tells`, `bin/session-codeintel` | Bash tool's PATH | The two packages below as commands, while the plugin is enabled. Each runs in the environment its hook uses, in `CLAUDE_PLUGIN_DATA`. |
| `bin/session-intent` | Bash tool's PATH | `session-intent index` writes `docs/intent/INDEX.md`, the entries waiting on the owner first, and `session-intent check` reads the record and the `CLAUDE.md` Intent block, one line per problem. Standard library Python. |
| `handoff` skill | `/session-kit:handoff` | Writes `CLAUDE.local.md`, the working state a session reads first after a compaction. |

## Configuration

- The context warnings are the plugin's options `threshold` (percent of the window, 50) and `step` (tokens between warnings, 25000), set in `/config` under the plugin or in `settings.json` under `pluginConfigs`. The window is the engine's own figure for the session's model.
- `chain` (off) turns on the two tools: `clear_point`, with the handoff, compaction and continue that run when the turn it was called in ends, and `new_task`, with the band's offer of the handoff and a clear. The continue prompt reaches the model as the plugin's, telling it to read again the documents `CLAUDE.local.md` lists and take its next step. An interrupted turn cancels the chain.
- `docLines` (1500) is the cap past which a `docs/*.md` file an edit touched is named to the model.
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

Both default to user scope, so every project gets it. The install copies the plugin into `~/.claude/plugins/cache`, so a change reaches a machine only after a version bump in `plugin.json` and `claude plugin update session-kit@galileo-kit`, then the next session start or `/reload-plugins`.

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
plugins/session-kit/bin/session-intent check      # the record under docs/intent, and INDEX.md current
python3 plugins/session-kit/hooks/time_hooks.py   # what the settings hooks add to a tool call, see docs/measurements/hook-times.md
```

The hooks module is type-checked against the declarations the engine writes when it loads a mod (`.claude-plugin/types/`, ignored by git), or against the `claude-code.d.ts` the `plugin-authoring` skill lays out, with the `tsconfig.json` from that file's header kept outside the plugin:

```bash
nix-shell -p typescript --run "tsc -p <that tsconfig>"
```

The guard's cases live in a file because the guard matches the text of a command: a shell harness whose own arguments carry the patterns is denied by the rules it checks.

## Code intelligence

`plugins/session-kit/codeintel/` is a Python package, `session-codeintel`: pinned `ast-grep` and `import-linter`, tested rewrite recipes, `pyright-env` (a root `pyrightconfig.json` that lets a language server see every package of a multi-package repository), and a shim that starts a project's own language server through direnv. A project runs it from git at a pinned commit through a small wrapper. [Its README](plugins/session-kit/codeintel/docs/README.md) has the wrapper and the rest.

```bash
plugins/session-kit/codeintel/shims/install.sh    # the shim, linked into ~/.local/bin under both servers' names; run it from a checkout, such as ~/.claude/plugins/marketplaces/galileo-kit
plugins/session-kit/codeintel/scripts/check       # its gate
plugins/session-kit/codeintel/scripts/test        # its tests
```

## Global instructions

A plugin cannot ship a `CLAUDE.md`, so the rules that belong in every project live in `global/CLAUDE.md` and are linked into `~/.claude/CLAUDE.md` by a script:

```bash
global/install.sh          # link it (config dir: $CLAUDE_CONFIG_DIR, else ~/.claude)
global/install.sh --check  # say what the state is, change nothing
```

It never replaces a file. If `~/.claude/CLAUDE.md` already exists, it is left alone and the script prints the line to add to it, `@<path>/global/CLAUDE.md`, which imports the kit's text. Because the install is a link, `git pull` in the kit's working copy updates the rules. The cases are in `global/test_install.sh`.

`global/RATIONALE.md` holds the reason behind each rule, under the same headings. It is not linked or loaded: a session opens it when a rule looks arbitrary, and the rules work without it.

`global/goals-objectives-actions.md` is the process behind the rule that every kept decision has an entry under a project's `docs/intent/`, and `global/goals-objectives-actions-prior-art.md` sets it against the ideas it borrows from. Both are read on demand, like `RATIONALE.md`.
