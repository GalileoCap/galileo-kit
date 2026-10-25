"""The one place the tests run a pinned tool or git, so one ledger row covers it."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a pinned tool or git in a temporary project with a fixed argument list."""
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False, timeout=20)  # noqa: S603  (decisions.md, 6)
