"""Cases for session_docs.py. Run it: python3 docs_check/test_session_docs.py

Each case builds a small project in a temporary directory, runs the check
over it and reads its exit code and lines.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = str(Path(__file__).with_name("session_docs.py"))


def project(files: dict[str, str]) -> str:
    root = tempfile.mkdtemp(prefix="session-docs-")
    for name, text in files.items():
        path = Path(root, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def run(root: str) -> tuple[int, str]:
    out = subprocess.run([sys.executable, TOOL, "check", "--root", root], capture_output=True, text=True, timeout=30)
    return out.returncode, out.stdout + out.stderr


failures: list[str] = []


def case(name: str, ok: bool, detail: str = "") -> None:
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        failures.append(name + ("\n" + detail if detail else ""))


CLEAN = {
    "CLAUDE.md": "# P\n\n- `docs/plan.md`: the plan.\n- [the reviews](docs/reviews/one.md)\n- `docs/intent/`: one file per entry.\n",
    "docs/plan.md": "x\n",
    "docs/reviews/one.md": "x\n",
    "docs/intent/A1-a.md": "x\n",
    "docs/intent/INDEX.md": "x\n",
}
root = project(CLEAN)
code, out = run(root)
case("a document named by its path, by a link, or by a directory above it passes", code == 0 and "4 documents" in out, out)

root = project({**CLEAN, "docs/notes/new.md": "x\n"})
code, out = run(root)
case("a document no index names fails, naming the index and the document", code == 1 and out.strip() == "CLAUDE.md does not name docs/notes/new.md", out)

root = project({**CLEAN, "CLAUDE.md": CLEAN["CLAUDE.md"] + "- `docs/gone.md`: renamed away.\n"})
code, out = run(root)
case("a document an index names that does not exist fails", code == 1 and "CLAUDE.md names docs/gone.md, which does not exist" in out, out)

root = project({**CLEAN, "CLAUDE.md": CLEAN["CLAUDE.md"] + "```bash\nsession-tells show docs/a.md\n```\nSee other/docs/x.md and a.docs/y.md.\n"})
code, out = run(root)
case("a path in a code block, or inside a longer path, names nothing", code == 0, out)

root = project({**CLEAN, "CLAUDE.md": "# P\n\nEverything is under `docs/`.\n"})
code, out = run(root)
case("the documents directory alone covers nothing", code == 1 and out.count("does not name") == 4, out)

root = project({**CLEAN, ".claude/claude-kit.json": '{"docs": {"indexes": ["CLAUDE.md", "README.md"]}}\n', "README.md": "# R\n\n- `docs/plan.md`\n"})
code, out = run(root)
case("every index in the settings must name every document", code == 1 and "README.md does not name docs/reviews/one.md" in out and "CLAUDE.md does not name" not in out, out)

if failures:
    print(f"\n{len(failures)} failed")
    for f in failures:
        print(f)
    sys.exit(1)
print("\nall passed")
