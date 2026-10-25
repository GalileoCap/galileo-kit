---
id: O9
from: [G4]
source: inferred
status: proposed 2026-10-24
---

# O9 Costly steps run once

A costly step runs once and its output is kept to be read again: a test run's output is read from its file when a second question comes up.

## Changes

When a test run or a build is repeated.

## Known by

No test run is repeated within a turn to read output a file already holds, and the plugin's last-test log answers the second question.

Inferred from G4, "capture test output to avoid running tests multiple times".
