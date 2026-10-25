# Hook times

What the settings hooks add to a tool call, measured by `plugins/session-kit/hooks/time_hooks.py`: each command of `hooks.json` run through `bash -c` as the engine runs it, with a payload of its event on stdin, on this machine (Darwin, Python 3 from PATH). Wall time per command, so the shell wrapper and the interpreter start are counted and the engine's own spawn cost is not.

## Before the port, session-kit 0.5.1

Runs per command: 10, the first discarded. Root: /Users/galileo/devel/galileo/misc/galileo-kit/plugins/session-kit

| Event | Matcher | Command | Median ms | Min ms |
| --- | --- | --- | --- | --- |
| baseline |  | `python3 -c pass` | 19 | 18 |
| PreToolUse | Bash|Artifact | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/guard.py"` | 26 | 26 |
| PreToolUse | Bash | `json=$(cat); case "$json" in *python3*"<<"*) printf '%s' ...` | 6 | 6 |
| PostToolUse | Edit|Write|MultiEdit | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/doc_length.py"` | 22 | 22 |
| PostToolUse | Edit|Write|MultiEdit | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/format.py"` | 32 | 31 |
| PostToolUse | Edit|Write|MultiEdit | `command -v uv >/dev/null 2>&1 \|\| exit 0; UV_PROJECT_ENVIR...` | 79 | 77 |
| PostToolUse | Bash | `json=$(cat); case "$json" in *'"bashEditDiff"'*) printf '...` | 7 | 6 |
| PostToolUse | Bash | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/test_log.py"` | 31 | 30 |
| PostToolUse | * | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/context_pressure.py"` | 28 | 27 |

Per tool call, today: a Read or Edit result pays the `*` hook (28 ms). A Bash call pays the guard, the nudge filter, the test log, the Bash edit filter and the `*` hook, about 100 ms. An Edit or Write pays the document-length check, the formatter wrapper, the tells hook and the `*` hook, about 160 ms, before the formatter and the tells rules do their work. The Python start alone is 19 ms, so each hook spends about 10 ms of its own.

The context hook ported in-process (`A16`) removes 28 ms from every tool call, which is a small share of a call that reaches the model. The port's larger gains are elsewhere: the window figure comes from the engine instead of a constant, and the module is what the chain (`A17`) runs on.

## After step 1 of the port, session-kit 0.6.0

The `*` hook is gone: the context figure is read in-process by `hooks/context.tsx`, with no process started. The rest is unchanged.

Runs per command: 10, the first discarded. Root: /Users/galileo/devel/galileo/misc/galileo-kit/plugins/session-kit

| Event | Matcher | Command | Median ms | Min ms |
| --- | --- | --- | --- | --- |
| baseline |  | `python3 -c pass` | 19 | 18 |
| PreToolUse | Bash|Artifact | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/guard.py"` | 26 | 26 |
| PreToolUse | Bash | `json=$(cat); case "$json" in *python3*"<<"*) printf '%s' ...` | 6 | 6 |
| PostToolUse | Edit|Write|MultiEdit | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/doc_length.py"` | 23 | 22 |
| PostToolUse | Edit|Write|MultiEdit | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/format.py"` | 32 | 32 |
| PostToolUse | Edit|Write|MultiEdit | `command -v uv >/dev/null 2>&1 \|\| exit 0; UV_PROJECT_ENVIR...` | 79 | 78 |
| PostToolUse | Bash | `json=$(cat); case "$json" in *'"bashEditDiff"'*) printf '...` | 6 | 6 |
| PostToolUse | Bash | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/test_log.py"` | 31 | 31 |

## After step 3 of the port, session-kit 0.8.0

The nudge filter, the document-length check and the test log are in-process, in `hooks/nudge.ts`, `hooks/doc_length.ts` and `hooks/test_log.ts`, loaded through `hooks/kit.tsx`, the module the engine loads for the plugin. A Bash call now pays the guard and the Bash edit filter, about 32 ms, down from about 100 ms before the port. An Edit or Write pays the formatter wrapper and the tells hook, about 115 ms, down from about 160 ms, before either does its work.

Runs per command: 15, the first discarded. Root: /Users/galileo/devel/galileo/misc/galileo-kit/plugins/session-kit

| Event | Matcher | Command | Median ms | Min ms |
| --- | --- | --- | --- | --- |
| baseline |  | `python3 -c pass` | 19 | 18 |
| PreToolUse | Bash|Artifact | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/guard.py"` | 26 | 26 |
| PostToolUse | Edit|Write|MultiEdit | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/format.py"` | 34 | 32 |
| PostToolUse | Edit|Write|MultiEdit | `command -v uv >/dev/null 2>&1 \|\| exit 0; UV_PROJECT_ENVIR...` | 80 | 79 |
| PostToolUse | Bash | `json=$(cat); case "$json" in *'"bashEditDiff"'*) printf '...` | 6 | 6 |
