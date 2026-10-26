---
id: A60
from: [O1, O8]
source: session
status: decided 2026-10-26
kind: check
implemented_by: [plugins/session-kit/codeintel/src/session_codeintel/footprint.py, plugins/session-kit/codeintel/src/session_codeintel/cli.py, plugins/session-kit/footprint.toml, .claude/claude-kit.json]
proven_by: [plugins/session-kit/codeintel/tests/test_footprint.py]
supersedes: []
---

# A60 The kit's reach held to a reviewed footprint

`session-codeintel footprint` runs the engine's validator over each plugin named under `footprint.plugins` in `.claude/claude-kit.json` and holds what it reports to the plugin's `footprint.toml`. The file keeps the validator's lines under `[validator]`: for each hooks module the events it hooks, its gating hooks, the `$` calls with the functions they are made through, the environment and state it reads and writes, and the state its types declare. They are compared as counts, since their order is the order of registration. Under `[why]` it keeps a reason for each `$` member and each hook event. A line the file lacks, a line it holds that the validator does not print, a member or event with no reason, and a reason for one gone each fail the gate. `--write` takes the footprint again and keeps each reason whose name is still there, so a new reach waits on its reason and reaches the owner as a line of the commit's diff. The engine is the session's own (`CLAUDE_CODE_EXECPATH`), unless `--claude` names another.

## Context

`docs/analyses/mods-for-the-kit.md`, M22, from mod-builder's README: a footprint fixed before code, the events and `$` calls each module may use, diffed against the validator's `calls:` line. The kit's code reached its 24 `$` members and 12 events one action at a time, and nothing recorded all of it or asked why a new one was needed. The validator already reads the module the way the engine loads it, the calls through helpers in other files included (`via`). The engine loads one hooks module per plugin, so it reports `./kit.tsx`, which imports every concern.

## Options

- A footprint per concern, read from each file's source. Rejected: the validator reports the module the engine loads, and reading the TypeScript ourselves would be a second analysis to trust beside the engine's. The `via` names say which helper makes each call, which points at the concern.
- The members alone, without `via`. Rejected: a new function running a process is a reach the member hides when the member is already there. A renamed helper costs a `--write` and a line of the diff.
- A reason for every line. Rejected: the state is declared in `types/index.d.ts` and checked by the validator against it, and the environment is two names. The reasons go where the reach is, the members and the events.
- The settings hooks of `hooks/hooks.json` in the footprint. Rejected: the validator does not print them, and the file is their whole declaration, read in its own diff.
- The engine named by path in the settings. Rejected: the path is one machine's, and the kit runs under the session's own engine.
- The gate as an engine test under `plugin test`. Rejected: a test there cannot run the validator.

## Consequences

session-kit's footprint holds 125 items: 31 hooks, 20 of them gating, 24 `$` members, two environment reads and 16 state keys written, read and declared. Taken on the 2.1.308 engine the desktop app bundles. A plugin's first `--write` asks for every reason, so every member and event is reviewed once. Planted on a copy of the plugin, a direct `$.process.run` in a hook failed the gate. It also showed that once a member is called directly anywhere, the validator drops its `via` list and prints the bare member. The gate runs where an engine that accepts the plugin runs: the terminal's 2.1.296 refuses the kit's module since `gitOutput` takes `$` across an import (`e7c005e`), so the gate refuses there with the engine's error. That refusal is also what an installed kit meets in a terminal session on 2.1.296. The gate is in `iterate.static`, so `/session-kit:iterate` runs it.

## Proof

The cases in `codeintel/tests/test_footprint.py` were written before the code against a stand-in engine that prints a validator's report, and deleted once they passed, as blind tests. Kept: a call the footprint lacks, or a new caller of one, fails naming it, since a gate passing it would let the kit's code reach further unreviewed with nothing said. Run on session-kit with the session's engine, clean at 125 items, and on a copy with a planted call, which failed.
