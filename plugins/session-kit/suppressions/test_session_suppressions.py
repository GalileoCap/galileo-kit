"""Cases for session_suppressions.py. Run it: python3 suppressions/test_session_suppressions.py

Each case builds a small project in a temporary directory, runs the command
over it and reads its exit code and lines. The markers are spelled in pieces
so this file holds none of them whole.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = str(Path(__file__).with_name("session_suppressions.py"))
NOQA = "# " + "noqa: E501"
TS_IGNORE = "// @ts-" + "ignore"
AS_ANY = "as " + "any"
LEDGER = (
    "# Decisions\n\n## Exceptions awaiting approval\n\n| # | Where | Exception | Why |\n| --- | --- | --- | --- |\n"
    "| 3 | a.py | a long line | the url |\n\n## Exceptions the owner approved\n\n| # | Where | Exception | Why |\n"
    "| --- | --- | --- | --- |\n| 1 | b.ts | the library's any | TanStack |\n"
)


def project(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="session-suppressions-"))
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def run(root: Path, *args: str) -> tuple[int, str]:
    out = subprocess.run([sys.executable, TOOL, *args, "--root", str(root)], capture_output=True, text=True, timeout=30)
    return out.returncode, out.stdout + out.stderr


failures: list[str] = []


def case(name: str, ok: bool, detail: str = "") -> None:
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        failures.append(name + ("\n" + detail if detail else ""))


CLEAN = {
    "docs/decisions.md": LEDGER,
    "a.py": f"x = 1  {NOQA}  (decisions.md, 3)\n",
    "b.ts": f"// decisions.md, 1\nconst y = z {AS_ANY}\n",
}

root = project(CLEAN)
code, out = run(root, "list")
case("list prints each marker with its row and the heading it sits under", code == 0 and "a.py:1  noqa  row 3 (Exceptions awaiting approval)" in out and f"b.ts:2  {AS_ANY}  row 1 (Exceptions the owner approved)" in out, out)
case("list ends with the count", "2 suppressions" in out, out)
code, out = run(root, "check")
case("check passes when every marker cites a row", code == 0 and "2 suppressions, every one with its row" in out, out)

root = project({**CLEAN, "c.py": f"y = 2  {NOQA}\n"})
code, out = run(root, "check")
case("check fails on a marker that cites no row, naming its line", code == 1 and "c.py:1: `noqa` cites no row of docs/decisions.md" in out, out)

root = project({**CLEAN, "c.ts": f"{TS_IGNORE} decisions.md, 9\nlet q\n"})
code, out = run(root, "check")
case("check fails on a citation whose row the ledger lacks", code == 1 and f"c.ts:1: `{TS_IGNORE[3:]}` cites row 9, which docs/decisions.md does not hold" in out, out)

root = project({
    **CLEAN,
    "node_modules/x/index.js": f"{TS_IGNORE}\n",
    "CLAUDE.md": f"Never write {NOQA}.\n",
    ".venv/lib/site.py": f"z = 0  {NOQA}\n",
    "venv-tools/pyvenv.cfg": "home = /usr/bin\n",
    "venv-tools/lib/python3.14/site-packages/dep.py": f"d = 0  {NOQA}\n",
})
code, out = run(root, "list")
case("a marker in node_modules, in a venv of any name, in prose or in the ledger is not a site", code == 0 and "2 suppressions" in out, out)

root = project({
    **CLEAN,
    "fixtures.py": f'PLANTED = """\nx = 1  {NOQA}\n"""\nTEXT = "{TS_IGNORE} in a string"\n',
    "reader.ts": f"const DIRECTIVE = '{TS_IGNORE}'\nconst words = `{AS_ANY}`\n",
})
code, out = run(root, "check")
case("a marker inside a string or a docstring is a mention and no site", code == 0 and "2 suppressions, every one" in out, out)

root = project({"a.py": f"x = 1  {NOQA}\n"})
code, out = run(root, "check")
case("a missing ledger makes every marker a problem and names the ledger", code == 1 and "cites no row of docs/decisions.md" in out, out)

root = project({
    ".claude/claude-kit.json": '{"suppressions": {"ledger": "docs/exceptions.md", "cite": "exception (\\\\d+)", "skip": ["generated"]}}',
    "docs/exceptions.md": "| # | What |\n| --- | --- |\n| 7 | ok |\n",
    "a.py": f"x = 1  {NOQA}  exception 7\n",
    "generated/g.py": f"g = 1  {NOQA}\n",
})
code, out = run(root, "check")
case("the project's own ledger, citation pattern and skipped directories apply", code == 0 and "1 suppressions, every one with its row in docs/exceptions.md" in out, out)

if failures:
    print(f"\n{len(failures)} failed")
    for f in failures:
        print(f)
    sys.exit(1)
print("\nall passed")
