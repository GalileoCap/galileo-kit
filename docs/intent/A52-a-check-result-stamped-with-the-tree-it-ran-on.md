---
id: A52
from: [O6, O8]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/hooks/test_log.ts, plugins/session-kit/hooks/checkout.ts, plugins/session-kit/types/index.d.ts]
proven_by: [plugins/session-kit/hooks/test_log.test.ts]
supersedes: []
---

# A52 A check result stamped with the tree it ran on

The test log of `A11` (the test log) stamps each run with a fingerprint of the working tree's content, read through git with the repository's own config unable to run code (`A48`): the index's blob hashes, the files changed since hashed afresh, the deleted ones out and the untracked ones in, so a commit of the same content leaves the print unchanged. The last run reads back as PASS, FAIL (it failed, and none has passed since), STALE (it passed, and files have changed since) or UNKNOWN (no run, or no print). At a `git commit` the model is told of a FAIL or a STALE with what to do, and at the end of a main-loop turn the person sees one dim line for either. PASS and UNKNOWN say nothing.

## Context

`docs/analyses/mods-for-the-kit.md`, M14, from verify-board. The rule "never deliver red" in `global/CLAUDE.md` rested on the model's word: the log kept a run's output and nothing of the tree it ran on, so a run that passed before the last edit, or failed and was never repeated, could be delivered as green. With the stamp, done rests on a record a program wrote (`O6`).

## Options

- HEAD and the diffs against it as the stamp, as verify-board keeps them. Rejected: the common sequence is a test run on a dirty tree, then its commit, then the reply, and against HEAD that commit makes every passing run stale. The content print is the same before and after.
- A temporary index and `git write-tree`, git's own tree hash. Rejected: `git add` into it runs the clean filters the repository's config names, and writes objects. `hash-object --no-filters` runs none.
- The stamp taken before the run, so a run that edits files is marked. Rejected: a run that leaves an artefact behind (a coverage file, a snapshot) would read stale until the next run. The print after the run is the tree the result is handed back on.
- The verdict read at `clear_point`, refusing a chain on a FAIL or a STALE. Rejected: nothing in the context module blocks a tool call but the guard, and a run the kit does not recognise as a test run would be refused for no reason. The model gets the words at the commit.
- A line at every turn end for UNKNOWN and PASS too. Rejected: a session that writes documents never runs tests, and a passing run needs no confirmation.

## Consequences

A test run costs three git calls after it, four with files to hash, and so does each `git commit` and each main-loop turn end once a passing run is on record, in process. The print is a 64-bit FNV hash of the sorted entries. A tree with more than 1,000 changed or untracked files, a merge under way, a submodule moved, or git's output cut at 4 MiB is not stamped and reads UNKNOWN. A test command that edits tracked files stamps the edited tree. The record is `lastTest` in `$.state`, and the log file carries the same `Tree:` line for a person. In this repository the engine tests count as a test run through `plugin test` in `test_commands`, and a run whose exit code a trailing `echo` swallows is logged as passed, so the command's last word has to be the run's. Unverified in a real session: the git calls' time on the owner's repositories, and the dim line beside the checkout's.

## Proof

One engine test in `test_log.test.ts`, over a git stand-in of an index and a working tree. A passing run on a dirty tree stamps the log, and its commit is told nothing. The commit made, the turn end says nothing. A tracked file changed since draws the line and gives the commit its context, and the edit undone restores the run. An untracked file's content and a deletion count as changes. A failed run is the last word whatever the tree, until one passes. Outside a repository nothing is stamped or said, and a subagent's turn end says nothing. It failed on 0.25.0.
