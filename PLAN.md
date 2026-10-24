# Plan

## Done

- 2026-10-24: research on plugins, mods and their update process, in `claude-code-mods-research.md`.

- 2026-10-24: `cache-tax` reviewed at `e4940af` (v2.3.1) into `reviews/cache-tax.md`. Verdict: fork. Nothing malicious. The Sonnet 5.5 cache-read price is wrong.

## Candidates

| Mod | Source | Review | Verdict | Owner's decision |
| --- | --- | --- | --- | --- |
| `cache-tax` | `karanb192/cache-tax`, served by `karanb192/claude-code-mods` | `reviews/cache-tax.md` | Fork | Pending |

## Next

1. Owner decides on `cache-tax`: fork, or install as is. For a fork, the owner also confirms its three first changes (the review's verdict section lists them).
2. If forked: add it to `galileo-kit` as a separate plugin at `2.3.1-galileo.1`, work that follows `session-kit`'s own `CLAUDE.md`, and send the Sonnet 5.5 price fix upstream as a PR once the owner says to.
3. Next candidate from the owner, or a shortlist from public marketplaces and `anthropics/claude-code-playground` (`claude-code/mods`). The same marketplace also serves `image-peek`, `mod-builder` and `fable-pin`.

## Open questions

- Mod ordering: does a mod's `tool.call` or `tool.check` deny run before or after another user-installed mod's approval? This decides whether a mod port of the `session-kit` guard can hold against a third-party mod. Source: the "React to events" page, https://code.claude.com/docs/en/plugins/mods/events.md, and the mods admin page on seats (`prepend`, `append`).
- Login type: is this machine's session credential a personal or a Team/Enterprise login? On a personal login without managed settings, an installed mod can approve a tool call that the `session-kit` `PreToolUse` guard blocks.

## Deferred

- A cold-send guard in `session-kit` as a `UserPromptSubmit` settings hook, whose refusal names `/session-kit:handoff` then `/clear`. It conflicts with `cache-tax`'s own guard, so it waits on the `cache-tax` decision. Details in `reviews/cache-tax.md`, under "What could move into `session-kit`".
- Port `session-kit` to a mod, starting with one mod-only feature (a context-pressure band above the prompt, which could show `cache-tax`'s cache state beside it) beside the existing Python hooks. Trade-offs are in the research report under "Porting `session-kit` to a mod". This work belongs in the `session-kit` repository.
- Turn on auto-update for `galileo-kit` once every plugin in it is ours.
