# Changelog

This package's own line, in [semver](https://semver.org/). Its versions
move independently of any repository that uses it. A breaking change to
the command line, which is the public surface in [`api.md`](api.md), is
a major bump, and its entry says what a consumer has to change. Before
1.0, a minor bump may break.

## 0.7.0, 2026-10-26

- `footprint [ROOT] [--write] [--claude PATH]`: each plugin's reach
  as `claude plugin validate` reports it, held in its `footprint.toml`
  with a reason per `$` member and per hook event, so a new call or hook
  fails until its reason is written ([`api.md`](api.md)). The engine is
  the session's own unless named.

## 0.6.0, 2026-10-25

- `quality [ROOT] [--report]`: the duplicate gate, the fallback
  ledger and the file-length lint over `quality.areas`, with the ledger
  in `quality-ledger.toml` ([`api.md`](api.md)). The gates are
  tagents-quality's, read on the syntax tree, without its code map.
- `template new | refresh | check`: the quality bar as three base
  files a project's `pyproject.toml`, `pyrightconfig.json` and
  `scripts/check` extend, with the check that a copy has not drifted
  ([`api.md`](api.md)). abstract-template's Python kind, without copier.
  This package and `session-tells` take it.
- The settings file's JSON guards live in one module, `settings.py`,
  which the duplicate gate asked for on its first run over the kit.

## 0.5.0, 2026-10-25

- `measure [ROOT]`: size, complexity and repeated looks per area and
  per snapshot (`--at REF`, a `git archive` each), the Python complexity
  from ruff's `C901`, now a runtime dependency pinned like the other
  tools, and the TypeScript complexity counted with ast-grep
  ([`api.md`](api.md)). The counts are the ones behind generic-app's
  impact report, whose scripts are kept under the kit's `docs/analyses/`.

## 0.4.0, 2026-10-25

- `layers [ROOT]`: the pure-core gate written from the `layers`
  block of `.claude/claude-kit.json`: seven ast-grep rules with a test
  each, the core's `ruff.toml` and an `sgconfig.yml`, each file headed
  by the command and never replacing one it did not write
  ([`api.md`](api.md)). The rules are generic-app's, with the paths
  taken from the settings and the TypeScript core's ESLint block
  rewritten as an ast-grep rule.

## 0.3.0, 2026-10-25

- `looks [ROOT]`: the class strings of two or more classes written in
  more than one place under a frontend's source, found by three
  ast-grep rules through the pinned binary, with an allowlist in
  `.claude/claude-kit.json` that names each coincidence's files
  ([`api.md`](api.md)). Ported from generic-app's TypeScript checker.

## 0.2.0, 2026-10-11

- Moved into `session-kit` (`plugins/session-kit/codeintel/`) and
  renamed `session-codeintel`: the package `session_codeintel` and the
  command `session-codeintel`. Its history before the move is in the
  repository it came from, as `abstract-codeintel`.
- Run from git at a pinned commit: a consumer's wrapper runs
  `uvx --from` the commit, with `--exclude-newer` at the commit's date so
  every machine resolves the same versions ([`README.md`](README.md)).
- `shims/install.sh` puts the shim on `PATH` under both servers'
  names, and never replaces a file it did not write.

## 0.1.0a0


The first version.

- `recipes list` and `recipes path <name>`, over one bundled recipe:
  `api-migration-await-call`, which awaits every call site of a method
  that went `async`. It works on whole attribute chains, and is
  idempotent on a half-converted tree. Tested through the pinned
  `ast-grep`: the rewrite, the re-run, and a longer attribute chain
  rewritten whole, from its first segment.
- `pyright-env [ROOT]`, which writes a root `pyrightconfig.json` with
  one execution environment per package that has a venv. Each
  environment's `extraPaths` are its sources, its path dependencies'
  sources and its venv's `site-packages`, and the top-level
  `pythonVersion` is the newest package's. A package without a venv is
  left out and named. A package whose checker settings the root file
  would override is written, and named. The exit is 0, 1 or 2 ([`api.md`](api.md)).
- Pinned tools: `ast-grep-cli >=0.45.3,<0.46` and
  `import-linter >=2.15,<3`, locked at 0.45.3 and 2.15.
- `shims/language-server`, which runs a project's own language
  server through `direnv exec`, for an agent that starts servers from its
  own `PATH`. It ships in the source tree only. Under the name
  `typescript-language-server` it also turns off the separate syntax
  server (`useSyntaxServer: "never"` in `initialize`), one tsserver
  instead of two, 90–110 MB less per server on a large project.
- Python 3.12 floor.
