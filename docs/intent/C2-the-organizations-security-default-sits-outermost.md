---
id: C2
from: []
source: owner
status: stated 2026-10-26
---

# C2 The organization's security default sits outermost

The account's organization installs the engine's built-in `cc-plugin-sec-default@builtin` and seats it outermost, ahead of every plugin the person installs, `session-kit` included. It has been active on this machine since 18:32 on 2026-10-25, under engine 2.1.308. No managed settings file is on the machine, and `~/.claude/remote-settings.json` is `{}`: the seat comes from the organization, and changing it is the organization's call.

For these events it sends the event past the person's plugins to the last tier, so a hook of the kit on them never runs: every `classic.*` event, `prompt.section`, `prompt.context`, `prompt.attachment`, `prompt.compose`, `skill.prompt`, `attribution.text`, `session.compact`, `settings.read`, and `session.append` through its attachment, hook-context and compaction doors. It also judges `tool.check`, `tool.register`, `tool.describe`, `command.describe`, `agent.offer`, `agent.spawn`, `env.set` and `plugin.register` against the organization's policy, which today sets nothing on them. The engine names each skipped hook in the session once per event: "its <event> hook was skipped. "cc-plugin-sec-default" runs first and sent the event on past it."

The work responds so: no hook of the kit relies on an event the default sends past it. `measure.ts`'s two classic hooks, which timed the tool's own execution, are removed in session-kit 0.35.2. Two hooks in `context.tsx` wait on the owner: the `session.compact` backstop that gives the engine's own compaction the handoff's instructions, and `classic.PostModelSwitch`, from which the cold-cache timer takes the cache's lifetime (`A49`). The command hooks of `hooks.json` (the guard, the formatter, the tells hook) are classic hooks run by the engine and keep running.

Read from the 2.1.308 binary's `sec-default` module and from the transcripts of 2026-10-26, whose notices name `classic.PostToolUse`, `classic.PostToolUseFailure` and `session.compact`.
