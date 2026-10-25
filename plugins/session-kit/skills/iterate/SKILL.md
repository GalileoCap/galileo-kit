---
name: iterate
description: Fast-working mode, for while the owner iterates on a change. The session runs the static checks only, commits as it goes, says what did not run, and runs the tests once when the iteration ends.
allowed-tools: Bash, Read, Edit
---

Load it when the owner says they are iterating: *fast-working mode*,
*only run the static checks*, *we're iterating on this*. The owner turns
it on, and only the owner turns it off. It binds this session and no
other.

## What holds while it does

- **Static checks only.** After a change, run the project's static legs
  and nothing that runs a test. The legs are the `iterate.static`
  commands of `.claude/claude-kit.json`, each run from the project root
  with its output to a file and searched there, as always. A project
  that names none gets asked once, in this session's first report in the
  mode, which of its gates run no test, and the answer is written into
  that file. Red here is red: fix it before the next change.
- **No test runs.** The test runners wait (the builtin ones and the
  project's `test_commands`). A test the change needs is still
  **written**, blind and before the code as the global rule has it,
  and **run** when the iteration ends. The exception is a regression
  test for a defect fix, which has to fail first: that single test runs
  alone.
- **Commit proactively**, as in any mode. A commit in this mode is green
  to the static checks and says nothing about the tests.
- **Say what did not run.** Every report during the mode ends with one
  line: *static checks green, tests not run (iterating)*. A report never
  says *done* or *green* without that qualifier.
- **Write it into `CLAUDE.local.md`** as the `Mode:` line under the
  header (*iterating since <date>: static checks only, tests owed*), so a
  compaction does not lose it. Remove the line when the mode ends.
- Everything else is unchanged: a change to a screen is still looked at
  on the screen when the owner has it up, and the project's own rules and
  the tells rules stand.

## When it ends

The owner says the iteration is done (*done iterating*, *that's it*,
*run the tests*), **or the session is about to hand work back**: say
*done*, merge, push on the owner's word, or open a pull request, and the
mode ends there whether or not the owner ended it, because the global
rules stay as written: never deliver red, and done means it was run.
This skill is how a session meets them at the end of an iteration, and
no exception to them.

At the end, once:

1. The project's test runners over what the iteration touched, to a log
   file.
2. Fix what is red in its own commit, with the test that failed first
   where it is a defect.
3. Report which tests ran and their result, and remove the `Mode:` line.
