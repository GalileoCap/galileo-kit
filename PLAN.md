# Plan

## Done

- 2026-10-24: research on plugins, mods and their update process, in `claude-code-mods-research.md`.

## Next

1. Get the candidate list from the owner, or shortlist candidates from public marketplaces and the sample mods in `anthropics/claude-code-playground` (`claude-code/mods`).
2. Review each candidate into `reviews/<name>.md` (see `CLAUDE.md`), then decide with the owner: reject, install, or fork.

## Open questions

- Mod ordering: does a mod's `tool.call` or `tool.check` deny run before or after another user-installed mod's approval? This decides whether a mod port of the `session-kit` guard can hold against a third-party mod. Source: the "React to events" page, https://code.claude.com/docs/en/plugins/mods/events.md, and the mods admin page on seats (`prepend`, `append`).
- Login type: is this machine's session credential a personal or a Team/Enterprise login? On a personal login without managed settings, an installed mod can approve a tool call that the `session-kit` `PreToolUse` guard blocks.

## Deferred

- Port `session-kit` to a mod, starting with one mod-only feature (a context-pressure band above the prompt) beside the existing Python hooks. Trade-offs are in the research report under "Porting `session-kit` to a mod". This work belongs in the `session-kit` repository.
- Turn on auto-update for `galileo-kit` once every plugin in it is ours.
