#!/bin/bash
# Cases for bin/session-watched. Run it: bash plugins/session-kit/lib/test_watched.sh
# A stalled command is one that spends no CPU, starts no process and writes nothing.

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(dirname "$here")"
watched="$root/bin/session-watched"
failed=0
total=0

expect() {  # label, want, got
    total=$((total + 1))
    if [ "$2" = "$3" ]; then echo "  ok   $1"; else echo "  FAIL $1 (want $2, got $3)"; failed=$((failed + 1)); fi
}
has() {  # label, text, file
    total=$((total + 1))
    if grep -q -- "$2" "$3"; then echo "  ok   $1"; else echo "  FAIL $1 (no '$2' in $3)"; failed=$((failed + 1)); fi
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

"$watched" --stall 5 -- sh -c 'echo hi; exit 3' > "$work/exit3.log" 2>&1; expect "the command's exit status passes through" 3 $?
has "the command's output passes through" "hi" "$work/exit3.log"

"$watched" --stall 5 -- sh -c 'test "$SESSION_WATCHED" = 1' > /dev/null 2>&1; expect "the command is told it is watched" 0 $?

"$watched" sleep 1 > "$work/usage.log" 2>&1; expect "no -- is a usage error" 2 $?

"$watched" --stall 2 --sample 0.5 -- sleep 1234 > "$work/stall.log" 2>&1; expect "a stalled command is ended with 125" 125 $?
has "the stall is said" "no progress in the last 2s" "$work/stall.log"
has "the diagnostics are named" "diagnostics in" "$work/stall.log"
has "the tree is listed" "sleep 1234" "$work/stall.log"
pgrep -f "sleep 1234" > /dev/null 2>&1; expect "the tree is gone" 1 $?

"$watched" --stall 2 --sample 0.5 -- sh -c 'for i in 1 2 3 4 5 6 7 8; do echo tick; sleep 0.5; done' > "$work/output.log" 2>&1; expect "output growing into a file is progress" 0 $?
expect "every tick arrived" 8 "$(grep -c tick "$work/output.log")"

"$watched" --stall 2 --sample 0.5 -- sh -c 'for i in 1 2 3 4 5 6; do sleep 0.7; done' > /dev/null 2>&1; expect "a process starting is progress" 0 $?

"$watched" --warn --stall 1 --sample 0.5 -- sleep 3 > "$work/warn.log" 2>&1; expect "with --warn a stalled command is not ended" 0 $?
has "the warning is said" "not ended (--warn)" "$work/warn.log"

"$watched" --check 1 --stall 10 --sample 0.5 -- sleep 2.5 > "$work/check.log" 2>&1; expect "a check line does not end the command" 0 $?
has "every --check seconds it says what it decided" "in, no progress for" "$work/check.log"

"$watched" --label mine --stall 2 --sample 0.5 -- sleep 1234 > "$work/label.log" 2>&1
has "the label names the run" "(mine)" "$work/label.log"

echo "$total cases, $failed failed"
exit $((failed > 0))
