---
id: A38
from: [O6, O12]
source: session
status: decided 2026-10-25
kind: rule
implemented_by: [global/CLAUDE.md, plugins/session-kit/owed/session_owed.py, plugins/session-kit/bin/session-owed]
proven_by: [plugins/session-kit/owed/test_session_owed.py]
supersedes: []
---

# A38 The owed record

What a change leaves to do outside the code (a key to set on an instance, a command to run once after a deploy, a tool every worktree has to upgrade) is an entry in `OWED.md` at the project's root, written in the commit that makes it owed, under a `###` heading naming the branch, the commit and the change, inside a `##` section naming when it is due. The file is only appended to. `session-owed --since <ref> [--until <ref>] [--section <name>]` prints the entries the file gained across the range, by section, with the working file standing for `--until`, and fails on an entry the range removed, which is the half of the rule a program can hold. `.claude/claude-kit.json` may name the file under `owed`.

## Context

tagents lost such steps three ways before the file: in a landing-log entry, in one lane's uncommitted notes, and in a session's reply, where neither the deploy nor a lane would meet them. The 2026-10-25 reading named it the seventh tool, small as a rule, since every project with a deploy or a shared environment has such steps. A step that matters leaves a record (`O6`), and nothing is lost at a context boundary (`O12`): an owed step written in a reply is lost at the next compaction.

## Options

- A rule alone, as the analysis weighed. The rule says the file is appended in the commit and never cut, and a command that reads a range is what a deploy or a sync script calls, so the reading half is the kit's and the sections are the project's.
- tagents' deploy half: the migration data tests a release ships and the `.env` keys a template names. Both are that project's own shapes, and stay there.
- Fixed sections, as tagents has two. The sections are the project's words for when a step is due, so the command reads any `##` heading and `--section` keeps one.

## Proof

Eleven cases over a repository committed in steps: the entries gained across a range by section, an entry held before not listed, no file at the start owing nothing, one section kept, the working file read without `--until`, a removed entry failing with its heading, an empty range silent, an unknown ref refused, the file named by the settings and by `--file`. The kit has no `OWED.md` yet, since nothing of it deploys.

## Consequences

A project with a deploy script calls `session-owed --since <the release running>` from it and refuses until the entries were read, as tagents does. Undone if the entries are written after the fact, which would mean the rule asks for a note at the wrong moment.
