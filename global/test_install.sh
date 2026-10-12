#!/bin/bash
# Cases for install.sh, each against a throwaway config directory.
# Run it: bash global/test_install.sh

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install="$here/install.sh"
failed=0
total=0

expect() {  # label, want exit code, got exit code
    total=$((total + 1))
    if [ "$2" -eq "$3" ]; then echo "  ok   $1"; else echo "  FAIL $1 (want $2, got $3)"; failed=$((failed + 1)); fi
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# A missing file is linked.
export CLAUDE_CONFIG_DIR="$work/fresh"
bash "$install" >/dev/null; expect "links when absent" 0 $?
[ "$(readlink "$CLAUDE_CONFIG_DIR/CLAUDE.md")" = "$here/CLAUDE.md" ]; expect "link points at the kit's file" 0 $?

# Running it again changes nothing.
bash "$install" >/dev/null; expect "second run is a no-op" 0 $?

# An existing file is left byte for byte as it was.
export CLAUDE_CONFIG_DIR="$work/mine"
mkdir -p "$CLAUDE_CONFIG_DIR"
printf 'my own rules\n' > "$CLAUDE_CONFIG_DIR/CLAUDE.md"
out="$(bash "$install")"; expect "refuses to replace a file" 2 $?
[ "$(cat "$CLAUDE_CONFIG_DIR/CLAUDE.md")" = "my own rules" ] && [ ! -L "$CLAUDE_CONFIG_DIR/CLAUDE.md" ]
expect "existing file untouched" 0 $?
case "$out" in *"@$here/CLAUDE.md"*) r=0 ;; *) r=1 ;; esac
expect "prints the import line" 0 $r

# A link to somewhere else is not ours to replace either.
export CLAUDE_CONFIG_DIR="$work/other"
mkdir -p "$CLAUDE_CONFIG_DIR"
ln -s "$work/elsewhere.md" "$CLAUDE_CONFIG_DIR/CLAUDE.md"
bash "$install" >/dev/null; expect "refuses to replace another link" 2 $?
[ "$(readlink "$CLAUDE_CONFIG_DIR/CLAUDE.md")" = "$work/elsewhere.md" ]; expect "other link untouched" 0 $?

# --check changes nothing.
export CLAUDE_CONFIG_DIR="$work/checked"
bash "$install" --check >/dev/null; expect "--check reports not installed" 1 $?
[ ! -e "$CLAUDE_CONFIG_DIR" ]; expect "--check creates nothing" 0 $?

echo
echo "$((total - failed))/$total passed"
[ "$failed" -eq 0 ]
