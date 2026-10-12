#!/bin/bash
# Link the language-server shim onto PATH under each server's name.
#
# Both names point at shims/language-server in this checkout, so a pull
# updates them. A name already holding a copy of the shim is replaced by the
# link, which loses nothing. A name holding anything else is left alone and
# named, and the script exits 2.
#
# Usage: shims/install.sh          (directory: $CODEINTEL_BIN, else ~/.local/bin)
#        shims/install.sh --check  (report the state, change nothing)

set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
shim="$here/language-server"
bin="${CODEINTEL_BIN:-$HOME/.local/bin}"
check_only=0
[ "${1:-}" = "--check" ] && check_only=1
status=0

for name in pyright-langserver typescript-language-server; do
    target="$bin/$name"
    if [ -L "$target" ] && [ "$(readlink "$target")" = "$shim" ]; then
        echo "already linked: $target"
        continue
    fi
    if [ -e "$target" ] && ! cmp -s "$target" "$shim"; then
        echo "left alone: $target is not this shim"
        status=2
        continue
    fi
    if [ "$check_only" -eq 1 ]; then
        echo "not linked: $target"
        [ "$status" -eq 0 ] && status=1
        continue
    fi
    mkdir -p "$bin" || exit 1
    ln -sf "$shim" "$target" || exit 1
    echo "linked: $target -> $shim"
done
exit $status
