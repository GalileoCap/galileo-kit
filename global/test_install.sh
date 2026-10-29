#!/bin/bash
# Cases for install.sh, each against a throwaway config directory.
# Run it: bash global/test_install.sh

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install="$here/install.sh"
line="@$here/CLAUDE.md"
failed=0
total=0

expect() {  # label, want exit code, got exit code
    total=$((total + 1))
    if [ "$2" -eq "$3" ]; then echo "  ok   $1"; else echo "  FAIL $1 (want $2, got $3)"; failed=$((failed + 1)); fi
}

imports() {  # file, how many import lines it should hold
    [ -f "$1" ] && [ ! -L "$1" ] && [ "$(grep -cxF "$line" "$1")" -eq "$2" ]
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# A missing file is written with the import line.
export CLAUDE_CONFIG_DIR="$work/fresh"
bash "$install" >/dev/null; expect "writes the file when absent" 0 $?
imports "$CLAUDE_CONFIG_DIR/CLAUDE.md" 1; expect "the file imports the kit's rules" 0 $?

# Running it again adds nothing.
bash "$install" >/dev/null; expect "second run succeeds" 0 $?
imports "$CLAUDE_CONFIG_DIR/CLAUDE.md" 1; expect "second run adds no second import" 0 $?

# An existing file keeps its text and gains the import at its end.
export CLAUDE_CONFIG_DIR="$work/mine"
mkdir -p "$CLAUDE_CONFIG_DIR"
printf 'my own rules' > "$CLAUDE_CONFIG_DIR/CLAUDE.md"
bash "$install" >/dev/null; expect "appends to an existing file" 0 $?
[ "$(head -n 1 "$CLAUDE_CONFIG_DIR/CLAUDE.md")" = "my own rules" ] && [ "$(tail -n 1 "$CLAUDE_CONFIG_DIR/CLAUDE.md")" = "$line" ]
expect "own text kept, import on a line of its own" 0 $?

# A file that already imports the kit through ~ is left as it is.
export CLAUDE_CONFIG_DIR="$work/tilde"
mkdir -p "$CLAUDE_CONFIG_DIR"
printf '@~%s\n' "${here#"$HOME"}/CLAUDE.md" > "$CLAUDE_CONFIG_DIR/CLAUDE.md"
before="$(cat "$CLAUDE_CONFIG_DIR/CLAUDE.md")"
bash "$install" >/dev/null; expect "accepts an import written with ~" 0 $?
[ "$(cat "$CLAUDE_CONFIG_DIR/CLAUDE.md")" = "$before" ]; expect "~ import not duplicated" 0 $?

# The old install, a link to the kit's file, becomes a file that imports it.
export CLAUDE_CONFIG_DIR="$work/linked"
mkdir -p "$CLAUDE_CONFIG_DIR"
ln -s "$here/CLAUDE.md" "$CLAUDE_CONFIG_DIR/CLAUDE.md"
bash "$install" >/dev/null; expect "converts the old link" 0 $?
imports "$CLAUDE_CONFIG_DIR/CLAUDE.md" 1; expect "converted link is a file with the import" 0 $?

# A link to somewhere else is not ours to write through.
export CLAUDE_CONFIG_DIR="$work/other"
mkdir -p "$CLAUDE_CONFIG_DIR"
printf 'theirs\n' > "$work/elsewhere.md"
ln -s "$work/elsewhere.md" "$CLAUDE_CONFIG_DIR/CLAUDE.md"
out="$(bash "$install")"; expect "refuses another link" 2 $?
[ "$(readlink "$CLAUDE_CONFIG_DIR/CLAUDE.md")" = "$work/elsewhere.md" ] && [ "$(cat "$work/elsewhere.md")" = "theirs" ]
expect "other link and its target untouched" 0 $?
case "$out" in *"$line"*) r=0 ;; *) r=1 ;; esac
expect "prints the import line" 0 $r

# --check changes nothing.
export CLAUDE_CONFIG_DIR="$work/checked"
bash "$install" --check >/dev/null; expect "--check reports not installed" 1 $?
[ ! -e "$CLAUDE_CONFIG_DIR" ]; expect "--check creates nothing" 0 $?
mkdir -p "$CLAUDE_CONFIG_DIR"
printf 'my own rules\n' > "$CLAUDE_CONFIG_DIR/CLAUDE.md"
bash "$install" --check >/dev/null; expect "--check reports a file without the import" 1 $?
[ "$(cat "$CLAUDE_CONFIG_DIR/CLAUDE.md")" = "my own rules" ]; expect "--check leaves the file as it was" 0 $?

echo
echo "$((total - failed))/$total passed"
[ "$failed" -eq 0 ]
