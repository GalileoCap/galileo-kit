---
id: A69
from: [O4]
source: owner
status: decided 2026-10-26
kind: tool
implemented_by: [plugins/read-aloud/hooks/read_aloud.tsx, plugins/read-aloud/hooks/speech.ts, plugins/read-aloud/.claude-plugin/plugin.json, plugins/read-aloud/types/index.d.ts, plugins/read-aloud/footprint.toml, .claude-plugin/marketplace.json]
proven_by: []
supersedes: []
---

# A69 The final answer read aloud by its own plugin

The `read-aloud` plugin reads the final answer of the last main-session turn aloud with the system's voice. A row above the prompt carries a read button (a stop button while it reads) and an auto-read switch. `/read-aloud` reads or stops, `/read-aloud stop` stops, and `/read-aloud auto [on|off]` reads each answer as its turn ends. The `auto` option sets the switch at the session's start and the `voice` option names the system voice. Only prose is read: headings, paragraphs and list items each as one utterance, links as their label, a bare URL as "a link", and a code block or a table as "Code block skipped." or "Table skipped.".

## Context

The owner asked for it: the desktop app's read-aloud button starts from the first text block of a message, and the part they want to hear is the final answer, which comes after the tool calls. The engine's `turn.complete` carries that answer alone. `$.audio.speak` speaks plain text through `say` on macOS but cannot stop an utterance once begun, and the owner asked on 2026-10-26 that a stop be immediate, so each paragraph is a `/usr/bin/say` the plugin starts with `$.process.spawn`, which kills the child when its stream is closed.

## Options

The owner chose among these on 2026-10-26.

- Trigger. A. On demand, a button and a command. B. Every turn. C. Both, with a switch. C taken.
- Home. A. A plugin of its own in this marketplace: it shares no code or state with `session-kit`, and a person can install one without the other. B. A module of `session-kit`, shipped with every kit install. A taken.
- Content. A. Prose only, code blocks and tables named. B. Everything, code read out. A taken.

## Consequences

A stop silences the voice at once: it closes the stream of the `say` speaking, which kills it, and the reading checks before each paragraph that no stop or newer reading came after it. A new reading silences the one before it the same way. `say` reads a paragraph whole from its input, so no paragraph is cut. A subagent's report, an interrupted turn and an empty answer are neither kept nor read. The speech runs after the hook returns, so a turn's end never waits on the voice, and a failure (a voice not installed) is said in a toast. Every hook has a `.catch` that hands on to the engine, so the plugin is never the reason a session fails (`C1`).

The row above the prompt shows once a turn has ended with an answer, and stays: a person who never reads aloud sees it in every session where the plugin is installed. The plugin's reach is held by `plugins/read-aloud/footprint.toml` (`A60`, the kit's reach held to a reviewed footprint).

The blind tests drove all of this through the engine's test host on the terminal and the desktop, seven cases at 0.2.0, and were removed as scaffolding. In a headless session a `say` killed through its stream 800 ms in was gone 13 ms later. Not validated until the owner has heard an answer read in the desktop app, pressed stop and heard it end at once, and turned auto-read on. read-aloud 0.2.0.
