# claude-kit

Hooks and a skill for Claude Code that every project can use. It is a plugin marketplace (`galileo-kit`) holding one plugin (`session-kit`). Claude Code reserves plugin names starting with `claude-`, which is why the repository and the plugin are named differently.

## What `session-kit` does

| Piece | Event | What it does |
| --- | --- | --- |
| `context_pressure.py` | PostToolUse, Stop | Warns every 25k tokens once the context passes half the window, firmer past 65% and 80%. A turn that ends over half the window without saying whether it is safe to compact is held once and asked for `CLAUDE.local.md` and that line. |
| `guard.py` | PreToolUse (Bash, Artifact) | Refuses `git commit --no-verify`, `git push --force` (not `--force-with-lease`), `git rebase -i`, `git reset --hard`, a bare `git stash` or `stash pop`, `-x` on a test run, shell `timeout` around a Bash call, test output piped inline to `grep`/`head`/`tail`, amending a commit already on a remote, and publishing an Artifact. |
| `nudge_single_edit.py` | PreToolUse (Bash) | A Python heredoc doing one read, one replace and one write is told to use the Edit tool. |
| `doc_length.py` | PostToolUse (Edit, Write) | Says so when a `docs/*.md` file passes 1500 lines. |
| `direnv_env.sh` | SessionStart, CwdChanged, FileChanged | Puts the project's direnv environment in front of every Bash command. A project with no `.envrc` is left alone. |
| `handoff` skill | `/session-kit:handoff` | Writes `CLAUDE.local.md`, the working state a session reads first after a compaction. |

## Configuration

- `CLAUDE_KIT_CTX_WINDOW` (default 1000000), `CLAUDE_KIT_CTX_THRESHOLD` (0.50) and `CLAUDE_KIT_CTX_STEP` (25000) tune the context warnings. No API reports the window, so a session on a smaller one sets it.
- `CLAUDE_KIT_DOC_LINES` (1500) sets the doc-length warning.
- A project names its own test runners in `.claude/claude-kit.json`, so the `-x` and piped-output rules cover them:

  ```json
  { "test_commands": ["scripts/test", "scripts/check"] }
  ```

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
claude plugin validate . && claude plugin validate plugins/session-kit --strict
```

The guard's cases live in a file because the guard matches the text of a command: a shell harness whose own arguments carry the patterns is denied by the rules it checks.

## Not here yet

Global instructions. A plugin cannot ship a `CLAUDE.md`, so the rules that belong in `~/.claude/CLAUDE.md` need another route (a script that links the file, or a SessionStart hook that adds the text as context).
