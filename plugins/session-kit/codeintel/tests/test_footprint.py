"""The footprint gate against a stand-in engine that prints a validator's report.

Kept from the blind cases: a reach the footprint does not hold fails, since
the gate passing it would be silent and would let the kit's code reach further
unreviewed.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from session_codeintel.cli import main

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

MARK = "  " + chr(0x276F)
"""How the validator opens each line of its findings."""

HEAD = f"""\
Validating plugin manifest: /x/plug/.claude-plugin/plugin.json

{MARK} types ./types/index.d.ts declares on $: nothing (no EngineInterface member)
{MARK} types ./types/index.d.ts declares state: kit.a, kit.b

Validating hooks: /x/plug/hooks/hooks.json

"""

TAIL = f"""
Plugin directory checks for /x/plug. The plugin directory is the catalog plugins go to.

✘ Found 1 problem the plugin directory refuses a submission for:

{MARK} LICENSE: License missing (LICENSE_MISSING). This plugin has no LICENSE file.

✔ Validation passed
"""

HOOKS = 'tool.call{tool=Bash}, prompt.submit{text=/"a, b"/}, tool.call{tool=Bash}, turn.complete'

MODULE = f"""\
{MARK} ./kit.tsx hooks: {HOOKS}
{MARK} ./kit.tsx gating hook with .catch: tool.call{{tool=Bash}}
{MARK} ./kit.tsx gating hook with .catch: tool.call{{tool=Bash}}
{MARK} ./kit.tsx calls: $.clock.after (via hold, step), $.fs.read, $.process.run (via gitOutput)
{MARK} ./kit.tsx env writes: nothing
{MARK} ./kit.tsx env reads: HOME
"""

ENGINE = """\
#!/bin/sh
here=$(dirname "$0")
if [ "$1" = "--version" ]; then cat "$here/version"; exit 0; fi
cat "$here/out"
exit "$(cat "$here/status")"
"""


def engine(root: Path, module: str, *, status: int = 0, version: str = "2.1.308") -> Path:
    """Write a stand-in for ``claude`` that prints a validator's report with this module."""
    home = root / "engine"
    home.mkdir(exist_ok=True)
    (home / "out").write_text(HEAD + module + TAIL, encoding="utf-8")
    (home / "status").write_text(f"{status}\n", encoding="utf-8")
    (home / "version").write_text(f"{version} (Claude Code)\n", encoding="utf-8")
    claude = home / "claude"
    claude.write_text(ENGINE, encoding="utf-8")
    claude.chmod(0o755)
    return claude


def project(root: Path) -> None:
    """Make a project whose settings name one plugin."""
    (root / "plug").mkdir()
    (root / ".claude").mkdir()
    settings = {"footprint": {"plugins": ["plug"]}}
    (root / ".claude" / "claude-kit.json").write_text(json.dumps(settings), encoding="utf-8")


def gate(root: Path, claude: Path, *extra: str) -> int:
    """Run the command over the project with the stand-in engine."""
    return main(["footprint", str(root), "--claude", str(claude), *extra])


def reasoned(root: Path, claude: Path) -> None:
    """Take the footprint and give every reason it asks for."""
    gate(root, claude, "--write")
    held = root / "plug" / "footprint.toml"
    held.write_text(held.read_text(encoding="utf-8").replace(' = ""', ' = "needed"'), "utf-8")


def test_a_call_the_footprint_lacks_fails_naming_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A reach the footprint does not hold, or a new caller of one, fails until reviewed."""
    project(tmp_path)
    reasoned(tmp_path, engine(tmp_path, MODULE))
    capsys.readouterr()
    grown = MODULE.replace(
        "$.process.run (via gitOutput)", "$.net.fetch, $.process.run (via gitOutput, judge)"
    )
    assert gate(tmp_path, engine(tmp_path, grown)) == 1
    out = capsys.readouterr().out
    assert "+ ./kit.tsx calls: $.net.fetch" in out
    assert "+ ./kit.tsx calls: $.process.run (via gitOutput, judge)" in out
    assert "- ./kit.tsx calls: $.process.run (via gitOutput)" in out
    assert "no reason for $.net.fetch" in out
