---
id: A64
from: [O5, O1]
source: session
status: decided 2026-10-26
kind: check
implemented_by: [plugins/session-kit/codeintel/src/session_codeintel/review.py, plugins/session-kit/codeintel/src/session_codeintel/reach.py, plugins/session-kit/codeintel/src/session_codeintel/cli.py, plugins/session-kit/codeintel/src/session_codeintel/footprint.py, plugins/session-kit/codeintel/docs/api.md, CLAUDE.md, docs/claude-code-mods-research.md]
proven_by: [plugins/session-kit/codeintel/tests/test_review.py, docs/reviews/agent-profiler.md, docs/reviews/effortless.md, docs/reviews/replay-theater.md, docs/reviews/cache-tax.md]
supersedes: []
---

# A64 A review's mechanical third written by a program

`session-codeintel review <dir> --into docs/reviews/<name>.md` writes what a program can read off a plugin cloned for review into a section of the review, between its own markers. The section holds the plugin's name and version, the clone's commit, origin and working tree, the engine, and the validator's verdict with its errors and warnings and each line it cut short. It grades the plugin's reach from a table of every `$` member of 2.1.308, and lists each call with the functions it is made through. It lists each hook with its matcher, whether it gates without a `.catch`, whether it is hot, and what to read it for. It also names the environment and state the plugin reads and writes, another plugin's state it reads, what `claude plugin details` printed, each source line whose strings hold a control character, the size an install copies and the size a marketplace clones, and the symbolic links. A new review starts as its heading and the section. An existing one has the section replaced where it stands, or placed after its heading, and nothing outside the markers changes. Without `--into` the section is printed.

## Context

`docs/analyses/mods-for-the-kit.md`, M23, from the catalogue's scanner (`tools/grade.mjs:1-60`, `SCANNING.md` in `karanb192/awesome-claude-code-mods` at `e8c5c2a`). Each review under `A1` (review from a clone) opened with the same third done by hand: validate, details, read the calls and the gating hooks off the validator, measure the install. The scanner grades every mod on GitHub from the validator's calls, with a table of each `$` member's reach by its declaration, and warns when a mod that hooks `ui.render` has control-character strings in its source. Under `O5` (work moves down to programs) that third is a program's, and the reviewer reads the code it points at. Under `O1` (only read code runs) nothing of the clone runs: the engine's two commands read it, and git and ast-grep run from an empty directory outside it, git with `core.fsmonitor` off (`A48`).

## Options

- Print to stdout for the reviewer to paste. Rejected: the paste is the reviewer's copy, and the next run cannot refresh it.
- Write a file of its own beside each review. Rejected: the rule of engagement says each review is a file, and the owner would read two.
- A section between markers in the review, replaced in place, as the handoff's facts are (`A63`, facts from git and the session beside the model's prose in the handoff). Chosen: one document, the program's part marked as the program's, and a rerun at a new commit refreshes it with nothing around it moved.
- A subcommand of its own, `session-review`, as the analysis named it. Rejected: the validator's notes are read by the footprint gate's parser (`A60`, the kit's reach held to a reviewed footprint), and a second command would carry a second copy of it. It is `session-codeintel review`.
- The scanner's grade table copied. Rejected: the table is the scanner's, for 2.1.302. The kit's is written from the 2.1.308 declarations, where the members are the same 85, with labels the review checklist asks about: a model call apart from driving the session, a timer apart from drawing. A member outside the table is named unclassified, and the level is then a floor.
- The validator's text report, as the footprint gate reads it. Rejected for the review: `--json` gives the errors, the warnings and the gating hooks with `hasCatch` as data. Its notes are cut at about a thousand characters as the text is, so a cut line is named and its level is a floor.
- Control characters only where the plugin hooks `ui.render`, as the scanner does. Rejected: the scan is cheap, and a string written to `$.ui.log` or a file reaches a terminal too. Whether the plugin hooks `ui.render` is said beside the list.
- Every escape matched and filtered after. Rejected on the first real run: effortless's site pages are minified onto single lines, and ast-grep printed 3.4 GB of JSON for 42,421 matches, each carrying its line. The rule matches only the escapes that can stand for a control, in the TypeScript and JavaScript a hooks module can import.

## Consequences

Every string the clone supplies (a description, a validator note, a file name, a link's target) is shown with its control characters spelled out as `\xHH` and the comment markers broken, so a terminal printing the review runs nothing and a clone cannot end the section early. The four reviews written before carry the section, written from their clones at the commits they record: agent-profiler L3, effortless at least L3 with four lines cut, replay-theater L1 and cache-tax L2, which agree with the catalogue where it has a level. The grade table is the 2.1.308 release's, and a member a later release adds shows as unclassified until the table takes it. The control scan sees literals alone, so a string built at run time is missed, which the section says. Running it found a latent defect in `A60`'s gate, fixed apart: the engine's cut had been held as an item.

## Proof

Six cases in `codeintel/tests/test_review.py` were written before the code against a stand-in engine and a planted clone, and failed on 0.7.1 for want of the command. Kept, each a rule whose failure is silent and costly. The reviewer's text is never changed. Nothing the clone holds reaches the review as a control character or a marker. Each string holding a control character is named, with regular expressions, comments, tab, newline and an escaped backslash left out. Deleted once they passed, as blind tests: the section's content, a cut line or an unclassified member leaving the level a floor, and a failed validation recorded where a missing engine is refused. Run on the four reviewed clones into their reviews, a second run leaving `agent-profiler.md` byte for byte as it was.
