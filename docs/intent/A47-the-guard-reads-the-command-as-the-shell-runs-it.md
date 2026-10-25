---
id: A47
from: [O5]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/hooks/guard.py]
proven_by: [plugins/session-kit/hooks/test_guard.py]
supersedes: []
---

# A47 The guard reads the command as the shell runs it

Before any rule of `A6` (the guard refuses by regex) matches, `guard.py` blanks the command's heredoc bodies and its single- and double-quoted text, except a body or a double-quoted string that holds `$(` or a backtick, which the shell runs. A segment starts at the text's start, at a separator (`;`, `&`, `|`), at a subshell's `(` or at a substitution's backtick. The two test-runner rules (`-x`, output piped inline) match the runner only where a segment starts, behind an optional launcher (`uv run`, `poetry run`, `pipenv run`, `npx`, `pnpm exec`, `yarn run`, `python -m`, `env`, `time`, `nice`, `session-watched`) with its words, and an optional path prefix, and never as part of a longer word.

## Context

On 2026-10-25 the installed guard refused two calls of a session for text they only quoted: a `git reset --hard` inside a JSON string after a semicolon, and a `grep` whose pattern named `pytest` and whose output went to `head`. The test-runner rules matched the runner's name anywhere in the text. rulebook-guard (`hamzafer/claude-code-mods`) blanks quoted text and heredoc bodies before matching.

## Options

- Blank every quoted string and heredoc body, as rulebook-guard does. Rejected: `"$(git reset --hard)"` runs, and would pass.
- Blank them unless they hold a substitution. Taken. A string that holds one is matched whole, so `"$(ls); git reset --hard"` is refused for its second part too: the guard errs toward refusing.
- Parse the command with a shell grammar. Rejected: a dependency for a hook that runs on every Bash call, and the rules stay regexes by `A6`.

## Consequences

A git command inside a Python heredoc is not seen, as it was not before (it followed no separator). A launcher outside the list (`make test` calling pytest) hides the runner from the rules, which the project's `test_commands` setting is for. The amend rule reads the blanked text too.

## Proof

The guard's cases allow the two false refusals, a runner named after `echo`, a flag in a commit message and `-x` in a script body. They refuse `-x` behind `uv run` and `session-watched`, a runner behind `python -m` piped, a substitution in double quotes and in a heredoc body, and a project runner behind `./` piped. Six cases failed on 0.22.0.
