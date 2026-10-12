# Operating session-codeintel

Nothing here runs as a service. What an operator has to know is how the
generated config is kept current, how an agent reaches the project's own
language server, and what each failure looks like from outside.

## Keeping the root config current

`pyright-env` is cheap: it reads a few small files per package, in well
under a second. So run it whenever the set of venvs may have changed,
rather than trying to detect the change:

- **When a session or editor starts.** For an agent, that is a
  session-start hook. Claude Code, for example, runs a `SessionStart`
  hook from its settings.
- **After `uv sync`** in any package, and after adding a package.
- **Never in CI.** A CI job runs each package's checker from inside the
  package, under that package's own `pyrightconfig.json`, and has no
  language server to feed.

Run it where the project's toolchain is on `PATH`, so `uv` is the
version the project pins. **Report its exit status; never block on
it.** Exit 1 means the file was written, and a package without a venv
was left out. Stopping a session over one package nobody has synced yet
would switch navigation off for all the others. Pass the stderr lines
through, since each one names a directory and the fix.

A server started before the file changed keeps its old view. Restart it.
The command leaves an unchanged file untouched, so running it again
doesn't restart anything.

## Reaching the project's language server from an agent

An editor or agent that starts language servers from **its own
`PATH`**, not the project's, runs whatever server it finds there. That
server is often none, or an old one. `shims/language-server` bridges the
gap by running the project's server through the project's own
environment:

```sh
exec direnv exec "${CLAUDE_PROJECT_DIR:-$PWD}" "$name" "$@"
```

It needs [direnv](https://direnv.net/), and the project needs an
`.envrc` that puts the server on `PATH`, such as a nix flake's
`use flake` or a `PATH_add` of a `node_modules/.bin`.

**Install it once per machine**, under the server's own name, in a
directory on the agent's `PATH`. The shim ships in this package's source
tree only:

```bash
plugins/session-kit/codeintel/shims/install.sh          # from a session-kit checkout
plugins/session-kit/codeintel/shims/install.sh --check  # say what is there, change nothing
direnv allow .          # once per project checkout: direnv's own trust model
```

The script links both names in `~/.local/bin` (or `$CODEINTEL_BIN`) to the
shim, so a pull of the checkout updates them. Claude Code's clone of the
marketplace, `~/.claude/plugins/marketplaces/galileo-kit/`, is such a
checkout, and `claude plugin marketplace update` pulls it. The plugin's
cache is not: each version gets a directory of its own, and an update
leaves links into the old one dangling. A name already holding a copy
of the shim is replaced by the link; a name holding anything else is left
alone and named, with exit 2.

It works out which server to start from its own file name, so one file
serves every server. It finds the project through `CLAUDE_PROJECT_DIR`
when the agent sets it, and otherwise from the directory the server was
started in. Claude Code sets the variable, and starts servers in the
project root. Both were measured by logging from the shim inside the
desktop app.

**Under `typescript-language-server` it changes one option.** The server
starts two tsservers by default, the second a syntax-only one that
answers sooner while a person types. An agent never types, so the shim
adds `useSyntaxServer: "never"` to the `initialize` request's
`initializationOptions`, the only place the server reads it from, and
passes every other byte through untouched. One tsserver per project
instead of two: 90–110 MB less each, measured on a 2 600-file console.


### One agent's wiring: Claude Code

Claude Code's official `pyright-lsp` and `typescript-lsp` plugins start
`pyright-langserver --stdio` and `typescript-language-server --stdio`,
which are the two shims above. Three things about them were measured:

- **Enabling a plugin in the project's `.claude/settings.json` does not
  install it.** The marketplace is registered, and the tool never
  appears. Install it explicitly, from the checkout:

  ```bash
  claude plugin install pyright-lsp@claude-plugins-official --scope project
  claude plugin install typescript-lsp@claude-plugins-official --scope project
  ```

- **An install is recorded against the directory it ran in.** Each
  checkout, `git worktree` included, needs its own install.
- **The install rewrites `.claude/settings.json`.** Among other things,
  it turns `\uXXXX` escapes into raw characters. If the file is tracked
  and had no edits of its own, check it out again afterwards.

## Failure modes

| What you see | What it means | Recovery |
| --- | --- | --- |
| A reference search returns only the declaration | The server is still indexing. It answers at once, with what it has so far. | Ask again after a few seconds. |
| A reference search is complete in one package and misses call sites in another | That package is not in the config. It had no venv when `pyright-env` ran, and stderr named it. | `uv sync` in the package, run `pyright-env` again, restart the server. |
| Standard-library names are unknown to the server (`from datetime import UTC` is an error) | The config has no top-level `pythonVersion`, so the server read the standard library at the version of whatever `python3` it found. | Regenerate the config with this package. Never hand-write the file. |
| A package's own checker, run inside it, reports a hundred errors that were not there before | The package keeps its checker settings in `pyproject.toml`, and the root file overrides them. `pyright-env` named it and exited 1. | Move the settings into `<package>/pyrightconfig.json`. |
| The server's diagnostics disagree with the checker in your gate | They are different checkers. A pyright server and a basedpyright gate, for example, read some types differently. | Trust the gate. The server is for navigation. |
| The shim fails: `<name>: the project's toolchain has no <name>`, exit 127 | The project's environment has no such server, or the project has no `.envrc`, so the shim found itself again. | Put the server in the project's environment. |
| The shim fails: `direnv: error … .envrc is blocked`, exit 1 | This checkout's `.envrc` was never allowed. | `direnv allow` in the checkout. |
| An agent has no language-server tool at all | For Claude Code: the plugins are enabled and not installed in this directory. | The install above, from the checkout, then a new session. |
| `lint-imports` fails: `No matches for ignored import …` | An `ignore_imports` line outlived the import it covered. | Delete the line. The contract got stricter by itself. |

## What it logs

Only the lines in [`api.md`](api.md): one summary line on stdout, one
line per problem on stderr. There is nothing to alert on. The shim sets
`DIRENV_LOG_FORMAT=` so that direnv's per-load messages stay out of the
server's stderr, which an LSP client may treat as the server's log.
direnv's errors still print.
