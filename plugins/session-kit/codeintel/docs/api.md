# The surface

**The command line is the public surface**: the commands below,
their output lines and their exit statuses. A repository wires them, and
this package's version number protects them. The Python
modules behind it are described after it, for a contributor or a reader
of the tests, and are **not** public: they may change in any release
without a major bump.

`ast-grep`, `ruff` and `lint-imports` stay outside this surface: they are
the pinned tools' own CLIs, documented by their projects, and this package
fixes only their versions: `ast-grep-cli >=0.45.3,<0.46`,
`ruff >=0.15.7,<0.16` and `import-linter >=2.15,<3`.

## The command line

```text
session-codeintel recipes list
session-codeintel recipes path <name>
session-codeintel pyright-env [ROOT]
session-codeintel looks [ROOT]
session-codeintel layers [ROOT]
session-codeintel measure [ROOT] [--at REF]... [--area PATH]... [--skip PATH]... [--out FILE]
session-codeintel quality [ROOT] [--report]
session-codeintel footprint [ROOT] [--write] [--claude PATH]
session-codeintel template new <dir> --name <name> [--python <version>] [--no-docs]
session-codeintel template refresh <dir>
session-codeintel template check <dir>
```

### `recipes list`

One line per bundled recipe, sorted by name: `<name>`, a tab, its
one-line purpose. Exit 0.

### `recipes path <name>`

The recipe's rule file, as one absolute path. Once the package is
installed, this is inside `site-packages`, so copy it and edit the
copy. Exit 0.

An unknown name prints nothing on stdout, prints
`unknown recipe '<name>'; known: <a>, <b>` on stderr, and exits 2.

### `pyright-env [ROOT]`

Writes `ROOT/pyrightconfig.json`. `ROOT` defaults to the current
directory. [`integrating.md`](integrating.md) has what it reads, and
`render` below has what it writes.

| stream | line | when |
| --- | --- | --- |
| stdout | `pyrightconfig.json: <n> package(s)` | the file was written, or was already identical |
| stderr | `<dir>: pyproject.toml and no .venv — left out; run \`uv sync\` there` | once per package left out |
| stderr | `<dir>: checker settings in pyproject.toml, which the root pyrightconfig.json overrides when a checker runs there; move them to <dir>/pyrightconfig.json` | once per package written whose settings the root file would override |
| stderr | `pyrightconfig.json: not written — no package under <ROOT> has a .venv` | nothing could be written |

| exit | meaning |
| --- | --- |
| 0 | every package was written, and each is checked under its own settings |
| 1 | the file was written, and some package was left out or overridden, as named on stderr |
| 2 | nothing was written, because no package has a venv, and argparse's own usage errors |

An unchanged file is not rewritten, so a language server watching it
does not reload.

### `looks [ROOT]`

Reads the `looks` block of `ROOT/.claude/claude-kit.json`, runs the
pinned `ast-grep` over the source with three rules, and prints the
class strings of two or more classes written in more than one place: in
a `className` or `*ClassName` prop, an argument of `cn`, or a value of
a `*-looks.ts` file. The block holds `src`, the source directory (`src`
by default), `skip`, directories under it left out (`src/components/ui`
by default), and `allowed`, the looks that may repeat, each with `look`,
`files` and `reason`. The classes of a look are sorted, so their order
does not matter. An allowed look is not reported while it is written
in the files its entry lists and no other.

| stream | line | when |
| --- | --- | --- |
| stdout | `"<look>" is written in <n> places:` then `  <path>:<line>` per place | once per repeated look |
| stdout | `The allowed look "<look>" lists <files> but is written in <files or none>.` | once per allowance whose files drifted |
| stdout | `Each look belongs to one component or one *-looks.ts entry.` | after the repeats, when there are any |
| stdout | `Update the entry under looks.allowed in .claude/claude-kit.json: ...` | after the drifts, when there are any |
| stdout | `<n> class strings, none written twice` | nothing to report |
| stderr | `ast-grep failed: <stderr>` | the binary refused the source |

| exit | meaning |
| --- | --- |
| 0 | no look repeats and no allowance drifted |
| 1 | a look repeats, or an allowance drifted, as printed |
| 2 | ast-grep failed, and argparse's own usage errors |

### `layers [ROOT]`

Reads the `layers` block of `ROOT/.claude/claude-kit.json` and writes
the gate that holds the pure-core shape. The block names `rules` and
`tests`, the ast-grep directories (`lint/ast-grep/rules` and
`lint/ast-grep/tests`), and the layers: under `python`, `core` and
`shell` (directories), `source` (the tree `raise` is refused in, the
core's parent by default) and `unwinds` (files that may raise). Under
`typescript`, it names `core` and `effects` (directories) and `outside` (import
prefixes the core may not use, beyond `react`, `react-dom` and
`@tanstack/`). It writes one rule and one test file per rule
(`py-core-no-io`, `py-core-sync`, `py-shell-declares-effects`,
`py-no-raise`, `ts-effects-declared`, `ts-core-no-effects`,
`ts-core-imports-only-core`, each only for the layers named), a
`ruff.toml` in the Python core banning the effect modules and extending
the nearest ruff or pyproject config above it, and `sgconfig.yml` at the
root when there is none. Each file starts with a header naming the
command. `ast-grep test -c sgconfig.yml` then proves the rules and
`ast-grep scan -c sgconfig.yml` runs them.

| stream | line | when |
| --- | --- | --- |
| stdout | `written <path>` | the file was written or replaced |
| stdout | `unchanged <path>` | the file already held this text |
| stderr | `refused <path>: it exists and was not written by session-codeintel layers` | a file without the header is in the way |
| stderr | `.claude/claude-kit.json: no \`layers\` block, so nothing to write` | no settings |

| exit | meaning |
| --- | --- |
| 0 | every file written or unchanged |
| 1 | a file was refused, as named on stderr |
| 2 | no `layers` block, and argparse's own usage errors |

### `measure [ROOT] [--at REF]... [--area PATH]... [--skip PATH]... [--out FILE]`

Measures the areas of `ROOT` and prints a markdown report, or writes it
to `FILE`. The areas come from `measure.areas` in
`ROOT/.claude/claude-kit.json` (each with `name`, `path`, `skip`
directories and `extensions`, by default `.py`, `.ts`, `.tsx`, `.js`,
`.jsx`, `.mjs`, `.cjs`, `.yml` and `.yaml`), or from `--area`, each a directory with every `--skip`
left out, or the root alone. Dependency and build directories are always
left out. Without `--at` the working tree is measured as one snapshot.
With it, each `REF` is taken as a `git archive` into a directory of the
run's own and measured as a snapshot of its own, so the rows read against
each other.

Per area and snapshot: files, lines, code, comment and docstring lines
(Python through the tokenizer and `ast`, TypeScript and the rest by a
line scan). Then per language, the functions, their McCabe complexity
summed, the mean, the functions at 6 or more and the maximum (Python
from the pinned ruff's `C901` at cap zero, TypeScript from the pinned
ast-grep counting `if`, `?:`, loops, `case`, `catch`, `&&`, `||` and
`??` inside the innermost function), with the JSX elements, fragments
included, and, when
`ROOT` has a `looks` block, the repeated looks and their places.

| stream | line | when |
| --- | --- | --- |
| stdout | the report | no `--out` |
| stdout | `<FILE>: <n> row(s)` | `--out` |
| stderr | `git archive <REF>: <stderr>` | git refused a ref |

| exit | meaning |
| --- | --- |
| 0 | the report was printed or written |
| 2 | git refused a ref, and argparse's own usage errors |

### `quality [ROOT] [--report]`

Runs the three quality gates over the Python files of the areas named
under `quality.areas` in `ROOT/.claude/claude-kit.json` (each with
`name`, `path` and `skip`), or the root alone, with the dependency
directories and every venv left out. The duplicate gate fails on a
function body written twice: at any length under the same name, at three
statements or more under different names, dunders and the methods a
`Protocol` declares aside (`quality.protocols_from` names other trees
whose protocols count). The fallback finder fails on a site the ledger
has not judged, outside the tests: `x or v`, `.get(k, v)`,
`getattr(o, n, v)`, a broad `except`, an `except` that returns a literal
or swallows, and `if x is None: x = v` in its statement and ternary
spellings, `isinstance` read as a presence test. The file-length lint
fails on a file over `quality.max_code_lines` code lines (500), unless a
`quality.long` entry (`file`, `cap`, `reason`) raises its cap, or lifts it
when `cap` is absent.

The ledger is `quality.ledger` (`quality-ledger.toml`), TOML: a
`[[duplicates]]` row has `members` (`path:qualname`, sorted), `home`,
`disposition` (`move` or `keep`) and `why`. A `[[fallbacks]]` row has
`site`, `where`, `form`, `code`, `count` (1), `class` (`declared`,
`spoken`, `silent` or `refusal-class`), `disposition` (`keep`, `speak`,
`refuse`, `remove` or `raised`) and `why`. A row the gate cannot read
refuses the ledger whole, a `dead` class included, since a dead fallback
is removed and not judged. The gate fails on a row nothing matches, so
the ledger only shrinks. `--report` prints rows for every new family and
unjudged site with the judgement blank, to paste in and fill.

| stream | line | when |
| --- | --- | --- |
| stdout | `new duplicate (<n> statements): keep one copy, or add a ledger row naming its home:` then `    <path:qualname>` per member | once per family the ledger does not name |
| stdout | `stale duplicate row: the family is no longer as listed, remove or fix it:` then the members | once per row no family matches |
| stdout | `unjudged fallback  <path>:<line>  in <where>  [<form>]  <code>  (found <n>, ledger <m>)` | once per site the ledger does not cover, or covers with a lower count |
| stdout | `stale fallback row  <path>  in <where>  [<form>]  <code>  (ledger <n>, found <m>): remove or fix it` | once per row found fewer times than it says |
| stdout | `<path>: <n> code lines, <m> over its cap of <c>` | once per file over its cap, largest first |
| stdout | `the long entry for <path> names a file that is not there` | once per `long` entry naming no module |
| stdout | `<n> problems` | after the lines above |
| stdout | `<n> modules: no duplicate, every fallback judged (<rows> rows), every file under its cap` | nothing to report |
| stdout | the rows | `--report` |
| stderr | `<ledger>: <what is wrong>` | a row the gate cannot read |
| stderr | `<path>: not a directory, and protocols_from names a tree that is there` | a `protocols_from` tree is missing |

| exit | meaning |
| --- | --- |
| 0 | every gate passes, or `--report` printed its rows |
| 1 | a problem, as printed |
| 2 | the ledger or a settings tree refused, and argparse's own usage errors |

### `footprint [ROOT] [--write] [--claude PATH]`

Holds each plugin named under `footprint.plugins` in
`ROOT/.claude/claude-kit.json` to its reach as the engine reports it. It
runs `claude plugin validate <plugin>` and reads the lines of its findings
up to the plugin directory's checks: for each hooks module the events it
hooks, its gating hooks, the `$` calls with the functions they are made
through, and the environment and state it reads and writes, with the state
its types declare. `<plugin>/footprint.toml` holds those lines under
`[validator]`, one table key per kind of line and its items sorted, and
under `[why]` a reason for each `$` member and each hook event (the name
before a matcher). The lines compare as counts, since their order is the
order of registration. The engine is `--claude`, else the session's own
(`CLAUDE_CODE_EXECPATH`), else `claude` on PATH. `--write` takes
the footprint again, keeping each reason whose name is still there and
leaving the new ones empty, which the gate then asks for.

| stream | line | when |
| --- | --- | --- |
| stdout | `written <plugin>/footprint.toml` | `--write` |
| stdout | `<plugin>/footprint.toml: + <kind>: <item>` | once per item the validator prints more often than the file holds |
| stdout | `<plugin>/footprint.toml: - <kind>: <item>` | once per item the file holds more often than the validator prints |
| stdout | `<plugin>/footprint.toml: no reason for <name>` | once per member or event with an empty or missing reason |
| stdout | `<plugin>/footprint.toml: a reason for <name>, which the validator no longer lists` | once per reason left over |
| stdout | `<plugin>/footprint.toml: taken with <version>, checked with <version>` | the engine differs from the engine that took the file |
| stdout | `<plugin>/footprint.toml: missing, and --write takes it` | no file |
| stdout | `<plugin>: the footprint holds the validator's <n> items, each with its reason` | nothing to report |
| stderr | `.claude/claude-kit.json: no `footprint` block, so no plugin to hold` | no block |
| stderr | `<plugin>: the engine cut short <kinds>: what follows the cut is unseen` | a line of the validator's ended in `… [+N chars]` |
| stderr | `<plugin>: <the engine's errors, or what is wrong with the file>` | the engine refused the plugin, could not run, or the file cannot be read |

| exit | meaning |
| --- | --- |
| 0 | every plugin's validation matches its footprint, with every reason given |
| 1 | a difference, a reason owed or left over, or a missing file |
| 2 | no block, the engine refused, could not run or cut a line short, a file cannot be read, and argparse's own usage errors |

### `template new <dir> --name <name> [--python <version>] [--no-docs]`

Writes the Python kind into `<dir>`, creating it if needed: every base
file (`ruff.base.toml`, `pyright.base.json`, `scripts/check.base.sh`,
each headed `Written by session-codeintel template`), and every project
file only if absent (`pyproject.toml` extending the base with its own
`ignore = []`, `pyrightconfig.json` extending the base with `include` and
the Python version, `scripts/check` running the base legs, `scripts/test`,
`src/<module>/__init__.py`, `src/<module>/py.typed`, `tests/__init__.py`,
and the five pages under `docs/` unless `--no-docs`). `--python` is the
floor (`3.12`). The module is the name with its dashes as underscores.

| stream | line | when |
| --- | --- | --- |
| stdout | `created  <path>`, `refreshed  <path>` (a base file that existed) or `skipped  <path>  (exists, this project's)` | one per file |

Exit 0, or 2 for argparse's own usage errors.

### `template refresh <dir>`

Rewrites every base file whose bytes differ from the template, and no
other file.

| stream | line | when |
| --- | --- | --- |
| stdout | `refreshed  <path>` | per base file rewritten |
| stdout | `up to date` | none differed |

Exit 0.

### `template check <dir>`

Compares each base file byte for byte, then reads each project file the
way its tool does (ruff's `extend` from the TOML, `extends` from the
JSONC, an uncommented line naming the base in `scripts/check`) and
checks that `pyproject.toml` sets neither `select` nor `per-file-ignores`
under `[tool.ruff]` or `[tool.ruff.lint]`, which would discard the base's.

| stream | line | when |
| --- | --- | --- |
| stdout | `3 base files match session-codeintel template <version>` | clean |
| stderr | `<base> differs from session-codeintel template <version>: run \`session-codeintel template refresh <dir>\`, or move the change into <the file extending it>` | a base file edited |
| stderr | `<base> is missing: run \`session-codeintel template refresh <dir>\`` | a base file gone |
| stderr | `<file> does not extend <base>, so the bar does not apply to this project: <how to link it>` | a project file that lost the link, or is missing |
| stderr | `pyproject.toml sets <table> <key>, which discards ruff.base.toml's: use extend-<key>` | a discarding setting |

| exit | meaning |
| --- | --- |
| 0 | clean |
| 1 | findings, as printed |
| 2 | argparse's own usage errors |

## The modules behind it, which are private

Import them only if you accept that they can change under you. A tool
that wants the discovery without the file should ask for it, and they
would then be made public, with their own versioning.

### `session_codeintel.recipes`

```python
DIRECTORY: Path
```
Where the rule files and `index.toml` are installed.

```python
@dataclass(frozen=True, slots=True)
class Recipe:
    name: str  # the rule's id, and its file's stem
    purpose: str  # one line, from index.toml
    path: Path  # the rule file, absolute
```

```python
class UnknownRecipeError(LookupError):
    name: str  # the name asked for
    known: tuple[str, ...]  # every bundled name
```

```python
def bundled() -> list[Recipe]
```
Every recipe this package ships, sorted by name. Raises `LookupError`
when a rule file has no purpose in `index.toml`. That is a packaging
mistake in this package.

```python
def find(name: str) -> Recipe
```
The recipe called `name`. Raises `UnknownRecipeError`.

### `session_codeintel.pyright_env`

```python
CONFIG: str = "pyrightconfig.json"
```

```python
@dataclass(frozen=True, slots=True)
class Package:
    # Relative to the root, POSIX separators; the environment's root.
    directory: str
    # "major.minor" the package is checked against.
    python_version: str
    # "major.minor" of its .venv, which names site-packages.
    interpreter: str
    # "src" or the directory itself, then "tests" if present; relative to the root.
    sources: tuple[str, ...]
    # The source roots of its [tool.uv.sources] path entries, in table order.
    path_dependencies: tuple[str, ...]
```

```python
@dataclass(frozen=True, slots=True)
class Discovery:
    # Sorted by directory.
    packages: tuple[Package, ...]
    # Directories with a pyproject.toml and no usable .venv, sorted.
    without_venv: tuple[str, ...]
    # Written packages whose checker settings are in pyproject.toml, sorted.
    overridden: tuple[str, ...] = ()
```

```python
def discover(root: Path) -> Discovery
```
Every immediate subdirectory of `root` holding a `pyproject.toml`. It
reads nothing and writes nothing outside them.

```python
def render(packages: Sequence[Package]) -> str
```
The file's text: two-space JSON, a trailing newline, and the same bytes
for the same input. Raises `ValueError` on an empty sequence, which
`write` never passes it. The shape:

```json
{
  "pythonVersion": "<the newest package's>",
  "include": ["<every package's sources>"],
  "executionEnvironments": [
    {
      "root": "<directory>",
      "pythonVersion": "<its python_version>",
      "extraPaths": ["<its sources>", "<its path dependencies' sources>",
                     "<directory>/.venv/lib/python<interpreter>/site-packages"]
    }
  ]
}
```

```python
def write(root: Path) -> Discovery
```
Discover, then write `root/pyrightconfig.json` when at least one package
can be written, and only if its text changed. Returns the discovery
either way, so the caller can name what was left out.

### `session_codeintel.cli`

```python
def main(argv: Sequence[str] | None = None) -> int
REFUSED: int = 2
PARTIAL: int = 1
```

`main` runs the command and returns its exit status, without calling
`sys.exit`. The console script is `session-codeintel =
"session_codeintel.cli:main"`.

## Not public

- Every Python name, above or starting with `_`.
- The file's exact text, beyond the shape `render` gives: key order
  and indentation are stable in practice, and not promised.
- The recipes' own text. A recipe's pattern and comments can
  improve in any release. Copy the one you use, since a script that
  references the installed file follows those changes.
- `index.toml`, the purposes file. `bundled()` reads it for you.
- The shim, `shims/language-server`. It is in the source tree and
  not in the wheel. [`operating.md`](operating.md) says how to install
  it.
