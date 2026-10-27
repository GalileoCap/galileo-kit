---
id: A78
from: [O2, O12]
source: owner
status: decided 2026-10-27
kind: rule
implemented_by: [CLAUDE.md]
proven_by: [OWED.md]
supersedes: []
---

# A78 A change that reaches sessions only by install ends with the offer to install it

When a commit changes what a session of the kit loads (the `session-kit` plugin, its hooks, its tools, its bin), the reply that delivers it offers, in one line, to push `main` and update the plugin at user scope and in each project install, as `OWED.md` describes. The session does not push or update unasked, since publishing is the owner's (`O2`, what runs in my sessions changes only when I choose). It offers every time, so the owner is not the one who has to remember that a change is not in a session until it is installed.

## Context

The owner asked for the time since their last message on the status line. The session committed it at 0.37.2 and said the owner would need to update the plugin. The owner then asked for the install and said to write down that the session must always offer it.

## Options

- Install after each commit without asking. Rejected: it publishes to GitHub and changes what runs in every project, which the owner chooses.
- Leave it to the `OWED.md` entry. Rejected: the entry waits until someone reads it, and the owner found the change missing from their session first.
- Offer at the end of the delivering reply. Taken.

## Consequences

Every delivery of a change to the plugin ends with the offer, and a yes is the push, the marketplace update, the user-scope update and each project install, then a read of `installed_plugins.json`. Running sessions keep the old version until `/reload-plugins` or a restart, and the offer names that. Undone if the owner moves the install to a program that runs on the push.
