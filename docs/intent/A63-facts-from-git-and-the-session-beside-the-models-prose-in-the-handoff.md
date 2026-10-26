---
id: A63
from: [O6, O12]
source: session
status: decided 2026-10-26
kind: behaviour
implemented_by: [plugins/session-kit/hooks/facts.ts, plugins/session-kit/hooks/kit.tsx, plugins/session-kit/hooks/context.tsx, plugins/session-kit/types/index.d.ts, plugins/session-kit/skills/handoff/SKILL.md, plugins/session-kit/footprint.toml]
proven_by: [plugins/session-kit/hooks/facts.test.ts]
supersedes: []
---

# A63 Facts from git and the session beside the model's prose in the handoff

When a main-loop turn that wrote `CLAUDE.local.md` ends, the kit adds a section of facts it read itself after the model's text: the branch against its upstream, the uncommitted paths, the last test run's verdict on this tree (`A52`, a check result stamped with the tree it ran on), the person's last prompt verbatim with the commits since it, and the commit ids the model's text names that the repository does not hold. The section sits between its own markers, and the next write of the file replaces it where it stands. Every line outside the markers is the model's and is never changed. The handoff skill says the section is the kit's.

## Context

`docs/analyses/mods-for-the-kit.md`, M11, from auto-handoff (`hooks/brief.ts:55-77, 160-190`). The handoff of `A5` (the handoff skill writes the live state) is the model's word alone, and the next context acts on it. auto-handoff has Haiku write its brief from the transcript with no tools, so its facts come from the transcript too: the paths of the Edit and Write calls, git's own `[branch sha]` line in a Bash result, the last message that was the person's. The kit's handoff is written by the session's own model, which can run git, so the facts here are the ones a model gets wrong from memory after a compaction or states loosely: where the branch stands, what is committed, whether the tests ran on this tree, what the owner last said.

## Options

- Add the section in the chain's `runHandoff` once the handoff command returns. Rejected: a handoff the person asks for, by the command or through the Skill tool, goes through no part of the chain.
- Add it at the end of any main-loop turn that wrote the file, by a Write or an Edit that landed, as built. Every way a handoff is written takes one path, and at the turn's end the model is done with the file. The concern is registered ahead of the context concern, so the section is in the file before the chain asks for the compaction.
- Add it right after each write. Rejected: a handoff turn often edits the file again (a tell fixed), and the engine refuses an edit of a file changed since the model read it.
- Give the facts to the model as context to copy into the file. Rejected: the copy is the model's word again.
- List the files edited, from the session's Edit and Write calls, as auto-handoff does. Rejected: the file is loaded on every turn and counted in the rulebook's budget (`A28`), the commits name what landed and git shows their files, and the uncommitted paths name what has not.
- Read the commits from git's `[branch sha]` lines in the transcript. Rejected: a compaction drops those lines from the messages, and git answers directly. The commits since the person's last prompt come from `git log --since` at the prompt's time, which the kit now records beside the prompt.
- Mark in place each figure of the model's that the facts do not hold, as auto-handoff marks token figures. Rejected: the kit would then change the model's text. The figures a program can check in the kit's handoffs are commit ids, so the ones git answers `missing` for are listed in the section. Token figures seldom appear in them.

## Consequences

The handoff file grows by the section, at most about 350 words with every list full (six commits, ten paths, 600 characters of the prompt), and the rulebook counts it on every turn. The person's last prompt is written to the uncommitted file, so whatever they pasted into it is on disk there too. The file changes under the model at the turn's end, so an Edit of it in the next turn is refused until the model reads it again. A hot reload during the handoff turn drops the noted write, and that handoff goes without the section. A failure to add it leaves the file as the model wrote it, with a dim line saying why. Undone if the owner reads the section as noise, or if the rulebook's budget cannot hold it.

## Proof

Four engine tests in `facts.test.ts` were written before the code and failed on 0.32.0. Kept: the section goes after the model's text, a later write replaces it where it stands, and the model's text before and after it is never changed, a section cut short included, since the kit rewrites the owner's handoff file and a slip there loses the model's account with nothing said. Deleted once they passed, as blind tests: the section's content (the branch against its upstream, the uncommitted paths, the prompt verbatim with a notification left out, the commits since it, a passing run gone stale, an unknown id), the case with no prompt recorded and no repository, and the section in the file before the chain's `/compact`. The timeline's test gains the concern, and a new-task test's stand-in engine gains the clock the prompt's time now reads. Not yet run: a real session, since the kit is installed once at the end.
