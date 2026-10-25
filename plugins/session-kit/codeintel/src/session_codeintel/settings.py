"""The settings file, ``.claude/claude-kit.json``, read as JSON under strict typing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeGuard

FILE = Path(".claude") / "claude-kit.json"


def is_record(value: object) -> TypeGuard[dict[str, object]]:
    """Whether a JSON value is an object."""
    return isinstance(value, dict)


def is_list(value: object) -> TypeGuard[list[object]]:
    """Whether a JSON value is an array."""
    return isinstance(value, list)


def strings(value: object) -> tuple[str, ...]:
    """Return the strings of a JSON array, and nothing for any other value."""
    return tuple(s for s in value if isinstance(s, str)) if is_list(value) else ()


def text(block: dict[str, object], key: str) -> str | None:
    """Return a non-empty string under the key with its slashes trimmed, else None."""
    value = block.get(key)
    return value.strip("/") if isinstance(value, str) and value.strip("/") else None


def block(root: Path, name: str) -> dict[str, object] | None:
    """Read one top-level block of the settings file: None when the file or the block is missing."""
    try:
        parsed: object = json.loads((root / FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    found = parsed.get(name) if is_record(parsed) else None
    return found if is_record(found) else None
