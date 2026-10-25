"""The layers pack: written from the settings, proven by its own cases, targeting the layers."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from session_codeintel.cli import main
from session_codeintel.layers import HEADER, Settings, read_settings, render, write

if TYPE_CHECKING:
    import pytest

AST_GREP = Path(sys.executable).parent / "ast-grep"
RUFF = Path(sys.executable).parent / "ruff"
SETTINGS = {
    "layers": {
        "python": {
            "core": "backend/src/app/core",
            "shell": "backend/src/app/shell",
            "unwinds": ["backend/src/app/core/result.py"],
        },
        "typescript": {
            "core": "frontend/src/core",
            "effects": "frontend/src/effects",
            "outside": ["@/effects/"],
        },
    }
}


FOREIGN_RULE = "id: py-no-raise\nrule:\n  kind: raise_statement\n"
PLANTED = {
    "backend/src/app/core/pure.py": (
        "import os\n\n\ndef f() -> None:\n    print(os.getcwd())\n    raise ValueError\n"
    ),
    "backend/src/app/core/result.py": "def fail() -> None:\n    raise RuntimeError\n",
    "backend/src/app/shell/io.py": (
        "def g() -> None:\n    print('hi')\n\n\n"
        'def h() -> None:\n    """Effects: prints."""\n    print(\'hi\')\n'
    ),
    "frontend/src/core/a.ts": (
        "import { useState } from 'react'\nexport function now(): number { return Date.now() }\n"
    ),
    "frontend/src/effects/b.ts": (
        "export function now(): number { return Date.now() }\n"
        "/** @effects clock */\nexport function then(): number { return Date.now() }\n"
    ),
}


def tree(root: Path, files: dict[str, str]) -> None:
    """Write each file under the root."""
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a pinned tool in the project."""
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False, timeout=20)  # noqa: S603  (decisions.md, 6)


def project(tmp_path: Path) -> Path:
    """Build a project with both layers named, the Python half under its own pyproject."""
    tree(
        tmp_path,
        {
            ".claude/claude-kit.json": json.dumps(SETTINGS),
            "backend/pyproject.toml": '[project]\nname = "app"\nversion = "0"\n',
        },
    )
    return tmp_path


def test_the_pack_is_written_once_and_a_foreign_file_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Each file carries the header, a second run changes nothing, a hand-written file stays."""
    root = project(tmp_path)
    settings = read_settings(root)
    assert settings is not None
    assert settings.python is not None
    assert settings.python.source == "backend/src/app"
    assert main(["layers", str(root)]) == 0
    out = capsys.readouterr().out
    rules = sorted(p.name for p in (root / "lint/ast-grep/rules").glob("*.yml"))
    assert rules == [
        "py-core-no-io.yml",
        "py-core-sync.yml",
        "py-no-raise.yml",
        "py-shell-declares-effects.yml",
        "ts-core-imports-only-core.yml",
        "ts-core-no-effects.yml",
        "ts-effects-declared.yml",
    ]
    assert sorted(p.name for p in (root / "lint/ast-grep/tests").glob("*.yml")) == [
        r.replace(".yml", "-test.yml") for r in rules
    ]
    assert "written sgconfig.yml" in out
    assert (root / "sgconfig.yml").read_text(encoding="utf-8").startswith(HEADER)
    ruff_toml = (root / "backend/src/app/core/ruff.toml").read_text(encoding="utf-8")
    assert 'extend = "../../../pyproject.toml"' in ruff_toml
    assert "backend/src/app/core/result.py" in (
        root / "lint/ast-grep/rules/py-no-raise.yml"
    ).read_text(encoding="utf-8")
    assert main(["layers", str(root)]) == 0
    assert "written" not in capsys.readouterr().out
    tree(root, {"lint/ast-grep/rules/py-no-raise.yml": FOREIGN_RULE})
    assert main(["layers", str(root)]) == 1
    assert "refused lint/ast-grep/rules/py-no-raise.yml" in capsys.readouterr().err
    tree(root, {".claude/claude-kit.json": "{}"})
    assert main(["layers", str(root)]) == 2


def test_the_rules_pass_their_own_cases_and_target_the_layers(tmp_path: Path) -> None:
    """ast-grep test passes every generated case, and a scan flags the core and not the shell."""
    root = project(tmp_path)
    write(root, render(root, settings_of(root)))
    tested = run([str(AST_GREP), "test", "-c", "sgconfig.yml", "--skip-snapshot-tests"], root)
    assert tested.returncode == 0, tested.stdout + tested.stderr
    tree(root, PLANTED)
    scanned = run([str(AST_GREP), "scan", "-c", "sgconfig.yml", "--json=compact", "."], root)
    found = sorted(
        (m["ruleId"], m["file"], m["range"]["start"]["line"] + 1)
        for m in json.loads(scanned.stdout)
    )
    assert found == [
        ("py-core-no-io", "backend/src/app/core/pure.py", 5),
        ("py-no-raise", "backend/src/app/core/pure.py", 6),
        ("py-shell-declares-effects", "backend/src/app/shell/io.py", 1),
        ("ts-core-imports-only-core", "frontend/src/core/a.ts", 1),
        ("ts-core-no-effects", "frontend/src/core/a.ts", 2),
        ("ts-effects-declared", "frontend/src/effects/b.ts", 1),
    ]
    linted = run(
        [str(RUFF), "check", "--select", "TID251", "--output-format", "concise", "backend/src"],
        root,
    )
    assert [line.split(":")[0] for line in linted.stdout.splitlines() if "TID251" in line] == [
        "backend/src/app/core/pure.py"
    ]


def settings_of(root: Path) -> Settings:
    """Read the settings as the module reads them."""
    settings = read_settings(root)
    assert settings is not None
    return settings
