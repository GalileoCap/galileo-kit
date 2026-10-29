from __future__ import annotations

"""PreToolUse: refuse what a regex can check and prose has not held.

A rule is here when breaking it is mechanical, the check has few false
positives, and a reminder in a CLAUDE.md has already failed to hold it.
A deny that misfires costs more than no hook, so each pattern is narrow
and the carve-outs are honoured: `git stash push -u -m` is allowed,
`timeout` inside a script body is allowed, amending an unpushed commit is
allowed. The rules read the command as the shell runs it: quoted text and
heredoc bodies are blanked first, so a commit message or a JSON string that
names a command is not taken for one, unless it holds a `$(...)` or a
backtick, which runs. The body of a heredoc whose delimiter is quoted
(`<<'EOF'`) never runs, and is always blanked.

A project adds its own test runners to the lists below in
`.claude/claude-kit.json`:

    {"test_commands": ["scripts/test", "scripts/check"]}

Each entry is a literal command name, matched where it starts a command
segment, behind a path (`./scripts/test`) or a launcher (`uv run`,
`session-watched --`) or not.
"""

import json
import os
import re
import subprocess
import sys

# The runners the -x and piped-output rules apply to.
BUILTIN_TEST_COMMANDS = [
    "pytest", "vitest", "jest", "playwright test", "cargo test", "go test",
    "npm test", "pnpm test", "yarn test",
]

# Where a command segment starts: the text, a separator, a subshell or a substitution.
START = r"(^|[;&|(`])\s*"
AMEND = re.compile(START + r"git\s+commit[^;&|]*--amend")

# What may stand between a segment's start and a test runner: a tool that runs it, with its own options.
LAUNCHER = r"(?:uv\s+run|poetry\s+run|pipenv\s+run|npx|pnpm\s+exec|yarn\s+run|python3?\s+-m|command(?!\s+-[vV])|env|time|nice|session-watched)"

HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n[\s\S]*?\n\s*\2\s*(?=\n|$)")
SINGLE_QUOTED = re.compile(r"'[^']*'")
DOUBLE_QUOTED = re.compile(r'"(?:[^"\\]|\\.)*"')
RUNS = re.compile(r"\$\(|`")


def _unless_it_runs(blank: str):
    def replace(match: re.Match[str]) -> str:
        text = match.group(0)
        return text if RUNS.search(text) else blank

    return replace


def _heredoc(match: re.Match[str]) -> str:
    # A quoted delimiter (<<'EOF') keeps the body literal, so a backtick in it never runs.
    return " " if match.group(1) else _unless_it_runs(" ")(match)


def bare(cmd: str) -> str:
    """The command as the shell runs it: heredoc bodies and quoted text blanked, except one holding a substitution."""
    cmd = HEREDOC.sub(_heredoc, cmd)
    cmd = SINGLE_QUOTED.sub("''", cmd)
    return DOUBLE_QUOTED.sub(_unless_it_runs('""'), cmd)


def project_test_commands(cwd: str) -> list[str]:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or cwd
    try:
        with open(os.path.join(root, ".claude", "claude-kit.json"), encoding="utf-8") as fh:
            listed = json.load(fh).get("test_commands", [])
    except (OSError, ValueError, AttributeError):
        return []
    return [c for c in listed if isinstance(c, str) and c]


def bash_rules(cwd: str) -> list[tuple[re.Pattern[str], str]]:
    names = BUILTIN_TEST_COMMANDS + project_test_commands(cwd)
    test_cmd = "(" + "|".join(re.escape(n) for n in names) + ")"
    # A runner where a segment starts, behind a launcher and its words, or a path, or neither.
    test_start = START + rf"(?:{LAUNCHER}(?:\s+\S+)*?\s+)?(?:\S*/)?{test_cmd}(?![\w.-])"
    return [
        (
            re.compile(START + r"git\s+commit[^|;&]*--no-verify"),
            "git commit --no-verify skips the hooks. Fix the failure instead of bypassing it.",
        ),
        (
            re.compile(START + r"git\s+push[^|;&]*(--force(\s|$)|\s-f(\s|$))"),
            "git push --force rewrites the remote. Use --force-with-lease if it is intended.",
        ),
        (
            re.compile(START + r"git\s+rebase[^|;&]*(-i|--interactive)(\s|$)"),
            "git rebase -i needs an editor and cannot run here. Squash with git reset --soft "
            "and a new commit instead.",
        ),
        (
            re.compile(START + r"git\s+reset[^|;&]*--hard"),
            "git reset --hard destroys uncommitted work. Prefer git reset --soft.",
        ),
        (
            re.compile(rf"{test_start}[^;&|]*\s(-x|--exitfirst)(\s|$|\))"),
            "-x / --exitfirst hides every failure after the first. Let the suite finish and "
            "read the whole list.",
        ),
        (
            re.compile(START + r"timeout\s+\d"),
            "Do not wrap a Bash call in shell `timeout`: the tool has its own `timeout` "
            "parameter, in milliseconds where the shell's is seconds. Inside a script it is fine.",
        ),
        (
            re.compile(rf"{test_start}[^;&|]*\|\s*(grep|head|tail|less|more)(\s|$|\))"),
            "Write test output to a file (`&> log`) and search the file. Piping it inline "
            "throws the rest away and forces a rerun.",
        ),
        (
            re.compile(START + r"git\s+stash\s*(pop|$|[;&|])"),
            "A bare git stash / stash pop works on a stack shared by every worktree, and "
            "another session may pop yours. Use a temporary WIP commit, or "
            "`git stash push -u -m \"<tag>\"` then `git stash apply <sha>`.",
        ),
    ]


def head_is_published(cwd: str) -> bool:
    """True when HEAD is already on a remote branch."""
    try:
        out = subprocess.run(
            ["git", "branch", "-r", "--contains", "HEAD"],
            cwd=cwd or None, capture_output=True, text=True, timeout=10,
        )
        return bool(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return False  # cannot tell, so do not block


def deny(reason: str) -> None:
    json.dump(
        {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }},
        sys.stdout,
    )


def check_bash(cmd: str, cwd: str) -> None:
    text = bare(cmd)
    for pattern, reason in bash_rules(cwd):
        if pattern.search(text):
            deny(reason)
            return
    if AMEND.search(text) and head_is_published(cwd):
        deny("HEAD is already on a remote branch. Never amend a pushed commit; commit on top.")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    tool = payload.get("tool_name", "")
    try:
        if tool == "Bash":
            check_bash(
                str((payload.get("tool_input") or {}).get("command", "")),
                str(payload.get("cwd", "")),
            )
        elif tool == "Artifact":
            deny(
                "A deliverable is a file in the project, never a published page. Write it as "
                "markdown or a plain .html beside the work, or in the scratchpad, and answer "
                "with its path."
            )
    except Exception:  # a guard must never break the session it guards
        return


if __name__ == "__main__":
    main()
