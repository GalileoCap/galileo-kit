# claude-kit

Hooks and a skill for Claude Code that every project can use. It is a plugin marketplace (`galileo-kit`) holding one plugin (`session-kit`). Claude Code reserves plugin names starting with `claude-`, which is why the repository and the plugin are named differently.

## What `session-kit` does

| Piece | Event | What it does |
| --- | --- | --- |
| `context_pressure.py` | PostToolUse | Warns every 25k tokens once the context passes half the window, firmer past 65% and 80%. It never holds a tool call or the end of a turn. |
| `guard.py` | PreToolUse (Bash, Artifact) | Refuses `git commit --no-verify`, `git push --force` (not `--force-with-lease`), `git rebase -i`, `git reset --hard`, a bare `git stash` or `stash pop`, `-x` on a test run, shell `timeout` around a Bash call, test output piped inline to `grep`/`head`/`tail`, amending a commit already on a remote, and publishing an Artifact. |
| `nudge_single_edit.py` | PreToolUse (Bash) | A Python heredoc doing one read, one replace and one write is told to use the Edit tool. |
| `doc_length.py` | PostToolUse (Edit, Write) | Says so when a `docs/*.md` file passes 1500 lines. |
| `session-tells hook` | PostToolUse (Edit, Write, Bash) | Lists the banned prose tells on the lines an edit wrote, each with its fix, and counts the rest of the file's. Never blocks. Bash edits are read from the `bashEditDiff` Claude Code reports. |
| `format.py` | PostToolUse (Edit, Write, Bash) | Formats the files an edit wrote with the project's own tools, chosen by its config: ruff (`uv run ruff` beside a `uv.lock`), oxlint and biome (from `node_modules/.bin`). Passes on the lint the fix could not clear. |
| `test_log.py` | PostToolUse, PostToolUseFailure (Bash) | Keeps the last test run's whole output in `<tempdir>/claude-kit-last-test-<session>.log`, and on a failure says where it is. |
| `direnv_env.sh` | SessionStart, CwdChanged, FileChanged | Puts the project's direnv environment in front of every Bash command, with the plugin's `bin/` kept at the end of PATH. A project with no `.envrc` is left alone. |
| `pyright_env.py` | SessionStart | For a project whose `.claude/claude-kit.json` sets `"pyright_env": true`, writes the root `pyrightconfig.json` with `session-codeintel pyright-env`, one execution environment per uv package, and names any package it left out. Off by default, because it would replace a root config kept by hand. |
| `bin/session-tells`, `bin/session-codeintel` | Bash tool's PATH | The two packages below as commands, while the plugin is enabled. Each runs in the environment its hook uses, in `CLAUDE_PLUGIN_DATA`. |
| `handoff` skill | `/session-kit:handoff` | Writes `CLAUDE.local.md`, the working state a session reads first after a compaction. |

## Configuration

- `CLAUDE_KIT_CTX_WINDOW` (default 1000000), `CLAUDE_KIT_CTX_THRESHOLD` (0.50) and `CLAUDE_KIT_CTX_STEP` (25000) tune the context warnings. No API reports the window, so a session on a smaller one sets it.
- `CLAUDE_KIT_DOC_LINES` (1500) sets the doc-length warning.
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

  `guide` names the pages a product's users read, which the guide's own rules hold. `languages` maps a directory name to the language of the files under it (English otherwise; Spanish and Portuguese have their own rules). `history_codes` adds a project's own codes to the rule that treats an issue number in a comment as history. `commands` hands files to a reader of the project's own, which prints `{"units": [{"path", "text", "pieces"}]}`.

## The prose tells

`plugins/session-kit/tells/` is a Python package, `session-tells`: one rule per habit of machine-written prose (the em dash, `X, not Y`, negative parallelism, inflated vocabulary, intensifiers, signposting, history in comments and the rest), each with text it must fire on and a near miss it must leave alone. *Banned* rules are reported; *rationed* ones (`rather than`, semicolons, bold lead-ins) are fine once and a habit in bulk, so `show` lists them and the hook does not. A line carrying `tells: allow <rule>` allows that rule there.

```bash
session-tells show docs/a.md src/b.py   # every tell, with its fix
session-tells check docs/a.md           # the banned ones; exits 1 on any
```

In a session the plugin's `bin/` puts the command on PATH. Elsewhere it is `uv run --project plugins/session-kit/tells session-tells`. The files are read against the current directory, or `--root`, whose `.claude/claude-kit.json` applies; a file outside it is refused.

The hook runs it with `uv` (silent without it), its environment kept in `CLAUDE_PLUGIN_DATA`. TypeScript and Rust are read through tree-sitter, so no Node or Rust toolchain is needed.

## Install

```bash
claude plugin marketplace add https://github.com/GalileoCap/session-kit.git
claude plugin install session-kit@galileo-kit
```

Both default to user scope, so every project gets it. The install copies the plugin into `~/.claude/plugins/cache`, so a change reaches a machine only after a version bump in `plugin.json` and `claude plugin update session-kit@galileo-kit`, then the next session start or `/reload-plugins`.

A project that depends on the kit declares it in `.claude/settings.json`, so anyone opening it is asked to install it. The marketplace is added over HTTPS because Claude Code's own clone does not use SSH keys:

```json
{
  "extraKnownMarketplaces": {
    "galileo-kit": { "source": { "source": "git", "url": "https://github.com/GalileoCap/session-kit.git" } }
  },
  "enabledPlugins": { "session-kit@galileo-kit": true }
}
```

## Tests

```bash
python3 plugins/session-kit/hooks/test_guard.py
python3 plugins/session-kit/hooks/test_context_pressure.py
bash global/test_install.sh
bash plugins/session-kit/lib/test_uv_package.sh
bash plugins/session-kit/hooks/test_direnv_env.sh
python3 plugins/session-kit/hooks/test_format.py
python3 plugins/session-kit/hooks/test_test_log.py
plugins/session-kit/tells/scripts/check     # ruff ALL, basedpyright strict, zero warnings
plugins/session-kit/tells/scripts/test
claude plugin validate . && claude plugin validate plugins/session-kit --strict
```

The guard's cases live in a file because the guard matches the text of a command: a shell harness whose own arguments carry the patterns is denied by the rules it checks.

## Code intelligence

`plugins/session-kit/codeintel/` is a Python package, `session-codeintel`: pinned `ast-grep` and `import-linter`, tested rewrite recipes, `pyright-env` (a root `pyrightconfig.json` that lets a language server see every package of a multi-package repository), and a shim that starts a project's own language server through direnv. A project runs it from git at a pinned commit through a small wrapper; [its README](plugins/session-kit/codeintel/docs/README.md) has the wrapper and the rest.

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
