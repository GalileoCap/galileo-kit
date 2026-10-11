---
name: handoff
description: Write the project's live state to CLAUDE.local.md (uncommitted) so a compaction or a lost session loses nothing. `init` creates it from the template.
allowed-tools: Bash, Read, Write, Edit
argument-hint: "[init]"
---

`CLAUDE.local.md` is the working state of this checkout: the task, what was
decided, where the work stands and what to do next. Claude Code loads it
beside `CLAUDE.md`, so it is the first thing a session reads after a
compaction or a restart. This skill writes it.

## When

- **`/handoff init`**: the file is missing. Copy `template.md` from beside
  this skill to `CLAUDE.local.md` at the project root, fill the header and
  everything the conversation already settles, and make sure `.gitignore`
  lists `CLAUDE.local.md`.
- **`/handoff`**: rewrite the file whole from the conversation's current
  state. Do it at the end of a turn that changed something, after a commit,
  after a decision, and before any long run or any point where the context
  is filling.

## The fields

The template carries them. If the project's `CLAUDE.md` names more fields
for this file, keep them too.

- **Task**: the user's ask in their words, one paragraph. Not the plan.
- **Documents in hand**: every document the work rests on, by path. After a
  compaction the session reads each again in full before its next step, so
  a document missing here is one it works on from a summary.
- **Decisions since**: dated, who took each (the user or the session), and
  why, enough that a fresh session does not reopen it.
- **Where it stands**: done, in progress (the file or step under the
  cursor), not started.
- **Last proof**: which check or tests ran, at which commit, with the
  result, or "none since <commit>".
- **Open questions** for the user, and **Next step**: one line a fresh
  session can execute.

## Rules

- Rewrite the whole file. It is a snapshot of now and keeps no history.
- Never commit it, and never paste it into `CLAUDE.md`.
- No secrets.
- Under about eighty lines. Detail that needs more belongs in a document or
  a commit message.
- Afterwards say in one line that the handoff is written. Do not repeat the
  file.
