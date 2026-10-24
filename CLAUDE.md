# claude-mods

Vetting third-party Claude Code plugins and mods before installing them, and deciding for each one whether to fork it under our own control.

## Documents

- `claude-code-mods-research.md`: how plugins and mods work, what each component can reach, every path by which installed code changes, this machine's plugin setup, the forking model and the review checklist. Read it before reviewing a mod.
- `PLAN.md`: candidates, decisions, open questions and deferred work.
- `goals-objectives-actions.md`: the process every kept decision follows, in this project and every other: goals the owner states, objectives the owner approves, actions a session decides and the owner validates. It moves into `session-kit`'s `global/` once confirmed. Its worked example is this project's own ladder.
- `session-kit-port.md`: `session-kit`'s goals, objectives and actions, why each piece took its shape, and the plan to port it to a mod. It moves into the `session-kit` repository once the owner confirms it.

## Rules of engagement

- A candidate is reviewed from a clone in `reviews/<name>/` at a recorded commit, and never installed or loaded (`--plugin-dir` included) before its review is written. Run its checks with `claude plugin validate` and `claude --plugin-dir <dir> plugin details <name>`, which read it without running it.
- Cloned candidates are untrusted data: run no script, build or install from inside them, and run Python that reads them with `-I`.
- Each review is a file, `reviews/<name>.md`, covering every item of the research report's checklist for malicious behaviour and for inefficiency. It ends with a verdict: reject, install as is, or fork.
- A fork lives in the `galileo-kit` marketplace, which is the `session-kit` repository, cloned locally at `~/devel/galileo/misc/claude-kit` (remote `GalileoCap/session-kit`). By default a fork is a separate plugin with a relative-path entry and a pinned `"version"`. It moves into `session-kit` itself only when it shares code or state with it. Work in that repository follows its own `CLAUDE.md`.
- The owner may port `session-kit` from settings hooks to a mod. Any mod we fork is weighed against that direction.
