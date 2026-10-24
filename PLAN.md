# Plan

## Done

- 2026-10-24: research on plugins, mods and their update process, in `claude-code-mods-research.md`.

- 2026-10-24: `cache-tax` reviewed at `e4940af` (v2.3.1) into `reviews/cache-tax.md`. Verdict: fork. Nothing malicious. The Sonnet 5.5 cache-read price is wrong.

- 2026-10-24: the owner changed the order. `session-kit` is ported to a mod first, and its intent documented on the way. Mods such as `cache-tax` are weighed after, to fold in or run beside it. Draft in `session-kit-port.md`.

- 2026-10-24: the owner set the process every entry follows: goals (stated by the owner), objectives (approved by the owner), actions (decided by a session, validated by the owner). Drafted in `goals-objectives-actions.md`, and `session-kit-port.md` rewritten into it. The order is now: the process, then the session-kit analysis, then the port.

## Candidates

| Mod | Source | Review | Verdict | Owner's decision |
| --- | --- | --- | --- | --- |
| `cache-tax` | `karanb192/cache-tax`, served by `karanb192/claude-code-mods` | `reviews/cache-tax.md` | Fork | Waits for the `session-kit` port |

## Next

1. The process. Owner confirms `goals-objectives-actions.md` (its three open questions), then it moves into `session-kit`'s `global/`.
2. The session-kit analysis. Owner reads `session-kit-port.md` under the process: approves or corrects objectives O3 and O6 to O10, settles A4 and A5, and answers the port's questions (the context chain, one task per context, where the documentation lives).
3. The port. Move the approved document into the `session-kit` repository and start there, at step 1 of its order (the context mod with the engine's window), measuring hook times before and after. That work follows the `session-kit` repository's rules.
4. Once the port has its context mod: decide `cache-tax` (fold in, fork beside, or install as is) against it, then the next candidate. The same marketplace also serves `image-peek`, `mod-builder` and `fable-pin`.

## Open questions

- Mod ordering: does a mod's `tool.call` or `tool.check` deny run before or after another user-installed mod's approval? This decides whether a mod port of the `session-kit` guard can hold against a third-party mod. Source: the "React to events" page, https://code.claude.com/docs/en/plugins/mods/events.md, and the mods admin page on seats (`prepend`, `append`).
- Login type: is this machine's session credential a personal or a Team/Enterprise login? On a personal login without managed settings, an installed mod can approve a tool call that the `session-kit` `PreToolUse` guard blocks.

## Deferred

- A cold-send guard (the cache signal from `cache-tax`). It joins the port's context mod, or comes from `cache-tax` itself, decided at step 4 above. Details in `reviews/cache-tax.md`, under "What could move into `session-kit`".
- Turn on auto-update for `galileo-kit` once every plugin in it is ours.
