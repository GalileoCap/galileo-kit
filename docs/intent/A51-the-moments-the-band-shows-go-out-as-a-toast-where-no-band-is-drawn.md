---
id: A51
from: [O12, O11]
source: session
status: decided 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx]
proven_by: [plugins/session-kit/hooks/toasts.test.tsx]
supersedes: []
---

# A51 The moments the band shows go out as a toast where no band is drawn

The band above the prompt is raised on the terminal and the desktop only. When `$.session.surfaces()` lists another surface (the phone through Remote Control, VS Code), the moments the band would show go out as a toast as well: the context warning each time the model is warned, a usage window reaching 80% and 95% (`A50`, the plan's usage windows beside the figure), a new task named (`A19`, one task per context), a clear point signalled and the compaction done with the next step the owner's (`A17`, the model signals and the mod runs the chain), and the cold-cache timer firing (`A49`). An engine that cannot say where it draws gets no toast.

## Context

`docs/analyses/mods-for-the-kit.md`, M5, from auto-handoff. The owner follows sessions from the phone, where the context band, the chain's stages and the `new_task` offer draw nothing. The 2.1.308 types say the band is raised on the terminal and desktop surfaces, and that a toast's text is drawn on a remote surface.

## Options

- A toast everywhere. Rejected: on a terminal or the desktop the band already shows the same line, with its button.
- A toast at every stage of the chain. Rejected: the handoff and the compaction follow the signal within seconds and a minute, and the transcript on the phone shows the handoff turn and the continue prompt. The signal and the end that waits on the owner are the moments to know.
- A toast when the cold-cache timer is armed. Rejected: it arms at every turn end past the floor, and a person prompting from the phone would get one per turn. The firing is the moment.
- An option to turn the toasts off. Rejected for now: a toast is clicked off, and nothing shows them to be noise yet.

## Consequences

Each moment reads `$.session.surfaces()` once, in process, before the toast. The new task's toast says the band on a terminal or the desktop offers the handoff and the clear, since a toast has no button. The context warning's toast is the band's line without the growth clause, since it goes out mid-turn. Unverified in a real session: a toast reaching the phone, and whether the kit's newer toast replacing its older one reads well there.

## Proof

Two engine tests in `toasts.test.tsx`. Every moment with a terminal and the desktop attached sends nothing, and with a phone attached sends the six texts in order, a window moving within a tier saying nothing again. VS Code counts as no band, and an engine that cannot say sends nothing. Both failed on 0.24.0.
