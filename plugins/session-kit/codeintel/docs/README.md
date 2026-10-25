# session-codeintel

Code intelligence for a repository of several Python packages: pinned
structural search and rewrite, import boundaries as a gate, and complete
"what uses this?" answers from a language server.

## What it does

- **Pins two tools, so every session runs the same ones.**
  [`ast-grep`](https://ast-grep.github.io/) for structural search and
  rewrite, and [`import-linter`](https://import-linter.readthedocs.io/)
  for import contracts. Both are runtime dependencies of this package,
  so running them through it gives the version its lock names, whatever
  is on `PATH`. A rule's test or a contract's verdict then means the
  same thing on every machine.
- **Ships tested rewrite recipes.** An ast-grep rule for a sweep that has
  gone wrong before, carrying the passes and guards that make it
  correct. The first one awaits every call site of a method that became
  `async`. It rewrites whole attribute chains, is idempotent on a
  half-converted tree, and documents the two ways a regex sweep of the
  same change breaks code. A recipe is a template: you copy it, retarget
  it and run it. It is never a check.
- **Finds a look written twice.** In a frontend built on utility
  classes, the same information shown the same way everywhere means one
  component or one looks entry per look, and `session-codeintel looks`
  fails when a class string of two or more classes is written in two
  places under the source. A look that repeats by coincidence is allowed
  in the project's settings with the files it lives in, and the check
  fails again when it spreads or leaves one, so the entry is reviewed.
- **Writes the `pyrightconfig.json` that makes a language server
  complete.** A server started at the root of a repository of several
  `uv` projects sees one interpreter, and answers "no references" for
  whatever lives in the other packages. `session-codeintel pyright-env`
  writes a root config with one execution environment per package: its
  sources, its path dependencies' sources, and its own venv's
  `site-packages`. Measured on one such repository, it took a reference
  search from 2 of 50 call sites to 50 of 50.

## What it does not do

- **It holds no contracts and no rules of yours.** An import contract
  names your modules, so it lives in your `pyproject.toml`.
  [`integrating.md`](integrating.md) gives the two shapes as templates.
  Gate rules for your own code are yours too. The recipes here are
  templates for one-off sweeps.
- **It does not wrap either tool.** `ast-grep` and `lint-imports` are
  run by their own documented CLIs. This package only fixes their
  versions.
- **It does not run a language server, or pin one.** It writes the
  server's configuration. The server comes from your toolchain, or from
  your editor, and [`operating.md`](operating.md) covers one way to make
  an agent start your toolchain's server.
- **It does not find call sites for a signature change.** Your
  typechecker does, per package, after the change. A language server
  answers "what depends on this?" before the change. The typechecker
  answers "what did I break?" after it. You want both.
- **It has no dataflow or control-flow analysis.** For a concurrency
  bug, read the code.

## What it depends on

- **Python 3.12 or newer**, and [`uv`](https://docs.astral.sh/uv/).
- **Two binaries, installed as wheels**: `ast-grep-cli` (MIT) and
  `import-linter` (BSD-2-Clause). Nothing to run as a service.
- **For `pyright-env`**: every package is an immediate subdirectory of
  the repository root, with its own `pyproject.toml` and its venv at
  `<package>/.venv`, which is where `uv sync` puts it. POSIX venv layout
  only.
- **For navigation**: a pyright-based language server of your choosing
  (`pyright`, `basedpyright`), and an editor or agent that speaks LSP.

## Install, and the smallest thing that works

It lives in the `session-kit` repository, at
`plugins/session-kit/codeintel/`, and is on no package index. A project
runs it from git at a pinned commit, through a wrapper of its own,
`scripts/codeintel`:

```sh
#!/bin/sh
# The pinned session-codeintel, and the ast-grep and import-linter it brings.
# To move the pin, change both lines in one commit.
rev=<commit>
date=<that commit's date, e.g. 2026-10-11T18:00:00Z>
exec uvx --quiet --exclude-newer "$date" \
    --from "session-codeintel @ git+https://github.com/GalileoCap/galileo-kit.git@$rev#subdirectory=plugins/session-kit/codeintel" \
    "$@"
```

The commit fixes the package, and `--exclude-newer` fixes everything it
resolves to what was published by that date, so every machine runs the
same `ast-grep` and `import-linter`. `uv` caches both, so only the first
run after a pin moves needs the network.

```bash
scripts/codeintel session-codeintel recipes list
scripts/codeintel ast-grep --version     # ast-grep 0.45.3
```

```text
api-migration-await-call	Await every call site of a method that went async: …
```

Complete navigation for a repository of packages, from its root:

```bash
(cd pkg-a && uv sync) && (cd pkg-b && uv sync)
scripts/codeintel session-codeintel pyright-env .
```

```text
pyrightconfig.json: 2 package(s)
```

With the `session-kit` plugin installed, `"pyright_env": true` in the project's
`.claude/claude-kit.json` runs this at every session start.

Add `/pyrightconfig.json` to `.gitignore`. The file names each venv's
`site-packages`, whose path carries the interpreter's minor version, so
it is right on one machine only. Then move each package's checker
settings into that package's own `pyrightconfig.json`
([`integrating.md`](integrating.md) explains why). Restart the language
server once the file is written.

## The pages

- [`integrating.md`](integrating.md): wiring it into a repository. The
  recipes, the contracts, the root config, and what the repository
  must not do.
- [`api.md`](api.md): the command line and the Python modules, with
  what is public and what is not.
- [`operating.md`](operating.md): regenerating the config, reaching the
  project's language server from an agent, and what each failure looks
  like.
- [`CHANGELOG.md`](CHANGELOG.md).
