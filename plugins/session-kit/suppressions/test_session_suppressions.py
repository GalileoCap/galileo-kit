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
PYRIGHT = "# pyright: " + "ignore[reportUnknownMemberType]"
TS_IGNORE = "// @ts-" + "ignore"
ESLINT = "// eslint-" + "disable-next-line no-console, no-alert"
AS_ANY = "as " + "any"
INDEX = "docs/suppressions.md"


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
    "a.py": f"x = 1  {NOQA}  the url is one token\n",
    "b.ts": f"// the library's own type is wider than ours\nconst y = z {AS_ANY}\n",
}

root = project(CLEAN)
code, out = run(root, "index")
case("index writes the file and says how many", code == 0 and f"{INDEX}: 2 suppressions" in out and (root / INDEX).is_file(), out)
text = (root / INDEX).read_text(encoding="utf-8")
case("the index is a table of where, marker and why", "| `a.py:1` | `noqa` | the url is one token |" in text and f"| `b.ts:2` | `{AS_ANY}` | the library's own type is wider than ours |" in text, text)
case("the index says it is generated", "session-suppressions index" in text, text)
code, out = run(root, "list")
case("list prints each marker with its reason", code == 0 and "a.py:1  noqa  the url is one token" in out and f"b.ts:2  {AS_ANY}  the library's own type is wider than ours" in out, out)
code, out = run(root, "check")
case("check passes when every marker has its reason and the index is current", code == 0 and f"2 suppressions, each with its reason, and {INDEX} current" in out, out)

root = project({**CLEAN, "c.py": f"y = 2  {NOQA}\n", "d.py": f"z = 3  {NOQA}  too short\n"})
run(root, "index")
code, out = run(root, "check")
case("check fails on a marker with no reason, naming its line", code == 1 and f"c.py:1: `noqa` has no reason on its line or the line above" in out, out)
case("two words are no reason", f"d.py:1: `noqa` has no reason" in out, out)
code, out = run(root, "list")
case("list marks a marker without a reason", "c.py:1  noqa  unjustified" in out, out)

root = project(CLEAN)
code, out = run(root, "check")
case("a missing index is a problem naming the command", code == 1 and f"{INDEX}: missing, run `session-suppressions index`" in out, out)
run(root, "index")
(root / "e.py").write_text(f"w = 4  {NOQA}  another one with a reason\n", encoding="utf-8")
code, out = run(root, "check")
case("a stale index is a problem", code == 1 and f"{INDEX}: stale, run `session-suppressions index`" in out, out)

root = project({
    "f.py": f"a = 1  {PYRIGHT}  the stubs lack the member\nb = 2  # the second line carries the reason\nc = 3  {NOQA}\n",
    "g.ts": f"{ESLINT}  the command line prints\nconsole.log(1)\n",
    "h.ts": f"{TS_IGNORE}: the type is wrong upstream, in the library\nconst q = 1\n",
})
code, out = run(root, "list")
case("the codes after a marker are not the reason", "f.py:1  pyright: ignore  the stubs lack the member" in out and "g.ts:1  eslint-disable  the command line prints" in out, out)
case("a reason on the line above counts", "f.py:3  noqa  the second line carries the reason" in out, out)
case("a colon after the marker is not the reason", "h.ts:1  @ts-ignore  the type is wrong upstream, in the library" in out, out)

root = project({
    **CLEAN,
    "node_modules/x.js": f"{TS_IGNORE}\n",
    "env/pyvenv.cfg": "home = /usr/bin\n",
    "env/lib/site.py": f"{NOQA}\n",
    "CLAUDE.md": f"Never {NOQA}.\n",
    "s.py": f'text = "{NOQA}"\n"""{NOQA} in a docstring."""\n',
    "t.ts": f"const s = '{AS_ANY}'\n",
})
run(root, "index")
code, out = run(root, "check")
case("a marker in node_modules, in a venv, in prose, in the index, in a string or a docstring is not a site", code == 0 and "2 suppressions" in out, out)

root = project({
    ".claude/claude-kit.json": '{"suppressions": {"index": "docs/escapes.md", "skip": ["vendor"]}}',
    "a.py": f"x = 1  {NOQA}  the url is one token\n",
    "vendor/v.py": f"{NOQA}\n",
})
code, out = run(root, "index")
case("the project's own index path and skipped directories apply", code == 0 and "docs/escapes.md: 1 suppressions" in out and (root / "docs/escapes.md").is_file(), out)
code, out = run(root, "check")
case("check reads the project's index path", code == 0 and "docs/escapes.md current" in out, out)

print(f"{len(failures)} failures")
if failures:
    print("\n".join(failures))
    sys.exit(1)
