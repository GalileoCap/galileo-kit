# Code measure of generic-app, read against its impact report

Run on 2026-10-25 with `session-codeintel measure` at the two snapshots `CONVENTIONS-IMPACT.md` compares, `9f5a9e4` and `937f93a`, over the report's three areas, to prove the command against the rescued scripts. Every size figure matches the report to the line, and every Python complexity figure to the function. The frontend's functions, totals, means and counts at 6 or more match too. The JSX elements run 13 and 14 higher (753 and 676 against 740 and 662) because tree-sitter parses a fragment, `<>…</>`, as an element and the rescued script counted none. The repeated looks are not counted here, since generic-app keeps its allowlist in TypeScript and has no `looks` block.

Written by `session-codeintel measure` over `/Users/galileo/devel/galileo/misc/generic-app`. Code lines leave out blank lines, comments and docstrings. Complexity is McCabe per function: Python from ruff's C901, TypeScript counted on the syntax tree, both at the same version for every row.

## backend/src

| Snapshot | Files | Lines | Code | Comment | Docstring |
| --- | --- | --- | --- | --- | --- |
| 9f5a9e4 | 70 | 18,452 | 11,754 | 77 | 3,420 |
| 937f93a | 73 | 18,514 | 11,453 | 85 | 3,623 |

| Snapshot | Language | Functions | Complexity | Mean | At 6 or more | Max | JSX elements | Repeated looks | Places |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9f5a9e4 | Python | 873 | 2,283 | 2.62 | 82 | 10 |  |  |  |
| 937f93a | Python | 922 | 1,906 | 2.07 | 37 | 10 |  |  |  |

## backend/tests

| Snapshot | Files | Lines | Code | Comment | Docstring |
| --- | --- | --- | --- | --- | --- |
| 9f5a9e4 | 26 | 11,654 | 8,506 | 65 | 1,186 |
| 937f93a | 30 | 12,020 | 8,756 | 66 | 1,216 |

| Snapshot | Language | Functions | Complexity | Mean | At 6 or more | Max | JSX elements | Repeated looks | Places |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9f5a9e4 | Python | 581 | 804 | 1.38 | 10 | 10 |  |  |  |
| 937f93a | Python | 611 | 841 | 1.38 | 10 | 10 |  |  |  |

## frontend/src

| Snapshot | Files | Lines | Code | Comment | Docstring |
| --- | --- | --- | --- | --- | --- |
| 9f5a9e4 | 55 | 7,331 | 6,342 | 566 | 0 |
| 937f93a | 73 | 7,614 | 6,520 | 621 | 0 |

| Snapshot | Language | Functions | Complexity | Mean | At 6 or more | Max | JSX elements | Repeated looks | Places |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9f5a9e4 | TypeScript | 603 | 1,199 | 1.99 | 30 | 85 | 753 |  |  |
| 937f93a | TypeScript | 636 | 1,239 | 1.95 | 30 | 85 | 676 |  |  |
