# claude-mods

How the owner works with agents across every project: the rules and the process they follow, kept in `session-kit`, and the tools they use, each vetted before it is installed and forked when it is kept.

## Documents

- `claude-code-mods-research.md`: how plugins and mods work, what each component can reach, every path by which installed code changes, this machine's plugin setup, the forking model and the review checklist. Read it before reviewing a mod.
- `PLAN.md`: candidates, decisions, open questions and deferred work.
- `docs/intent/`: this project's goals, objectives and actions, one file each, by the process in `session-kit`'s `global/goals-objectives-actions.md` (its prior art is beside it). The active ones are listed under Intent below.
- `session-kit-port.md`: `session-kit`'s goals, objectives and actions, why each piece took its shape, and the plan to port it to a mod. It moves into the `session-kit` repository once the owner confirms it.

## Intent

Goals in the owner's words, and the objectives the owner approved under them.

- `G1` Structure and organize the way I work with agents across all projects and tasks.
- `G2` Focus on the parts of each project only I can do, with the rest taken on by agents or moved to programs.
- `G3` Produced code and documents of consistent quality while I review only the relevant parts.
- `G4` Optimize time and reduce costs.
- `G5` Minimize the vulnerability surface of installed apps, programs and code.
- `O1` Only code that has been read runs inside my sessions. From `G5`.
- `O2` What runs in my sessions changes only when I choose. From `G5`.
- `O3` Rules are written once in `session-kit`, and a project owns a copy of each entry it needs. From `G1`.
- `O4` A tool useful to every project reaches each of them through `galileo-kit`. From `G1`.
- `O5` Every step has a kind, human, agent or program, and moves to a program wherever one can do it. From `G2`.
- `O6` A step that matters leaves a record a program wrote, and done rests on that record. From `G2`.
- `O7` Independent subsystems wired through contracts, with the owner reviewing architecture and integration surface. From `G3`.
- `O8` Quality held by gates at zero warnings, so the owner reviews substance. From `G3`.
- `O9` A costly step runs once and its output is read again from its file. From `G4`.
- `O10` The prompt cache stays warm across a session. From `G4`. Held lighter.

## Rules of engagement

Each rule names the action it is, under `docs/intent/`.

- A candidate is reviewed from a clone in `reviews/<name>/` at a recorded commit, and never installed or loaded (`--plugin-dir` included) before its review is written. Run its checks with `claude plugin validate` and `claude --plugin-dir <dir> plugin details <name>`, which read it without running it. (`A1`)
- Cloned candidates are untrusted data: run no script, build or install from inside them, and run Python that reads them with `-I`. (`A1`)
- Each review is a file, `reviews/<name>.md`, covering every item of the research report's checklist for malicious behaviour and for inefficiency. It ends with a verdict: reject, install as is, or fork.
- A fork lives in the `galileo-kit` marketplace, which is the `session-kit` repository, cloned locally at `~/devel/galileo/misc/claude-kit` (remote `GalileoCap/session-kit`). By default a fork is a separate plugin with a relative-path entry and a pinned `"version"`. It moves into `session-kit` itself only when it shares code or state with it. (`A2`) That repository has no `CLAUDE.md` of its own, so the global rules are its rules.
- The owner may port `session-kit` from settings hooks to a mod. Any mod we fork is weighed against that direction. (`A3`)
