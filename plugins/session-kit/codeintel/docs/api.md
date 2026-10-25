# The surface

**The command line is the public surface**: the four commands below,
their output lines and their exit statuses. A repository wires them, and
this package's version number protects them. The Python
modules behind it are described after it, for a contributor or a reader
of the tests, and are **not** public: they may change in any release
without a major bump.

`ast-grep` and `lint-imports` stay outside this surface: they are the
pinned tools' own CLIs, documented by their projects, and this package
fixes only their versions: `ast-grep-cli >=0.45.3,<0.46` and
`import-linter >=2.15,<3`, locked at 0.45.3 and 2.15.

## The command line

```text
session-codeintel recipes list
session-codeintel recipes path <name>
session-codeintel pyright-env [ROOT]
session-codeintel looks [ROOT]
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

- **Every Python name**, above or starting with `_`.
- **The file's exact text**, beyond the shape `render` gives: key order
  and indentation are stable in practice, and not promised.
- **The recipes' own text.** A recipe's pattern and comments can
  improve in any release. Copy the one you use, since a script that
  references the installed file follows those changes.
- **`index.toml`**, the purposes file. `bundled()` reads it for you.
- **The shim**, `shims/language-server`. It is in the source tree and
  not in the wheel. [`operating.md`](operating.md) says how to install
  it.
