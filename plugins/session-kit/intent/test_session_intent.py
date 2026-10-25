"""Cases for session_intent.py. Run it: python3 intent/test_session_intent.py

Each case builds a small project in a temporary directory, runs the command
over it and reads its exit code and lines.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = str(Path(__file__).with_name("session_intent.py"))

GOAL = "---\nid: G1\nsource: owner\nstatus: stated 2026-10-01\n---\n\n# G1 A goal\n\n> In the owner's words.\n"
OBJECTIVE = (
    "---\nid: O1\nfrom: [G1]\nsource: inferred\nstatus: approved 2026-10-02\n---\n\n"
    "# O1 An approved objective\n\nText.\n\n## Changes\n\nThe work.\n\n## Known by\n\nA check.\n"
)
PROPOSED = (
    "---\nid: O2\nfrom: [G1]\nsource: inferred\nstatus: proposed 2026-10-03\n---\n\n"
    "# O2 A proposed objective\n\nText.\n"
)
ACTION = (
    "---\nid: A1\nfrom: [O1]\nsource: session\nstatus: decided 2026-10-04\nkind: behaviour\n"
    "implemented_by: [CLAUDE.md]\nproven_by: unproven\nsupersedes: [A2]\n---\n\n"
    "# A1 A decided action\n\nText.\n"
)
RETIRED = (
    "---\nid: A2\nfrom: [O1]\nsource: session\nstatus: retired 2026-10-04\nkind: behaviour\n"
    "implemented_by: [CLAUDE.md]\nproven_by: unproven\nsupersedes: []\n---\n\n"
    "# A2 A retired action\n\nText.\n"
)
VALIDATED = (
    "---\nid: A3\nfrom: [O1]\nsource: owner\nstatus: validated 2026-10-01\nkind: check\n"
    "implemented_by: [not yet written: a tool]\nproven_by: unproven\nsupersedes: []\n---\n\n"
    "# A3 A validated action\n\nText.\n"
)
CONSTRAINT = "---\nid: C1\nfrom: []\nsource: owner\nstatus: stated 2026-10-05\n---\n\n# C1 A constraint\n\nWhen X, Y.\n"
CLAUDE_MD = (
    "# Project\n\n## Intent\n\n- `G1` A goal.\n- `O1` An approved objective. From `G1`.\n"
    "- `O2` A proposed objective. From `G1`. Proposed.\n- `C1` A constraint.\n\n## Rules\n\n- A rule. (`A1`)\n"
)

CLEAN = {
    "docs/intent/G1-a-goal.md": GOAL,
    "docs/intent/O1-an-approved-objective.md": OBJECTIVE,
    "docs/intent/O2-a-proposed-objective.md": PROPOSED,
    "docs/intent/A1-a-decided-action.md": ACTION,
    "docs/intent/A2-a-retired-action.md": RETIRED,
    "docs/intent/A3-a-validated-action.md": VALIDATED,
    "docs/intent/C1-a-constraint.md": CONSTRAINT,
    "CLAUDE.md": CLAUDE_MD,
}


def project(files: dict[str, str]) -> str:
    root = tempfile.mkdtemp(prefix="session-intent-")
    for name, text in files.items():
        path = Path(root, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def run(root: str, *args: str) -> tuple[int, str]:
    out = subprocess.run(
        [sys.executable, TOOL, *args, "--root", root],
        capture_output=True, text=True, timeout=30,
    )
    return out.returncode, out.stdout + out.stderr


def with_change(files: dict[str, str], name: str, old: str, new: str) -> dict[str, str]:
    assert old in files[name], (name, old)
    return {**files, name: files[name].replace(old, new)}


failures: list[str] = []


def case(name: str, ok: bool, detail: str = "") -> None:
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        failures.append(name + ("\n" + detail if detail else ""))


# The index: the queue first, oldest first, then the ladder downward, then the retired.
root = project(CLEAN)
code, out = run(root, "index")
index = Path(root, "docs/intent/INDEX.md").read_text(encoding="utf-8")
case("index writes INDEX.md and exits 0", code == 0 and index != "", out)
queue = index[index.index("## Waiting on the owner"):index.index("## Goals")]
case("the queue holds the proposed objective and the decided action, oldest first",
     queue.index("O2") < queue.index("A1") and "A3" not in queue and "A2" not in queue, queue)
ladder = index[index.index("## Goals"):]
case("the ladder lists the objective under its goal and the action under its objective",
     ladder.index("G1") < ladder.index("O1") < ladder.index("A1") and "[A1 A decided action](A1-a-decided-action.md)" in index, ladder)
case("the retired action is listed last with its successor",
     index.rindex("A2 A retired action") > index.index("## Retired") and "superseded by `A1`" in index, index)
case("the constraint is listed", "C1 A constraint" in ladder, ladder)
case("the index says it is generated", "session-intent index" in index.splitlines()[2], index)

# The check: a clean ladder with a current index passes.
code, out = run(root, "check")
case("check passes on a clean ladder with a current index", code == 0 and out.strip() == "", out)

# Each problem the entry names.
problems: list[tuple[str, dict[str, str], str]] = [
    ("an id that does not resolve",
     with_change(CLEAN, "docs/intent/A1-a-decided-action.md", "from: [O1]", "from: [O9]"), "O9"),
    ("a path in implemented_by that does not exist",
     with_change(CLEAN, "docs/intent/A1-a-decided-action.md", "implemented_by: [CLAUDE.md]", "implemented_by: [hooks/gone.py]"), "hooks/gone.py"),
    ("an approved objective with no action",
     with_change(with_change(CLEAN, "docs/intent/A1-a-decided-action.md", "from: [O1]", "from: [O2]"),
                 "docs/intent/A3-a-validated-action.md", "from: [O1]", "from: [O2]"), "O1"),
    ("an action that names no objective",
     with_change(CLEAN, "docs/intent/A1-a-decided-action.md", "from: [O1]", "from: []"), "A1"),
    ("a status without a date",
     with_change(CLEAN, "docs/intent/O1-an-approved-objective.md", "status: approved 2026-10-02", "status: approved"), "date"),
    ("a retired entry nothing supersedes",
     with_change(CLEAN, "docs/intent/A1-a-decided-action.md", "supersedes: [A2]", "supersedes: []"), "A2"),
    ("an active objective missing from the CLAUDE.md block",
     with_change(CLEAN, "CLAUDE.md", "- `O1` An approved objective. From `G1`.\n", ""), "O1"),
    ("a retired entry listed in the CLAUDE.md block",
     with_change(CLEAN, "CLAUDE.md", "- `C1` A constraint.\n", "- `C1` A constraint.\n- `A2` Gone.\n"), "A2"),
    ("a file whose name does not carry its id",
     {**CLEAN, "docs/intent/A9-wrong.md": ACTION.replace("id: A1", "id: A8")}, "A9-wrong.md"),
    ("an action without its fields",
     with_change(CLEAN, "docs/intent/A1-a-decided-action.md", "kind: behaviour\n", ""), "kind"),
]
for name, files, needle in problems:
    root = project(files)
    run(root, "index")
    code, out = run(root, "check")
    case(f"check fails on {name}", code == 1 and needle in out, out)

# A stale index is a problem of its own, and a missing one too.
root = project(CLEAN)
code, out = run(root, "check")
case("check fails when INDEX.md is missing", code == 1 and "INDEX.md" in out, out)
run(root, "index")
Path(root, "docs/intent/INDEX.md").write_text("stale\n", encoding="utf-8")
code, out = run(root, "check")
case("check fails when INDEX.md is stale", code == 1 and "INDEX.md" in out, out)

# An approved objective may say "no action yet" instead of naming one.
root = project(with_change(with_change(with_change(CLEAN, "docs/intent/A1-a-decided-action.md", "from: [O1]", "from: [O2]"),
                           "docs/intent/A3-a-validated-action.md", "from: [O1]", "from: [O2]"),
                           "docs/intent/O1-an-approved-objective.md", "Text.\n", "No action yet: the work has not reached it.\n"))
run(root, "index")
code, out = run(root, "check")
case("an approved objective that says no action yet passes", code == 0, out)

# A retired action's paths are not checked: what implemented it may be gone by design.
root = project(with_change(CLEAN, "docs/intent/A2-a-retired-action.md", "implemented_by: [CLAUDE.md]", "implemented_by: [hooks/gone.py]"))
run(root, "index")
code, out = run(root, "check")
case("a retired action's gone path is not a problem", code == 0, out)

# A placeholder in implemented_by is not a path.
root = project(CLEAN)
run(root, "index")
code, out = run(root, "check")
case("a 'not yet written' placeholder is not read as a path", code == 0, out)

# names prints each entry's id and name, all or the ones asked for, and refuses an unknown id.
root = project(CLEAN)
code, out = run(root, "names")
case("names prints every entry with its name, the ladder downward, the retired one marked",
     code == 0 and out.index("G1 A goal") < out.index("O1 An approved objective") < out.index("A1 A decided action") and "A2 A retired action (retired)" in out, out)
code, out = run(root, "names", "A1", "O2")
case("names prints only the ids asked for", code == 0 and out.strip().splitlines() == ["A1 A decided action", "O2 A proposed objective"], out)
code, out = run(root, "names", "A9")
case("names fails on an unknown id", code == 1 and "A9: no such entry" in out, out)

# next claims the following id of a level under the lock, from the record's highest or the last claim, and never twice.
root = project(CLEAN)
state = tempfile.mkdtemp(prefix="session-intent-state-")
code, out = run(root, "next", "A", "--state", state, "--title", "The first claim")
case("next A gives the id after the record's highest action", code == 0 and out.strip() == "A4", out)
code, out = run(root, "next", "A", "--state", state)
case("a second claim moves on although no file was written", code == 0 and out.strip() == "A5", out)
log = Path(state, "claims.log").read_text(encoding="utf-8").splitlines()
case("the claims log names each id with its checkout and title",
     len(log) == 2 and log[0].startswith("A4 ") and log[0].endswith(" The first claim") and Path(root).name in log[0], "\n".join(log))
code, out = run(root, "next", "objective", "--state", state)
case("a level may be named by its word", code == 0 and out.strip() == "O3", out)
code, out = run(root, "next", "X", "--state", state)
case("an unknown level is refused", code == 2 and "no such level" in out, out)
Path(state, "G.next").write_text("1\n", encoding="utf-8")
code, out = run(root, "next", "G", "--state", state)
case("a counter below the record's highest is raised to it", code == 0 and out.strip() == "G2", out)
Path(state, ".lock").mkdir()
dead = subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"], capture_output=True, text=True, timeout=30).stdout.strip()
Path(state, ".lock", "pid").write_text(dead, encoding="utf-8")
code, out = run(root, "next", "C", "--state", state)
case("a lock left by a dead process is reclaimed", code == 0 and out.strip() == "C2" and not Path(state, ".lock").exists(), out)
import concurrent.futures
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(lambda _: run(root, "next", "A", "--state", state), range(8)))
ids = {out.strip() for _, out in results}
case("eight claims at once get eight distinct ids", all(code == 0 for code, _ in results) and ids == {f"A{n}" for n in range(6, 14)}, str(sorted(ids)))

LEVELS_SETTINGS = (
    '{"intent": {"directory": "notes/intent", "levels": ['
    '{"letter": "E", "word": "epic", "statuses": ["open", "done", "retired"], "waiting": "open", "ask": "close", "listed": true}, '
    '{"letter": "T", "word": "task", "from": ["E"], "statuses": ["planned", "done", "retired"], "waiting": "planned", "ask": "plan", "fields": ["kind"]}'
    "]}}"
)
EPIC = "---\nid: E1\nsource: owner\nstatus: open 2026-10-01\n---\n\n# E1 An epic\n\nText.\n"
TASK = "---\nid: T1\nfrom: [E1]\nsource: session\nstatus: planned 2026-10-02\nkind: step\n---\n\n# T1 A task\n\nText.\n"
CUSTOM = {
    ".claude/claude-kit.json": LEVELS_SETTINGS,
    "notes/intent/E1-an-epic.md": EPIC,
    "notes/intent/T1-a-task.md": TASK,
    "CLAUDE.md": "# P\n\n## Intent\n\n- `E1` An epic.\n",
}
root = project(CUSTOM)
code, out = run(root, "index")
case("the levels and the directory come from the settings", code == 0 and "2 entries" in out, out)
index = Path(root, "notes/intent/INDEX.md").read_text(encoding="utf-8")
case("a root level is a section named by its word, its children nested", "## Epics" in index and "- [E1 An epic](E1-an-epic.md): open 2026-10-01\n  - [T1 A task](T1-a-task.md): planned 2026-10-02 (step)" in index, index)
case("the waiting status and its ask come from the level", "(an epic to close)" in index and "(a task to plan)" in index, index)
code, out = run(root, "check")
case("a record under its own levels passes", code == 0 and out == "", out)
state = tempfile.mkdtemp(prefix="session-intent-state-")
code, out = run(root, "next", "T", "--state", state)
case("next takes a level from the settings", code == 0 and out.strip() == "T2", out)
code, out = run(root, "next", "task", "--state", state)
case("a settings level may be named by its word", code == 0 and out.strip() == "T3", out)
code, out = run(root, "next", "A", "--state", state)
case("a level outside the settings is refused, naming the ones there", code == 2 and "one of E, T" in out, out)
code, out = run(root, "names")
case("names prints the ladder in the settings' order", code == 0 and out == "E1 An epic\nT1 A task\n", out)
code, out = run(project(with_change(CUSTOM, "notes/intent/T1-a-task.md", "planned 2026-10-02", "decided 2026-10-02")), "check")
case("a status outside the level's list is a problem naming the level", code == 1 and "none of planned, done, retired for a task" in out, out)
code, out = run(project(with_change(CUSTOM, "notes/intent/T1-a-task.md", "kind: step\n", "")), "check")
case("a level's own fields are required", code == 1 and "a task without `kind`" in out, out)
code, out = run(project(with_change(CUSTOM, "CLAUDE.md", "- `E1` An epic.\n", "- `T1` A task.\n")), "check")
case("the Intent block lists the levels marked listed and no other", code == 1 and "lacks the active entry `E1`" in out and "lists `T1`, which is retired or not listed" in out, out)

if failures:
    print(f"\n{len(failures)} failed")
    for f in failures:
        print(f)
    sys.exit(1)
print("\nall passed")
