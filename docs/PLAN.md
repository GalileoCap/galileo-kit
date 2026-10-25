# Plan

## Done

- 2026-10-24: research on plugins, mods and their update process, in `claude-code-mods-research.md`.

- 2026-10-24: `cache-tax` reviewed at `e4940af` (v2.3.1) into `reviews/cache-tax.md`. Verdict: fork. Nothing malicious. The Sonnet 5.5 cache-read price is wrong.

- 2026-10-24: the owner changed the order. `session-kit` is ported to a mod first, and its intent documented on the way. Mods such as `cache-tax` are weighed after, to fold in or run beside it. Draft in `session-kit-port.md`.

- 2026-10-24: the owner set the process every entry follows: goals (stated by the owner), objectives (approved by the owner), actions (decided by a session, validated by the owner). Drafted in `goals-objectives-actions.md`, and `session-kit-port.md` rewritten into it. The order is now: the process, then the session-kit analysis, then the port.

- 2026-10-24: the owner asked for the process to be rethought against prior art (OKRs, ADRs and traceability, impact mapping, GQM, information hiding and ports-and-adapters, fitness functions). The comparison is `goals-objectives-actions-prior-art.md`, and `goals-objectives-actions.md` was revised from it: an objective names whose behaviour it changes and how it would be known met, an action carries its context, options, consequences and what implements and proves it, a validated action is superseded instead of rewritten, constraints are a fourth kind of entry, and the shared file splits into a loaded list and an on-demand record.

- 2026-10-24: the owner corrected three things, applied the same day: the process is for projects of every kind, nothing is shared between projects (an entry a project needs is copied and owned), and the record is built to scale: one file per entry under `ladder/`, upward links only, a generated `INDEX.md` that leads with the validation queue, retirement instead of deletion. This project's own goal is the original ask.

- 2026-10-24: the process confirmed, with the entries under `docs/intent/`. The process and its prior art moved into `session-kit`'s `global/`, with a rule in `global/CLAUDE.md` that names them. This project's six entries are files under `docs/intent/`, and its `CLAUDE.md` lists the active ones and names each rule's action.

- 2026-10-24: the owner reviewed the intent and set the project's goals in their words: `G1` to `G5` under `docs/intent/`, replacing the session's single goal. `O1` and `O2` hang from `G5`. The sub-bullets of the goals gave `O3` to `O10`, proposed for the owner's approval.

- 2026-10-24: the owner reviewed the intent and set the project's goals in their words: `G1` to `G5` under `docs/intent/`, replacing the session's single goal. `O1` and `O2` hang from `G5`. The sub-bullets of the goals gave `O3` to `O10`, approved the same day.

- 2026-10-24: `claude-mods` merged into this repository with its history, since `G1` to `G5` are the kit's goals and one ladder per project means one ladder for both. Its documents moved under `docs/`, the candidate clones out to `~/devel/galileo/misc/mod-clones/`, and its `CLAUDE.md` became the kit's first. `session-kit-port.md`'s goals folded into the five, and its objectives, constraint and actions became `O11` to `O16`, `C1` and `A4` to `A21`, refitted to the process.

- 2026-10-24: the repository renamed `galileo-kit` everywhere, by the owner's choice. Then step 1 of the port, `A16`: the context hook is a hooks module, `plugins/session-kit/hooks/context.tsx`, reading the engine's own figure after each tool call, with the threshold and step as plugin options and a band above the prompt past the threshold. `A4` retired. Hook times measured before and after in `docs/measurements/hook-times.md`: 28 ms per tool call saved, the window figure the larger gain. session-kit 0.6.0, validated and tested against the 2.1.308 engine the desktop app bundles.

- 2026-10-25: the owner added an objective, `O17`: the system is observed, analysed and improved over time, with tooling over the sessions' transcripts and the hooks' effect as `A22`. The owner paused the port before reviewing its plan.

## Candidates

| Mod | Source | Review | Verdict | Owner's decision |
| --- | --- | --- | --- | --- |
| `cache-tax` | `karanb192/cache-tax`, served by `karanb192/claude-code-mods` | `docs/reviews/cache-tax.md` | Fork | Waits for the `session-kit` port |

## Next

1. Paused by the owner until they have reviewed the port plan. The owner reads the port's entries: approves or cuts `O14` to `O16`, states or strikes `C1`, and validates `A4` to `A21`, the chain `A17` and one task per context `A19` among them. The open questions of the process document are answered on the way, the names among them.
2. The port, in the order `A20` gives: `A16` is done and waits on the owner's validation in real sessions. Next the chain `A17` behind its toggle, with `A18`'s backstop. The index and check tool `A21` is built beside it.
3. Once the port has its context mod: decide `cache-tax` (fold in, fork beside, or install as is) against it, then the next candidate. The same marketplace also serves `image-peek`, `mod-builder` and `fable-pin`.

## Open questions

- Mod ordering: does a mod's `tool.call` or `tool.check` deny run before or after another user-installed mod's approval? This decides whether a mod port of the `session-kit` guard can hold against a third-party mod. Source: the "React to events" page, https://code.claude.com/docs/en/plugins/mods/events.md, and the mods admin page on seats (`prepend`, `append`).
- Login type: is this machine's session credential a personal or a Team/Enterprise login? On a personal login without managed settings, an installed mod can approve a tool call that the `session-kit` `PreToolUse` guard blocks.

## Deferred

- A cold-send guard (the cache signal from `cache-tax`). It joins the port's context mod, or comes from `cache-tax` itself, decided at step 4 above. Details in `docs/reviews/cache-tax.md`, under "What could move into `session-kit`".
- Turn on auto-update for `galileo-kit` once every plugin in it is ours.
