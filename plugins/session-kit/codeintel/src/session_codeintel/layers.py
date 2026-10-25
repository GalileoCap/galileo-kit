"""The layers pack: the pure core and the effect shell, held by generated rules.

A project that takes the shape names its layers under ``layers`` in
``.claude/claude-kit.json``: for Python, ``core`` and ``shell`` directories,
``source`` (the tree ``raise`` is refused in, the core's parent by default)
and ``unwinds`` (the files that may raise, where ``fail`` unwinds to its
``attempt``); for TypeScript, ``core`` and ``effects`` directories and
``outside``, import prefixes the core may not import beyond the frameworks.
``session-codeintel layers`` writes the ast-grep rules that hold the shape
(no I/O, clock, randomness or ``await`` in the core, every shell function
naming its effects, no ``raise`` outside the unwinding files, the core
importing only the core), one test file per rule, a ``ruff.toml`` in the
Python core banning the effect modules, and an ``sgconfig.yml`` when the
project has none. Every file carries a header naming this command, and a
file without it is never replaced.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from session_codeintel.settings import block as read_block
from session_codeintel.settings import is_record, strings, text

if TYPE_CHECKING:
    from pathlib import Path

HEADER = (
    "# Written by session-codeintel layers from .claude/claude-kit.json: edit the settings and"
    " run it again, since this file is replaced.\n"
)
FRAMEWORKS = ("react", "react-dom", "@tanstack/")
EFFECT_GLOBALS = (
    "fetch|EventSource|WebSocket|XMLHttpRequest|window|document|navigator|localStorage|"
    "sessionStorage|indexedDB|console|setTimeout|setInterval|clearTimeout|clearInterval|"
    "requestAnimationFrame|queueMicrotask|crypto|performance|alert"
)
BANNED_PYTHON = (
    ("os", "the environment and the filesystem are effects: pass values in"),
    ("time", "the clock is an effect: pass the time in"),
    ("random", "randomness is an effect: pass the value in"),
    ("secrets", "randomness is an effect: pass the value in"),
    ("asyncio", "scheduling is an effect: keep it in the shell"),
    ("datetime.datetime.now", "the clock is an effect: pass the time in"),
    ("datetime.datetime.today", "the clock is an effect: pass the time in"),
    ("datetime.date.today", "the clock is an effect: pass the time in"),
    ("uuid.uuid1", "a new id reads the clock: pass the id in"),
    ("uuid.uuid4", "a new id is randomness: pass the id in"),
    ("uuid.uuid6", "a new id reads the clock: pass the id in"),
    ("uuid.uuid7", "a new id reads the clock and draws randomness: pass the id in"),
)


@dataclass(frozen=True, slots=True)
class Python:
    """The Python layers."""

    core: str
    shell: str
    source: str
    unwinds: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TypeScript:
    """The TypeScript layers."""

    core: str
    effects: str
    outside: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Settings:
    """The ``layers`` block."""

    rules: str = "lint/ast-grep/rules"
    tests: str = "lint/ast-grep/tests"
    python: Python | None = None
    typescript: TypeScript | None = None


@dataclass(frozen=True, slots=True)
class Outcome:
    """What one run did, each list holding paths from the root."""

    written: tuple[str, ...]
    unchanged: tuple[str, ...]
    refused: tuple[str, ...]


def read_settings(root: Path) -> Settings | None:
    """Read the ``layers`` block; None when the file or the block is missing."""
    block = read_block(root, "layers")
    if block is None:
        return None
    return Settings(
        rules=text(block, "rules") or "lint/ast-grep/rules",
        tests=text(block, "tests") or "lint/ast-grep/tests",
        python=_python(block.get("python")),
        typescript=_typescript(block.get("typescript")),
    )


def _python(block: object) -> Python | None:
    if not is_record(block):
        return None
    core, shell = text(block, "core"), text(block, "shell")
    if core is None or shell is None:
        return None
    source = text(block, "source") or core.rsplit("/", 1)[0]
    return Python(core=core, shell=shell, source=source, unwinds=strings(block.get("unwinds")))


def _typescript(block: object) -> TypeScript | None:
    if not is_record(block):
        return None
    core, effects = text(block, "core"), text(block, "effects")
    if core is None or effects is None:
        return None
    return TypeScript(core=core, effects=effects, outside=strings(block.get("outside")))


def render(root: Path, settings: Settings) -> dict[str, str]:
    """Every file the pack writes, keyed by its path from the root."""
    files: dict[str, str] = {}
    if settings.python:
        files.update(_python_rules(settings.python, settings))
        files[f"{settings.python.core}/ruff.toml"] = _ruff(root, settings.python.core)
    if settings.typescript:
        files.update(_typescript_rules(settings.typescript, settings))
    if not (root / "sgconfig.yml").exists():
        config = f"ruleDirs:\n  - {settings.rules}\ntestConfigs:\n  - testDir: {settings.tests}\n"
        files["sgconfig.yml"] = HEADER + config
    return files


def _rule(settings: Settings, name: str, body: str, cases: str) -> dict[str, str]:
    return {
        f"{settings.rules}/{name}.yml": HEADER + f"id: {name}\n" + body,
        f"{settings.tests}/{name}-test.yml": HEADER + f"id: {name}\n" + cases,
    }


def _python_rules(py: Python, settings: Settings) -> dict[str, str]:
    at = {"core": py.core, "shell": py.shell}
    ignores = "".join(f"  - {path}\n" for path in py.unwinds)
    no_raise = PY_NO_RAISE.format(
        source=py.source, ignores=f"ignores:\n{ignores}" if ignores else ""
    )
    files: dict[str, str] = {}
    files.update(_rule(settings, "py-core-no-io", PY_CORE_NO_IO.format(**at), PY_CORE_NO_IO_CASES))
    files.update(_rule(settings, "py-core-sync", PY_CORE_SYNC.format(**at), PY_CORE_SYNC_CASES))
    files.update(
        _rule(settings, "py-shell-declares-effects", PY_SHELL.format(**at), PY_SHELL_CASES)
    )
    files.update(_rule(settings, "py-no-raise", no_raise, PY_NO_RAISE_CASES))
    return files


def _typescript_rules(ts: TypeScript, settings: Settings) -> dict[str, str]:
    at = {"core": ts.core, "effects": ts.effects}
    prefixes = "|".join(_escaped(p) for p in FRAMEWORKS + tuple(ts.outside))
    imports = TS_CORE_IMPORTS.format(core=ts.core, prefixes=prefixes)
    no_effects = TS_CORE_NO_EFFECTS.format(**at, globals=EFFECT_GLOBALS)
    files: dict[str, str] = {}
    files.update(_rule(settings, "ts-effects-declared", TS_EFFECTS.format(**at), TS_EFFECTS_CASES))
    files.update(_rule(settings, "ts-core-no-effects", no_effects, TS_CORE_NO_EFFECTS_CASES))
    files.update(_rule(settings, "ts-core-imports-only-core", imports, TS_CORE_IMPORTS_CASES))
    return files


def _escaped(prefix: str) -> str:
    return "".join("\\\\" + c if c in ".+*?()[]{}|^$/" else c for c in prefix)


def _ruff(root: Path, core: str) -> str:
    """Render the core's ruff.toml: the effect modules banned, the nearest config extended."""
    lines = [
        HEADER,
        "# The core is pure: these imports would let it reach the filesystem, the clock,",
        "# randomness or the environment. It receives what they produce as arguments.\n",
    ]
    parent = _config_above(root, core)
    if parent is not None:
        lines.append(f'extend = "{parent}"\n')
    lines.append("[lint.flake8-tidy-imports.banned-api]")
    lines += [f'"{module}".msg = "{why}"' for module, why in BANNED_PYTHON]
    return "\n".join(lines) + "\n"


def _config_above(root: Path, core: str) -> str | None:
    directory = (root / core).parent
    while True:
        for name in ("ruff.toml", ".ruff.toml", "pyproject.toml"):
            if (directory / name).is_file():
                return os.path.relpath(directory / name, root / core)
        if directory == root or root not in directory.parents:
            return None
        directory = directory.parent


def write(root: Path, files: dict[str, str]) -> Outcome:
    """Write each file, keeping one that is identical and refusing one with another author."""
    written: list[str] = []
    unchanged: list[str] = []
    refused: list[str] = []
    for path, content in sorted(files.items()):
        target = root / path
        if target.exists():
            current = target.read_text(encoding="utf-8")
            if current == content:
                unchanged.append(path)
                continue
            if not current.startswith(HEADER):
                refused.append(path)
                continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(path)
    return Outcome(written=tuple(written), unchanged=tuple(unchanged), refused=tuple(refused))


PY_CORE_NO_IO = """\
language: python
severity: error
message: "`{core}` is pure: reading or writing files or the console is an effect for `{shell}`."
files:
  - {core}/**/*.py
rule:
  any:
    - pattern: open($$$ARGS)
    - pattern: print($$$ARGS)
    - pattern: input($$$ARGS)
    - pattern: $P.read_text($$$ARGS)
    - pattern: $P.read_bytes($$$ARGS)
    - pattern: $P.write_text($$$ARGS)
    - pattern: $P.write_bytes($$$ARGS)
    - pattern: $P.open($$$ARGS)
"""
PY_CORE_NO_IO_CASES = """\
valid:
  - "def f(data: bytes) -> str:\\n    return data.decode()"
invalid:
  - "def f(p: Path) -> bytes:\\n    return p.read_bytes()"
  - "def f() -> None:\\n    print('hi')"
  - "def f(name: str) -> str:\\n    with open(name) as fh:\\n        return fh.read()"
"""
PY_CORE_SYNC = """\
language: python
severity: error
message: >-
  `{core}` is pure: an `async` function or an `await` means an effect belongs
  in `{shell}`.
files:
  - {core}/**/*.py
rule:
  any:
    - kind: await
    - all:
        - kind: function_definition
        - regex: "^async\\\\s"
"""
PY_CORE_SYNC_CASES = """\
valid:
  - "def f(x: int) -> int:\\n    return x + 1"
invalid:
  - "async def f() -> None:\\n    pass"
  - "def f(g):\\n    return (await g())"
"""
PY_SHELL = """\
language: python
severity: error
message: >-
  A function in `{shell}` names its effects in an `Effects:` docstring line.
  A function with none belongs in `{core}`.
files:
  - {shell}/**/*.py
rule:
  kind: function_definition
  not:
    has:
      field: body
      has:
        nthChild: 1
        kind: expression_statement
        has:
          kind: string
          regex: "Effects:"
"""
PY_SHELL_CASES = """\
valid:
  - "def f() -> None:\\n    \\"\\"\\"Do it.\\n\\n    Effects: writes.\\n    \\"\\"\\"\\n    pass"
  - "async def f() -> None:\\n    \\"\\"\\"Effects: reads the clock.\\"\\"\\"\\n    pass"
invalid:
  - "def f() -> None:\\n    \\"\\"\\"Do it.\\"\\"\\"\\n    pass"
  - "async def f() -> None:\\n    pass"
  - "def f() -> None:\\n    x = 1\\n    \\"Effects: late\\""
"""
PY_NO_RAISE = """\
language: python
severity: error
message: >-
  Return an `Err`, or hand the error to `fail`, instead of raising.
  A library exception that signals a bug may propagate on its own.
files:
  - {source}/**/*.py
{ignores}rule:
  kind: raise_statement
"""
PY_NO_RAISE_CASES = """\
valid:
  - "def f() -> Result[int, str]:\\n    return Err('no')"
invalid:
  - "def f() -> int:\\n    raise ValueError('no')"
  - "try:\\n    pass\\nexcept E:\\n    raise"
"""
TS_EFFECTS = """\
language: typescript
severity: error
message: >-
  An export of `{effects}` names its effects in an `@effects` JSDoc tag.
  One without effects belongs in `{core}`.
files:
  - {effects}/**/*.ts
rule:
  kind: export_statement
  has:
    any:
      - kind: function_declaration
      - kind: lexical_declaration
  not:
    follows:
      kind: comment
      regex: "@effects"
      stopBy: neighbor
"""
TS_EFFECTS_CASES = """\
valid:
  - "/**\\n * Load it.\\n *\\n * @effects network\\n */\\nexport function load(): void {}"
  - "/** @effects network */\\nexport const query = queryOptions({})"
  - "export type Status = 'a' | 'b'"
  - "function helper(): void {}"
invalid:
  - "export function load(): void {}"
  - "/** Loads it. */\\nexport function load(): void {}"
  - "export const query = queryOptions({})"
  - "/** @effects network */\\nconst x = 1\\nexport function load(): void {}"
"""
TS_CORE_NO_EFFECTS = """\
language: typescript
severity: error
message: >-
  `{core}` is pure: an effect (the network, the clock, randomness, storage, the DOM,
  a timer, await) belongs in `{effects}`, and the value it produces is passed in.
files:
  - {core}/**/*.ts
rule:
  any:
    - kind: await_expression
    - all:
        - any:
            - kind: function_declaration
            - kind: arrow_function
            - kind: method_definition
            - kind: function_expression
        - regex: "^async\\\\b"
    - pattern: Date.now($$$ARGS)
    - pattern: Math.random($$$ARGS)
    - pattern: new Date()
    - all:
        - kind: identifier
        - regex: "^({globals})$"
"""
TS_CORE_NO_EFFECTS_CASES = """\
valid:
  - "export function add(a: number, b: number): number { return a + b }"
  - "export const at = (now: number): string => String(now)"
  - "const o = { fetch: 1 }; export const f = o.fetch"
invalid:
  - "export async function load(): Promise<void> {}"
  - "export const load = async () => {}"
  - "export function now(): number { return Date.now() }"
  - "export function roll(): number { return Math.random() }"
  - "export function today(): Date { return new Date() }"
  - "export function get(u: string) { return fetch(u) }"
  - "export function w() { return window.innerWidth }"
  - "export function log(x: string) { console.log(x) }"
  - "export function later(f: () => void) { setTimeout(f, 1) }"
"""
TS_CORE_IMPORTS = """\
language: typescript
severity: error
message: >-
  `{core}` imports only `{core}`: an effect module, a page, a component or a
  framework is outside it.
files:
  - {core}/**/*.ts
rule:
  kind: import_statement
  has:
    field: source
    regex: "^['\\"]({prefixes})"
"""
TS_CORE_IMPORTS_CASES = """\
valid:
  - "import {{ add }} from './math'"
  - "import type {{ Millis }} from '@/core/model'"
invalid:
  - "import {{ useState }} from 'react'"
  - "import {{ queryOptions }} from '@tanstack/react-query'"
"""
