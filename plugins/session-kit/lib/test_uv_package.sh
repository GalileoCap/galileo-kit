#!/bin/bash
# Cases for bin/session-tells, bin/session-codeintel and lib/uv_package.sh.
# Run it: bash plugins/session-kit/lib/test_uv_package.sh

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(dirname "$here")"
failed=0
total=0

expect() {  # label, want, got
    total=$((total + 1))
    if [ "$2" = "$3" ]; then echo "  ok   $1"; else echo "  FAIL $1 (want $2, got $3)"; failed=$((failed + 1)); fi
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# The commands run from the caller's directory, so a relative path is the caller's.
mkdir -p "$work/project"
printf 'A plain sentence about the build.\n' > "$work/project/clean.md"
printf 'The build is fast \xe2\x80\x94 and it is cheap.\n' > "$work/project/dashed.md"
(cd "$work/project" && "$root/bin/session-tells" check clean.md >/dev/null 2>&1); expect "tells: a clean file passes" 0 $?
(cd "$work/project" && "$root/bin/session-tells" check dashed.md >/dev/null 2>&1); expect "tells: a dash fails" 1 $?
out="$(cd "$work/project" && "$root/bin/session-tells" show dashed.md 2>&1)"
case "$out" in *dashed.md*) got=named ;; *) got=missing ;; esac
expect "tells: show names the caller's file" named "$got"

"$root/bin/session-codeintel" recipes list >"$work/recipes" 2>&1; expect "codeintel: recipes list runs" 0 $?
[ -s "$work/recipes" ]; expect "codeintel: recipes list prints the recipes" 0 $?

# Without uv the command says so and exits 127, the shell's code for a missing command.
nouv="$work/nouv"; mkdir -p "$nouv"
for tool in dirname basename cd pwd tr printf; do
    path="$(command -v "$tool")"; case "$path" in /*) ln -s "$path" "$nouv/$tool" ;; esac
done
err="$(PATH="$nouv" /bin/sh "$root/bin/session-tells" show x 2>&1)"; code=$?
expect "no uv: exits 127" 127 "$code"
case "$err" in *uv*) got=said ;; *) got=silent ;; esac
expect "no uv: says uv is missing" said "$got"

# Where the environment lives: the hooks' data directory when the plugin runs from
# Claude Code's cache, the plugin's own directory otherwise.
# shellcheck source=uv_package.sh
. "$here/uv_package.sh"
got="$(plugin_data /home/u/.claude/plugins/cache/galileo-kit/session-kit/0.4.0)"
expect "data: cached plugin uses the data directory" /home/u/.claude/plugins/data/session-kit-galileo-kit "$got"
got="$(plugin_data "/home/u/cfg/plugins/cache/my.market/session-kit/0.4.0")"
expect "data: an id's other characters become dashes" /home/u/cfg/plugins/data/session-kit-my-market "$got"
got="$(plugin_data /home/u/src/claude-kit/plugins/session-kit)"
expect "data: a working copy keeps its own directory" /home/u/src/claude-kit/plugins/session-kit "$got"
got="$(CLAUDE_PLUGIN_DATA=/elsewhere plugin_data /home/u/.claude/plugins/cache/galileo-kit/session-kit/0.4.0)"
expect "data: CLAUDE_PLUGIN_DATA wins when set" /elsewhere "$got"

echo "$((total - failed))/$total passed"
[ "$failed" -eq 0 ]
