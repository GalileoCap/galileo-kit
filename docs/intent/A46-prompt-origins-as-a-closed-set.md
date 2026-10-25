---
id: A46
from: [O11]
source: session
status: decided 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx]
proven_by: [plugins/session-kit/hooks/new_task.test.tsx, plugins/session-kit/hooks/chain.test.tsx]
supersedes: []
---

# A46 Prompt origins as a closed set

One predicate says whether a prompt is the person's own words: it is, unless its origin kind is `plugin`, `task-notification`, `scheduled-trigger`, `peer`, `peer-send-message`, `projects-relay`, `coordinator`, `observer`, `observer-activity` or `auto-continuation`, or it runs a slash command. Only the person's words are kept as the prompt a `new_task` press sends again (`A19`, one task per context), and only they reset the chain's loop guard (`A45`, a loop guard on the chain).

## Context

`context.tsx` kept every prompt but a plugin's as `lastPrompt`, so a background task's notification or another session's message, landing between the person's prompt and a `new_task` press, would have been sent again after the clear as if the person had typed it. The 2.1.308 types close the set of origins (`PromptOrigin`, sixteen kinds).

## Options

- Keep only `composer` and `bridge`, as auto-handoff does. Rejected: which kind the desktop app stamps on the person's prompt is not known, and a prompt the engine cannot classify arrives as `unclassified`, so keeping two kinds would drop the person's own words on some host.
- Refuse the kinds known not to be the person's, keep the rest. Taken. `composer`, `bridge`, `sdk`, `channel`, `slack-ping`, `unclassified` and no origin stay the person's. A plugin's `$.command.run` is stamped `plugin` by the engine, so the chain's own commands are refused the same way.

## Consequences

A kind the engine adds later is the person's until it is named here. A prompt from a Slack channel counts as the person's, which on a channel-driven session is right.

## Proof

One engine test submits a prompt of each refused kind after the person's and sees the person's sent again on Keep going here, then one from the phone taken in its place. It failed on 0.22.0: the auto-continuation's text was sent.
