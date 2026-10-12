#!/bin/bash
# Link global/CLAUDE.md into the Claude Code config directory as CLAUDE.md.
#
# It never replaces a file that is already there. When ~/.claude/CLAUDE.md
# exists and is not this link, it is left alone and the one line that imports
# the kit's text is printed, to add by hand.
#
# Usage: global/install.sh        (config dir: $CLAUDE_CONFIG_DIR, else ~/.claude)
#        global/install.sh --check (report the state, change nothing)

set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_file="$here/CLAUDE.md"
config_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
target="$config_dir/CLAUDE.md"
check_only=0
[ "${1:-}" = "--check" ] && check_only=1

if [ -L "$target" ] && [ "$(readlink "$target")" = "$source_file" ]; then
    echo "already linked: $target -> $source_file"
    exit 0
fi

if [ -e "$target" ] || [ -L "$target" ]; then
    echo "left alone: $target already exists and is not this link."
    echo "To use the kit's rules as well, add this line to it:"
    echo
    echo "  @$source_file"
    exit 2
fi

if [ "$check_only" -eq 1 ]; then
    echo "not installed: $target does not exist"
    exit 1
fi

mkdir -p "$config_dir" || exit 1
ln -s "$source_file" "$target" || exit 1
echo "linked: $target -> $source_file"
