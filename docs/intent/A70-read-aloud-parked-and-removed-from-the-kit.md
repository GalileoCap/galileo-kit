---
id: A70
from: [O4]
source: owner
status: decided 2026-10-26
kind: tool
implemented_by: [.claude-plugin/marketplace.json, .claude/claude-kit.json]
proven_by: []
supersedes: [A69]
---

# A70 Read-aloud parked and removed from the kit

The `read-aloud` plugin is removed from the marketplace and from the tree, and the work on a better voice is parked. What was learned stays as notes.

## Context

`A69` (the final answer read aloud by its own plugin) shipped at 0.2.0 with the system's default voice, which the owner found too synthetic. The two local neural voices measured for it, Kokoro and Piper, were set aside after the owner heard the samples (Kokoro fp32 "barely passable", its 1.1 GB peak unacceptable). The system's `Premium` and `Enhanced` voices were the next to try and none was downloaded. On 2026-10-26 the owner said to park all the speech work and remove it from the kit, and to leave the notes in case it is taken up again.

## Options

- A. Keep the plugin installed with the default voice. Rejected by the owner: the voice is the reason for the work.
- B. Remove the plugin, keep the notes. Taken.
- C. Remove everything, notes included. Rejected by the owner.

## Consequences

`plugins/read-aloud` is gone from the tree, the marketplace lists `session-kit` alone, and the footprint gate reads one plugin. The notes stay where they are: `docs/analyses/local-neural-voice.md` (candidates, the verdict, the system's higher voices), `docs/measurements/local-voice-2026-10-26.md` with its scripts and raw figures under `docs/measurements/local-voice/`, and `docs/reviews/kokoro-onnx.md` and `docs/reviews/piper-tts.md`. `A69`'s entry stays, retired, and its design is in git at `ac9cd82`: each paragraph a `/usr/bin/say` spawned through `$.process.spawn`, killed by closing its stream, with the final answer taken from `turn.complete`. To resume, restore `plugins/read-aloud` from that commit, download a `Premium` voice and measure it with `local-voice/driver.py say:<voice>`.

Outside the repository, about 1.1 GB of environments and weights remain under `~/.local/share/read-aloud/`, left for the owner to delete or keep. Nothing was installed from the marketplace, so nothing needs uninstalling.
