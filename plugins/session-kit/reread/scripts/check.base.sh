# Written by session-codeintel template: the bar's own legs. Edit the template, not
# this file. Run by scripts/check from the project's root, and the project's own
# legs follow it there. Every leg runs, so one run shows every failure there is.
set -uo pipefail
status=0
echo "== ruff format =="
uv run --quiet ruff format --check . || status=1
echo "== ruff check =="
uv run --quiet ruff check . || status=1
echo "== basedpyright =="
uv run --quiet basedpyright --warnings || status=1
exit $status
