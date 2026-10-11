from __future__ import annotations

"""PostToolUse (Edit, Write): say so when a markdown file under docs/ passes
a length worth splitting. The limit is CLAUDE_KIT_DOC_LINES, 1500 by default.
Anything unexpected exits silently."""

import json
import os
import sys

LIMIT = int(os.environ.get("CLAUDE_KIT_DOC_LINES", "1500"))


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        path = str((payload.get("tool_input") or {}).get("file_path") or "")
    except (ValueError, AttributeError):
        return
    if "/docs/" not in path or not path.endswith(".md"):
        return
    try:
        with open(path, encoding="utf-8") as fh:
            lines = sum(1 for _ in fh)
    except OSError:
        return
    if lines > LIMIT:
        json.dump(
            {"systemMessage": f"Doc growing large ({lines} lines): {path}. Consider splitting."},
            sys.stdout,
        )


if __name__ == "__main__":
    main()
