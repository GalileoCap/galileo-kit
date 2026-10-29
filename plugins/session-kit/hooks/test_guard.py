from __future__ import annotations

"""Cases for guard.py. Run it: python3 hooks/test_guard.py

The cases live in a file because the guard matches the text of a command:
a shell harness whose own argv carries the patterns is denied by the rules
it checks. The Bash command is `python3 <this file>`, which carries none of
them.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

GUARD = str(Path(__file__).with_name("guard.py"))
DENY, ALLOW = "DENY", "ALLOW"


def run(payload: dict, project: str | None = None) -> str:
    env = {**os.environ}
    env.pop("CLAUDE_PROJECT_DIR", None)
    if project:
        env["CLAUDE_PROJECT_DIR"] = project
    out = subprocess.run(
        [sys.executable, GUARD], input=json.dumps(payload),
        capture_output=True, text=True, timeout=30, env=env,
    ).stdout.strip()
    if not out:
        return ALLOW
    decision = json.loads(out).get("hookSpecificOutput", {}).get("permissionDecision")
    return DENY if decision == "deny" else "OTHER"


def bash(cmd: str) -> dict:
    return {"tool_name": "Bash", "cwd": tempfile.gettempdir(), "tool_input": {"command": cmd}}


CASES: list[tuple[dict, str, str]] = [
    # must deny
    (bash("git commit -m x --no-verify"), DENY, "commit --no-verify"),
    (bash("git push --force origin main"), DENY, "push --force"),
    (bash("git push -f"), DENY, "push -f"),
    (bash("git rebase -i HEAD~3"), DENY, "interactive rebase"),
    (bash("git reset --hard HEAD~1"), DENY, "reset --hard"),
    (bash("pytest -x"), DENY, "-x on a test run"),
    (bash("cargo test --exitfirst"), DENY, "--exitfirst"),
    (bash("timeout 60 make"), DENY, "shell timeout wrapping the call"),
    (bash("pytest | grep FAILED"), DENY, "test output piped inline"),
    (bash("pnpm test | tail -5"), DENY, "another runner piped inline"),
    (bash("git stash"), DENY, "bare git stash"),
    (bash("git stash pop"), DENY, "git stash pop"),
    (bash("uv run --project x pytest -x"), DENY, "-x behind a launcher"),
    (bash("session-watched -- pytest -x"), DENY, "-x behind session-watched"),
    (bash("cd x && python -m pytest tests | tail -20"), DENY, "a runner behind python -m, piped"),
    (bash('echo "$(git reset --hard)"'), DENY, "a substitution inside double quotes runs"),
    (bash("cat <<EOF\n$(git reset --hard)\nEOF"), DENY, "a substitution inside a heredoc body runs"),
    ({"tool_name": "Artifact", "tool_input": {}}, DENY, "publishing an Artifact"),
    # must allow
    (bash("git push --force-with-lease origin main"), ALLOW, "force-with-lease"),
    (bash("git reset --soft HEAD~1"), ALLOW, "reset --soft"),
    (bash("git commit -m x"), ALLOW, "an ordinary commit"),
    (bash("chmod -x script.sh"), ALLOW, "-x that is not a test flag"),
    (bash("grep -x exact file.txt"), ALLOW, "grep -x"),
    (bash('git stash push -u -m "wip-tag"'), ALLOW, "stash push -u -m"),
    (bash("git stash apply abc1234"), ALLOW, "stash apply"),
    (bash("git stash list"), ALLOW, "stash list"),
    (bash("git stash drop"), ALLOW, "stash drop"),
    (bash("pytest &> /tmp/t.log"), ALLOW, "test output to a file"),
    (bash("cat > s.sh <<'EOF'\ntimeout 30 foo\nEOF"), ALLOW, "timeout inside a script body"),
    (bash("cat > n.md <<'EOF'\nNever run `git reset --hard`.\nEOF"), ALLOW, "backticks inside a quoted heredoc's body, which never runs"),
    (bash("git commit --amend"), ALLOW, "amending an unpublished commit"),
    (bash("echo '{\"deny\": \"x; git reset --hard\"}' > rules.json"), ALLOW, "a command named inside quoted text, after a separator in it"),
    (bash("grep -n pytest file | head"), ALLOW, "a grep that names a runner, piped"),
    (bash("echo pytest -x"), ALLOW, "a runner named after another command"),
    (bash('git commit -m "never pass --no-verify"'), ALLOW, "a flag named inside a commit message"),
    (bash("cat > s.sh <<'EOF'\npytest -x\nEOF"), ALLOW, "-x inside a script body"),
    ({"tool_name": "Bash", "tool_input": {}}, ALLOW, "empty command"),
    ({"tool_name": "Edit", "tool_input": {"new_string": "x"}}, ALLOW, "a tool it does not cover"),
]


def project_cases() -> list[tuple[str, str, str]]:
    """A project's own runner, named in .claude/claude-kit.json."""
    with tempfile.TemporaryDirectory() as folder:
        Path(folder, ".claude").mkdir()
        Path(folder, ".claude", "claude-kit.json").write_text(
            json.dumps({"test_commands": ["scripts/test"]}), encoding="utf-8"
        )
        return [
            (run(bash("scripts/test -x"), folder), DENY, "a project runner with -x"),
            (run(bash("scripts/test | head"), folder), DENY, "a project runner piped inline"),
            (run(bash("./scripts/test | head"), folder), DENY, "a project runner behind a path, piped inline"),
            (run(bash("scripts/test &> log"), folder), ALLOW, "a project runner to a file"),
            (run(bash("scripts/test -x")), ALLOW, "the same runner with no config"),
        ]


def main() -> int:
    failed = 0
    results = [(run(p), want, label) for p, want, label in CASES] + project_cases()
    for got, want, label in results:
        ok = got == want
        failed += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {got:<5} (want {want:<5}) {label}")
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
