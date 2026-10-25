"""Cases for session_owed.py. Run it: python3 owed/test_session_owed.py

Each case builds a small repository in a temporary directory with OWED.md
committed in steps, runs the command over a range and reads its lines.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = str(Path(__file__).with_name("session_owed.py"))
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]

STEP1 = """# Owed

What a change leaves to do outside the code.

## At a deploy

### `work` @ `1` first thing

Before the deploy, set the key.
"""
STEP2 = STEP1 + """
### `work` @ `2` second thing

After the deploy, run the migration.

## In every worktree

### `work` @ `2` a new key

Add `KEY` to `.env`.
"""
STEP3 = STEP2.replace("### `work` @ `1` first thing\n\nBefore the deploy, set the key.\n", "")
WORKING = STEP2 + """
### `work` @ `3` uncommitted

Not committed yet.
"""


def git(root: str, *args: str) -> str:
    done = subprocess.run([*GIT, *args], cwd=root, capture_output=True, text=True, check=True, timeout=30)
    return done.stdout.strip()


def repo() -> tuple[str, list[str]]:
    root = tempfile.mkdtemp(prefix="session-owed-")
    git(root, "init", "-q")
    shas: list[str] = []
    Path(root, "README.md").write_text("x\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "start")
    shas.append(git(root, "rev-parse", "HEAD"))
    for text in (STEP1, STEP2, STEP3):
        Path(root, "OWED.md").write_text(text, encoding="utf-8")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "step")
        shas.append(git(root, "rev-parse", "HEAD"))
    return root, shas


def run(root: str, *args: str) -> tuple[int, str, str]:
    out = subprocess.run([sys.executable, TOOL, *args], cwd=root, capture_output=True, text=True, timeout=30)
    return out.returncode, out.stdout, out.stderr


failures: list[str] = []


def case(name: str, ok: bool, detail: str = "") -> None:
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        failures.append(name + ("\n" + detail if detail else ""))


root, (start, c1, c2, c3) = repo()

code, out, err = run(root, "--since", c1, "--until", c2)
case("a range lists the entries gained, by section", code == 0 and out == (
    "## At a deploy\n\n### `work` @ `2` second thing\n\nAfter the deploy, run the migration.\n\n"
    "## In every worktree\n\n### `work` @ `2` a new key\n\nAdd `KEY` to `.env`.\n"
), out + err)
case("an entry held at since is not listed", "first thing" not in out)

code, out, err = run(root, "--since", start, "--until", c1)
case("a since with no OWED.md owes nothing, so everything is listed", code == 0 and "first thing" in out, out + err)

code, out, err = run(root, "--since", c1, "--until", c2, "--section", "In every worktree")
case("--section keeps one section", code == 0 and "a new key" in out and "second thing" not in out, out + err)

Path(root, "OWED.md").write_text(WORKING, encoding="utf-8")
code, out, err = run(root, "--since", c2)
case("without --until the working file is read", code == 0 and out == (
    "## In every worktree\n\n### `work` @ `3` uncommitted\n\nNot committed yet.\n"
), out + err)

code, out, err = run(root, "--since", c2, "--until", c3)
case("an entry removed fails with its heading", code == 1 and "removed: `work` @ `1` first thing" in err and out == "", out + err)

code, out, err = run(root, "--since", c1, "--until", c1)
case("an empty range prints nothing and passes", code == 0 and out == "" and err == "", out + err)

code, out, err = run(root, "--since", "nosuchref", "--until", c2)
case("a ref git does not know is refused", code == 2 and "nosuchref" in err, out + err)

Path(root, "due.md").write_text(STEP1, encoding="utf-8")
Path(root, ".claude").mkdir()
Path(root, ".claude", "claude-kit.json").write_text('{"owed": {"file": "due.md"}}', encoding="utf-8")
code, out, err = run(root, "--since", start)
case("the settings name the file", code == 0 and "first thing" in out and "second thing" not in out, out + err)
code, out, err = run(root, "--since", start, "--file", "OWED.md")
case("--file wins over the settings", code == 0 and "second thing" in out, out + err)

bare = tempfile.mkdtemp(prefix="session-owed-bare-")
git(bare, "init", "-q")
Path(bare, "README.md").write_text("x\n", encoding="utf-8")
git(bare, "add", "-A")
git(bare, "commit", "-q", "-m", "start")
code, out, err = run(bare, "--since", "HEAD")
case("a repository without the file owes nothing", code == 0 and out == "", out + err)

print(f"{len(failures)} failures")
if failures:
    print("\n".join(failures))
    sys.exit(1)
