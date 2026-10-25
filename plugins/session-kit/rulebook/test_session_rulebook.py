"""Cases for session_rulebook.py. Run it: python3 rulebook/test_session_rulebook.py

Each case builds a small project and a Claude directory in temporary
directories, runs the command over them and reads its exit code and lines.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = str(Path(__file__).with_name("session_rulebook.py"))


def tree(files: dict[str, str]) -> str:
    root = tempfile.mkdtemp(prefix="session-rulebook-")
    for name, text in files.items():
        path = Path(root, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def run(root: str, claude_dir: str) -> tuple[int, str]:
    out = subprocess.run(
        [sys.executable, TOOL, "--root", root, "--claude-dir", claude_dir],
        capture_output=True, text=True, timeout=30,
    )
    return out.returncode, out.stdout + out.stderr


failures: list[str] = []


def case(name: str, ok: bool, detail: str = "") -> None:
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        failures.append(name + ("\n" + detail if detail else ""))


def five(n: int) -> str:
    return " ".join(["word"] * n) + "\n"


# The rules group: the user's file with its import, the project's file, its rules directory, the handoff. An import line is a word the model reads.
claude_dir = tree({"CLAUDE.md": "@global/rules.md\n" + five(10), "global/rules.md": five(100)})
root = tree({
    "CLAUDE.md": five(20) + "@docs/more.md\n",
    "docs/more.md": five(5),
    ".claude/rules/one.md": five(3),
    "CLAUDE.local.md": five(7),
    ".claude/skills/a/SKILL.md": five(30),
    "plugins/x/skills/b/SKILL.md": five(40),
})
code, out = run(root, claude_dir)
case("every file a turn loads is counted, imports included, and the totals are under the default budgets",
     code == 0 and "rules: 147 of 5,000 words" in out and "skills: 30 of 16,000 words" in out, out)
case("each file is listed with its count", "    100  ~/" in out or "    100  " in out and "global/rules.md" in out and "      5  docs/more.md" in out, out)

# The budgets and the extra skill files come from the project's settings.
Path(root, ".claude/claude-kit.json").write_text(
    '{"rulebook": {"rules": 100, "skills": 60, "skills_from": ["plugins/*/skills/*/SKILL.md"]}}\n', encoding="utf-8")
code, out = run(root, claude_dir)
case("a group over its budget fails, naming the total and the budget",
     code == 1 and "rules: 147 words over its budget of 100" in out and "skills: 70 words over its budget of 60" in out, out)
case("skills_from adds a plugin's skills to the skills group", "plugins/x/skills/b/SKILL.md" in out, out)

# A file that is missing is skipped, and an import loop is read once.
root = tree({"CLAUDE.md": "@CLAUDE.md\n@gone.md\n" + five(4)})
code, out = run(root, tree({}))
case("a missing file or import is skipped and a loop is read once", code == 0 and "rules: 6 of 5,000 words" in out, out)

if failures:
    print(f"\n{len(failures)} failed")
    for f in failures:
        print(f)
    sys.exit(1)
print("\nall passed")
