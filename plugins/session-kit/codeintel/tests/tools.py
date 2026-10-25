"""The one place the tests run a pinned tool or git, so one ledger row covers it."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def tree(root: Path, files: dict[str, str]) -> None:
    """Write each file under the root."""
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a pinned tool or git in a temporary project with a fixed argument list."""
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False, timeout=20)  # noqa: S603  a pinned tool or git over a temporary project, fixed arguments, no shell
