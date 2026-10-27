# Why sessions file requests as goals

Written 2026-10-27 at the owner's ask: sessions write goals that are objectives or actions, and gallery's recent goals are the example. This reads gallery's record and the eight other records under `~/devel`, finds the cause in the process, and drafts the change. Nothing here is applied yet.

## What gallery's record shows

Gallery has 17 goals. G1 to G5 came from the first description of the app on 2026-10-25. From G6 on, each goal is one request of the owner's, copied into a new goal file the day it was asked.

| Entry | Text | What it is | Why |
| --- | --- | --- | --- |
| `G1` | A gallery to catalogue eye photos by patient | Goal | It names a need and no feature. |
| `G2` | Follow and compare the eye across consults | Goal | Same. |
| `G3` | Fast on a very low-end Android | Goal, or a constraint | It bounds every action more than it leads to any. |
| `G5` | Understand the architecture decisions | Goal | A need of the owner's own. |
| `G6` | Catalogue the photos already taken | Objective under `G1` | An observable change: old photos sit in their patient. |
| `G7` | Archive patients without losing data | Objective under `G1`, with `C2` | The list shows the current patients and nothing is deleted. |
| `G8` | Manual focus and brightness | Objective | Serves a goal nobody wrote: a photo good enough to judge the eye from. |
| `G9` | Adjust ISO too | Action under `O8` | A further control, the same objective as `G8`. |
| `G10` | The phone's camera as a fallback | Objective | `O9` restates it. |
| `G11` | Keep what was set by hand | Action | `A17` restates it. |
| `G12` | See a photo larger with a tap | Objective | `O10` restates it. The tap is the action. |
| `G13` | Change a photo's date | Objective under `G2` | `O11` restates it. |
| `G14` | A sober UI with day and night modes | Part goal, part action | "Looks like a professional tool" is a need. "Follows the phone's day and night" is a decision. |
| `G15` | Browse without enlarging | Objective under `G2` | `O13` restates it. |
| `G16` | Back to the camera fast from any screen | Objective under `G3` | `O14` restates it. The camera icon, `A32`, is the action. |
| `G17` | Three presets and one on auto | Action | `O15` and `A33` both restate it. |

Two things in the record show the sessions knew. Every objective under a request-goal also names the real goal: `O11` comes from `G13` and `G2`, `O14` from `G16` and `G3`. The request-goal adds a parent and no meaning. And `O15` comes from four goals, `G17`, `G8`, `G9` and `G11`, all four camera requests, and none of them the reason for a camera control. That reason is the goal missing from the record: a photo sharp and lit enough to compare from. `O8` aims at it.

So gallery has five goals, perhaps six with the missing one. The other eleven are objectives and actions with an extra file above them.

The other records show it less often, and in the same shape: an adoption or a design decision filed as a goal. `mat-lib`'s `G1` "takes session-kit's CODE.md, whole" and `abstract-refactor`'s `G9` "adopt session-kit's rules" are actions. `mat-lib`'s `G2` "every Core API operation is typed and takes a proof" is an objective. `generic-app`'s `G4` "durable jobs, with a tool-calling chat over any MCP server" is a set of features.

## The cause: the process defines a level by who said it

The sessions follow the process as written. The process tells them what a goal is by its source and gives no test of what it is.

- `global/CLAUDE.md`, the line every session loads: "A goal is the owner's words and an objective needs the owner's approval." Read literally, anything the owner says is a goal.
- `goals-objectives-actions.md`, the levels table: a goal is "an abstract, high-level need", and its writer is "the owner. Every goal rests on something the owner said or answered in so many words." The first half is the only definition of what a goal is, and it gives nothing to test a sentence against. The second half is concrete, so it is what a session acts on.
- The verification section: "An action with no trace is not taken. The gap is put to the owner as a question." A new request often has no objective above it yet. The owner's message is right there and qualifies as "the owner's words", so copying it into a goal closes the gap without asking. The rule rewards the misfiling.
- The worked example files the owner's original ask as `G1`, which is right for a first description and teaches the wrong habit for every later request. Its only owner-sourced action, `A3`, is a reordering of the plan, so no example shows a feature request filed as an action.
- The rule "a goal is never written to fit an action already taken" is broken by every request-goal: `G17` exists because `A33` was about to be built. Nothing checks it.

The owner's reading is right in direction, with one correction. The quick link to the camera is an action, and it is `A32`. The request "back to the camera fast from any screen", `G16`, is an objective: it names an observable change and no mechanism. Neither is a goal.

On the owner's side, nothing is wrong with asking in features. People ask for solutions. The process has to say where a request lands, and today it says the request is a goal because the owner said it.

## The change

### Define each level by what it is

| Level | What it is | Test |
| --- | --- | --- |
| Goal | Why the project exists, or a need of the owner's it serves. | No piece of the work completes it. It holds whatever is built. Asking the owner "why do you want that?" leaves the project. |
| Objective | What changes, observed from outside, with no mechanism named. | Two different actions could meet it, and *Known by* can be checked. |
| Action | The mechanism: a screen, a control, a rule, a file, a step. | It can be built or done, and then it is there. |

The ladder test for any sentence: ask "why?". If the answer is a sentence the owner would also sign, the first sentence is not a goal. Ask "how?". If the answer is "build this", the sentence is an objective. If the sentence is the thing built, it is an action.

A goal is rare. A project has a handful, and a new one is an event, written when the owner's why reaches something the record does not hold.

### Separate the source from the level

Any level can come from the owner. A request is filed at the level it is, with `source: owner` and the quote in its body. An objective the owner asked for in so many words is approved by asking. An action the owner asked for is decided by the owner, as `A32` and `A33` already are. The rule that a session never writes a goal stays: a session asks for the why, the owner's answer becomes the goal, and the request is filed beneath it.

### How a session files a request

1. Find the goal the request serves among those in `CLAUDE.md`. Almost every request has one.
2. File the request at its level beneath it: a new objective if it names a change, an action if it names a mechanism. When it names both, as `G14` does, split it.
3. When no goal fits, ask the owner why they want it, in one line, and keep working. The answer is the new goal.

### Let a program flag the shape

Whether a sentence is a goal is judgment, so no gate can decide it. The smell can be listed, though. `session-intent index` can add a section to `INDEX.md`, under what waits on the owner, of goals that look like requests: a goal whose only child is a single objective, or whose every objective also names another goal. In gallery that lists `G10`, `G12`, `G13`, `G15`, `G16` and `G17`, and `G8`, `G9`, `G11` through `O15`. The check stays green on it, since the zero-warning gate would otherwise block every young project whose first goal has one objective.

### The text to change

- `global/CLAUDE.md`, Intent: "A goal is the owner's words and an objective needs the owner's approval." becomes "A goal is the owner's why, and rare: a request is filed at the level it is, a change as an objective, a mechanism as an action, with the owner as its source." About ten words more, within the rulebook budget.
- `goals-objectives-actions.md`: the levels table takes the *What it is* and *Test* columns above, a paragraph says a level is not its source, the verification bullet on an untraced action says to ask for the why, and the worked example gains a feature request filed as an owner's action.
- `RATIONALE.md`, Intent: a sentence on why, citing gallery.
- A new action under `docs/intent/` for the change, from `O18` (communication with the owner is clear), and the supersession of whatever action holds the levels' current wording.

### Repairing the records

No entry is deleted. A misfiled goal is retired with the reason "a request filed as a goal" and the entry it now is: an objective it duplicates (`G16` to `O14`), or a new objective or action written from it. The objectives that named it drop it from `from`. In gallery that retires eleven goals and asks the owner one question: what is the camera control for. That repair is gallery's own work and runs in gallery. The same pass, smaller, applies to `mat-lib`, `ow-as-python`, `abstract-refactor` and `generic-app`.

## For the owner

1. The three definitions and their tests: right as written?
2. `G3`, fast on a low-end phone: a goal, or a constraint bounding every action?
3. The listing in `INDEX.md`: wanted, or does the rule alone suffice?
4. Repair gallery's record first and the others after, or only change the rule and let each project repair as it touches the entries?
