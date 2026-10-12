#!/bin/bash
# Cases for install.sh, each against a throwaway directory.
# Run it: bash shims/test_install.sh

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install="$here/install.sh"
shim="$here/language-server"
failed=0
total=0

expect() {  # label, want exit code, got exit code
    total=$((total + 1))
    if [ "$2" -eq "$3" ]; then echo "  ok   $1"; else echo "  FAIL $1 (want $2, got $3)"; failed=$((failed + 1)); fi
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# An empty directory gets both links.
export CODEINTEL_BIN="$work/fresh"
bash "$install" --check >/dev/null; expect "check reports nothing linked" 1 $?
bash "$install" >/dev/null; expect "links when absent" 0 $?
[ "$(readlink "$CODEINTEL_BIN/pyright-langserver")" = "$shim" ]; expect "pyright name points at the shim" 0 $?
[ "$(readlink "$CODEINTEL_BIN/typescript-language-server")" = "$shim" ]; expect "typescript name points at the shim" 0 $?
bash "$install" >/dev/null; expect "second run is a no-op" 0 $?
bash "$install" --check >/dev/null; expect "check reports both linked" 0 $?

# A copy of the shim becomes the link.
export CODEINTEL_BIN="$work/copied"
mkdir -p "$CODEINTEL_BIN"
cp "$shim" "$CODEINTEL_BIN/pyright-langserver"
bash "$install" >/dev/null; expect "replaces a copy of the shim" 0 $?
[ -L "$CODEINTEL_BIN/pyright-langserver" ]; expect "the copy is now a link" 0 $?

# Anything else is left byte for byte as it was.
export CODEINTEL_BIN="$work/mine"
mkdir -p "$CODEINTEL_BIN"
printf 'my own server\n' > "$CODEINTEL_BIN/typescript-language-server"
bash "$install" >/dev/null; expect "refuses to replace another file" 2 $?
[ "$(cat "$CODEINTEL_BIN/typescript-language-server")" = "my own server" ]; expect "the other file is untouched" 0 $?
[ -L "$CODEINTEL_BIN/pyright-langserver" ]; expect "the free name is still linked" 0 $?

echo "$((total - failed))/$total passed"
[ "$failed" -eq 0 ]
