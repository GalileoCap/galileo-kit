# Decisions

## Suppressions awaiting the owner's approval

Every gate runs at its strictest setting, and a suppression in the code is a numbered row here, cited beside the marker (`decisions.md, <n>`). `session-suppressions check` holds the two together. A row moves to the next table on the owner's word and keeps its number.

| # | Where | Suppression | Why |
| --- | --- | --- | --- |
| 1 | `plugins/session-kit/codeintel/tests/test_recipes.py` | ruff `S603` on a `subprocess.run` | The argv is fixed: the pinned ast-grep and the test's own paths. |
| 2 | `plugins/session-kit/hooks/test_format.py` | ruff `BLE001` on an `except Exception` | The test runner reports a case that raises as a failed case instead of stopping the run. |
| 3 | `plugins/session-kit/hooks/test_pyright_env.py` | ruff `BLE001` on an `except Exception` | The same runner shape as row 2. |
| 4 | `plugins/session-kit/tells/src/session_tells/readers/command.py` | ruff `S603` on a `subprocess.run` | The argv is the project's own prose command from `claude-kit.json`, run without a shell. |

## Suppressions the owner approved

None yet.
