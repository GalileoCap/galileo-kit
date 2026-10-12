# Integrating session-codeintel

Three things a repository wires, each independent of the others: sweeps
with the recipes, import contracts in its gate, and the root
`pyrightconfig.json` for its language server. Take the ones you need.

## What the repository supplies

| What | Why it is yours |
| --- | --- |
| **The packages**, each an immediate subdirectory of the root with its own `pyproject.toml` | `pyright-env` discovers them there. It ignores a directory with no `pyproject.toml`, and does not look deeper than one level. |
| **Each package's venv**, at `<package>/.venv`, made by `uv sync` | The venv holds the third-party code a package imports. A package without one is left out of the config and named, because the server could not resolve its imports anyway. |
| **Each package's checker settings, in its own `pyrightconfig.json`** | Why is under *The root `pyrightconfig.json`*, below. |
| **The contracts**, in the package's own `pyproject.toml` | They name your modules. |
| **When the config is regenerated** | Only your tooling knows when a venv appeared or moved. `operating.md` has the usual choices. |
| **The language server**, and the editor or agent that starts it | Its version is your toolchain's to pin. |

## Configuration

There is none to set: no environment variables, no settings file. The
command-line arguments are in [`api.md`](api.md). What `pyright-env`
*reads* is your configuration, so here it is:

| Read from | Used for | A wrong value |
| --- | --- | --- |
| `<package>/pyproject.toml` exists | the directory is a package | none: without it, the directory is not a package |
| `<package>/.venv/pyvenv.cfg`, `version` or `version_info` | the interpreter's `major.minor`, which names `lib/python<x.y>/site-packages` | missing or without a version: the package is left out and named, exit 1 |
| `pythonVersion` in `<package>/pyrightconfig.json`, else `[tool.basedpyright]` or `[tool.pyright]` in `pyproject.toml`, else the floor of `requires-python`, else the interpreter's | the environment's `pythonVersion` | the package's own code is judged at that version |
| the newest of those versions | the top-level `pythonVersion`, which is the one pyright reads the standard library at | none you set: it is computed |
| `[tool.uv.sources]` entries with a `path` | their `src/` (or their directory) joins the package's `extraPaths` | an entry pointing at no directory is skipped |
| `<package>/src/`, else the package directory; then `<package>/tests/` | the package's own source roots, and the top-level `include` | a flat layout works; any other name is not found |

## Wiring 1: sweeps with a recipe

A recipe is an ast-grep rule to **copy, retarget and run**, never a
check. For the `async` migration:

```bash
cp "$(scripts/codeintel session-codeintel recipes path api-migration-await-call)" await-fetch.yml
# edit the copy: the pattern and fix name your method instead of store.history
```

Then read the copy's header comment. It is the procedure: two
parenthesising passes, then the rule. A subscripted or attribute-accessed
call awaited by the rule alone would await the subscript and leave the call bare.

```bash
ag() { scripts/codeintel ast-grep "$@"; }
ag run -U -l py -p '$OBJ.client.fetch($$$A)[$I]' -r '(await $OBJ.client.fetch($$$A))[$I]' src tests
ag run -U -l py -p '$OBJ.client.fetch($$$A).$F'  -r '(await $OBJ.client.fetch($$$A)).$F'  src tests
ag scan -U -r await-fetch.yml src tests
```

The rule leaves an already-awaited call alone, so it is safe to re-run
while your typechecker drives the next wave: each call site that became
`await` inside a sync helper makes that helper `async`, and its own
callers are the next pass.

**Your own gate rules**, the kind that must never match, are written the
same way and tested with ast-grep's own runner (`ast-grep test`, which
reads `ruleDirs` and `testConfigs` from an `sgconfig.yml`). Run both
through this package, so the rule and its test see the same engine.

## Wiring 2: import contracts in the gate

Contracts go in the package's own `pyproject.toml`, under
`[tool.importlinter]`. Run from that package's directory:

```bash
# through this package's project: your package is not installed there, so name its source root
PYTHONPATH=src scripts/codeintel lint-imports
# or, with session-codeintel as a dev dependency of the package
uv run lint-imports
```

It exits 0 when every contract is kept and 1 otherwise, and it names each
illegal import with its importer and line. Put it in the package's check
script beside the linter and the typechecker.

**Two shapes cover moving a subsystem out of its host.** Both were
checked on a planted package with `import-linter` 2.15. `shop` is the
host and `shop.secrets` the subsystem.

*The subsystem imports nothing of the host* (`forbidden`):

```toml
[tool.importlinter]
root_package = "shop"

[[tool.importlinter.contracts]]
name = "secrets imports nothing of the host but its own table models"
type = "forbidden"
source_modules = ["shop.secrets"]
forbidden_modules = ["shop.billing", "shop.web", "shop.db"]   # every other top-level module, written out
ignore_imports = ["shop.secrets.** -> shop.db"]
allow_indirect_imports = true
```

*The host reaches the subsystem only through its public module*
(`protected`):

```toml
[[tool.importlinter.contracts]]
name = "the host reaches secrets only through shop.secrets"
type = "protected"
protected_modules = ["shop.secrets.*"]
allowed_importers = ["shop.secrets"]
```

`allowed_importers` covers the subsystem's own descendants, so its
modules still import each other. `from shop.secrets import seal` is
legal; `from shop.secrets.store import seal` in `shop.billing.pay` is
reported as `shop.billing.pay -> shop.secrets.store (l.2)`.

**A contract enters holding, or as a ratchet.** One that does not hold
today enters with each current breach as an `ignore_imports` line, so it
is green, and every new breach is red. `lint-imports` fails on an ignore
line that matches no import ("No matches for ignored import …"), so each
line has to be deleted with the import it covers, and the list only
shrinks. The count is the migration's progress report.

**Treat an added `ignore_imports` line as a relaxation of the gate**, and
a deleted one as progress. The first needs a reviewer's decision; the
second needs nobody's.

What a contract does not catch:

- **Tests.** `lint-imports` analyses the package named by
  `root_package`, and leaves your test directory out. That is the right default,
  since tests are part of the host.
- **Indirect imports**, when `allow_indirect_imports` is set. Without
  it, `forbidden` also follows chains through other modules, which is
  rarely what an extraction wants.
- **Imports made at runtime** through `importlib`.
- **A new top-level module**, in a `forbidden` list that is written out.
  Add it to the list in the change that creates it.

## Wiring 3: the root `pyrightconfig.json`

```bash
scripts/codeintel session-codeintel pyright-env .
```

**Never commit the file.** Add `/pyrightconfig.json` to `.gitignore`. Its
`extraPaths` name `lib/python3.12/site-packages`, and the next machine's
venv may be on 3.13. Regenerate it instead ([`operating.md`](operating.md)).

**Move each package's checker settings into its own
`pyrightconfig.json`.** Pyright and basedpyright look for a
`pyrightconfig.json` in every directory up to the root *before* they read
the local `pyproject.toml`. With the root file present, a checker run
inside a package that keeps `[tool.basedpyright]` in `pyproject.toml`
loads the root file instead, and judges the package under settings that
are not its own. On one repository that meant 141 reported errors that
were not there. A `pyrightconfig.json` beside the package's
`pyproject.toml` is found first. It is JSON with comments:

```jsonc
// This package's checker settings, found before the generated root file.
{
  "typeCheckingMode": "strict",
  "include": ["src", "tests"],
  "pythonVersion": "3.12"
}
```

`pyright-env` names every package it wrote that still keeps its settings
in `pyproject.toml`, and exits 1 for it.

**Two answers to expect from the server**, neither of them a fault:

- **An answer holding only the declaration means the server is still
  loading.** Ask again after a few seconds. A large TypeScript project
  takes longer than a Python one.
- **A Protocol splits a reference search in two.** Asked from the
  Protocol's method, the server finds the call sites typed as the
  Protocol. Asked from the implementation, it finds the rest.

## What the repository must not do

- **Commit the generated file**, or edit it by hand. The next run
  overwrites it; the one after that, on another machine, disagrees with
  it.
- **Keep a checker's settings in `pyproject.toml`** in any package under
  the root file. The package's own gate is then judged under someone
  else's settings, and nothing fails to tell you.
- **Run a second `ast-grep` from `PATH`** anywhere a pinned one also
  runs, a console's lint script included. Two versions of one engine
  give two verdicts on one rule.
- **Move a venv out of the package directory**, with
  `UV_PROJECT_ENVIRONMENT` or otherwise. `pyright-env` looks only at
  `<package>/.venv` and leaves out a package without one.

## Migrations

None. The package owns no tables and stores nothing, and the one file it
writes is regenerated from what is on disk.
