---
id: A54
from: [O5, O12, O13]
source: owner
status: decided 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/types/index.d.ts]
proven_by: [plugins/session-kit/hooks/chain.test.tsx]
supersedes: [A45]
---

# A54 A Haiku judge reads the unattended chain for a loop or a step beyond its task

The chain of `A17` (the model signals a clear point, the mod runs the chain) goes on by itself with no limit on its count. The kit keeps the chains that went on since the person's last prompt (`A46`, prompt origins as a closed set), each with its next step and HEAD when it continued. At the third signal since that prompt, the fifth, and every one from the seventh, Haiku reads the owner's task from the handoff's Task section, their last prompt, the steps so far with their commits, the commits since the first, and the step proposed, and answers CONTINUE, LOOP or BEYOND with a reason. LOOP is a session going round: the same step again, steps that undo each other, a fix tried again that keeps failing, with nothing committed between. BEYOND is a step past the task: work it does not name, or a decision that is the owner's (publishing, pushing, installing, choosing between options the owner has not chosen, approving its own work). On LOOP, BEYOND, or no verdict, the chain still writes the handoff and compacts, then stops with the next step the owner's. The model is told why in the tool's answer, and the band says it after the compaction ("The chain stopped since ..."), a toast too where no band is drawn (`A51`). A signal whose next step is the owner's asks no judge.

## Context

The owner, on 2026-10-25, of `A45` (a loop guard on the chain), which refused a third `clear_point` since the person's last prompt: "I don't want this. I like the sessions going on autonomously if it fits. Maybe we can use a haiku to identify if it's stuck on an infinite loop (first at 3, then at 5, and from 7 onwards)", and then that it stops on a loop "or when the session is going further than its responsibilities". The guard stopped a session that was making progress after two chains, the case this repository hit the same day with the improvements going on one by one.

## Options

- The count of `A45` raised, or no guard. Rejected by the owner: a count says nothing of whether the chain is progressing, and a loop with nobody present runs a compaction each time.
- A refusal of the signal on LOOP or BEYOND, as `A45` refused. Rejected: the clear point is real (the tree is committed and green), so the handoff and the compaction are worth running. Only the continue is wrong. Stopping after the compaction leaves the person a small context and a current handoff, as the cold-cache timer of `A49` does.
- A judge that fails open, the chain going on when Haiku gives no verdict. Rejected: an outage would let a loop run unjudged, each turn a compaction. Failing closed costs one wait for the owner.
- The session's own model as the judge, through `$.model.fork` over the cached transcript. Rejected for now: the judge must not be the party it judges, and a fork bills the session's model on every token of the prefix. Haiku reads a few hundred words.
- The commits read by date since the person's last prompt. Rejected: a range from the first chain's HEAD needs no clock and no extra state.

## Consequences

`chainSteps` in `$.state` replaces `chainsUnattended`, reset by the person's own prompt. A judged signal adds a Haiku call of a few seconds to the `clear_point` tool call, at most 200 tokens out and a 30-second limit, on the session's own credentials, and two git calls. Each continue adds one `git rev-parse`. The judge reads text the session wrote (its notes, its commit subjects), so a session that writes its notes to please the judge can pass it. The owner's task comes from `CLAUDE.local.md`, which the handoff rewrites, so a handoff that rewrote the Task section in its own words would widen the scope the judge holds it to: the handoff skill keeps the task in the owner's words. Unverified in a real session: Haiku's verdicts on real chains, its latency, and the stop line on the band.

## Proof

Two engine tests in `chain.test.tsx`, both failed on 0.26.0 at the refusal of the third signal. Eight chains go on, the judge read at the third, the fifth, the seventh and the eighth, with the owner's task, their last prompt, the earlier steps with their commits and the proposed step in its prompt. A task notification resets nothing, the person's prompt starts over, and a step that is the owner's asks no judge. A LOOP, a BEYOND in bold, an empty reply and a reply with no verdict each stop the chain after the handoff and the compaction, with no continue sent, the reason in the tool's answer and on the band.
