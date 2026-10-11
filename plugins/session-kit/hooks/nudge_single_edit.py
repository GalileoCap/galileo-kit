from __future__ import annotations

import ast
import json
import re
import sys


def extract_heredoc_body(cmd: str) -> str | None:
    lines = cmd.splitlines()
    delim = None
    start_idx = None
    for i, line in enumerate(lines):
        m = re.search(r"<<-?\s*['\"]?(\w+)['\"]?", line)
        if m:
            delim = m.group(1)
            start_idx = i + 1
            break
    if delim is None:
        return None
    end_idx = None
    for j in range(start_idx, len(lines)):
        if lines[j].strip() == delim:
            end_idx = j
            break
    return "\n".join(lines[start_idx:end_idx]) if end_idx is not None else "\n".join(lines[start_idx:])


def is_heredoc_edit(cmd: str) -> bool:
    if not re.match(r"^\(?python3([\s]|$)", cmd.strip()):
        return False
    if "<<" not in cmd:
        return False
    has_replace = bool(re.search(r"\.replace\(", cmd))
    has_read = bool(re.search(r"read_text\(|\.read\(\)", cmd))
    has_write = bool(re.search(r"write_text\(|\.write\(", cmd))
    return has_replace or (has_read and has_write)


def classify(cmd: str) -> str | None:
    body = extract_heredoc_body(cmd)
    if body is None:
        return None
    try:
        tree = ast.parse(body)
    except SyntaxError:
        return None

    has_regex = has_loop = has_glob = False
    replace_calls = 0
    path_literals: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            has_loop = True
        if isinstance(node, ast.Call):
            func = node.func
            attr = getattr(func, "attr", None)
            if attr == "sub" and isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "re":
                has_regex = True
            if attr in ("glob", "rglob", "walk"):
                has_glob = True
            if attr == "replace":
                replace_calls += 1
            name = func.id if isinstance(func, ast.Name) else attr
            if (
                name in ("open", "Path")
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                path_literals.add(node.args[0].value)

    multi_file = has_glob or len(path_literals) > 1
    if has_regex:
        return "regex"
    if multi_file:
        return "multi_file"
    if has_loop or replace_calls >= 2:
        return "multi_edit"
    return "single_edit"


def main() -> None:
    try:
        data = json.load(sys.stdin, strict=False)
    except Exception:
        return
    cmd = str((data.get("tool_input") or {}).get("command") or "")
    if not is_heredoc_edit(cmd):
        return
    if classify(cmd) != "single_edit":
        return
    print(
        json.dumps(
            {
                "systemMessage": (
                    "This Bash call is a Python heredoc doing a single file edit "
                    "(read + one replace + write). Measured on this project's own "
                    "history, a single Edit tool call for this same change is "
                    "~35% cheaper in tokens, and — unlike Bash — it runs the "
                    "project's post-edit hooks (formatters, linters)."
                )
            }
        )
    )


if __name__ == "__main__":
    main()
