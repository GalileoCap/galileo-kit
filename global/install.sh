#!/bin/bash
# Make the Claude Code config directory's CLAUDE.md import global/CLAUDE.md.
#
# The user's CLAUDE.md stays the user's: the kit adds one `@` line to it, and
# whatever else the file holds is this machine's own. A missing file is
# written with the line alone, an existing file gains it at its end, and a
# file that already imports the kit (by its full path or through ~) is left
# as it is. The old install, a link to the kit's file, is replaced by a file
# holding the line. A link to anything else is left alone and the line is
# printed, since appending would write into the link's target.
#
# Usage: global/install.sh        (config dir: $CLAUDE_CONFIG_DIR, else ~/.claude)
#        global/install.sh --check (report the state, change nothing)
# Exit: 0 installed, 1 not installed (--check), 2 left alone.

set -u

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_file="$here/CLAUDE.md"
line="@$source_file"
tilde_line="@~${source_file#"$HOME"}"
config_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
target="$config_dir/CLAUDE.md"
check_only=0
[ "${1:-}" = "--check" ] && check_only=1

if [ -L "$target" ] && [ "$(readlink "$target")" != "$source_file" ]; then
    echo "left alone: $target is a link to $(readlink "$target")."
    echo "To use the kit's rules, add this line to the file it points at:"
    echo
    echo "  $line"
    exit 2
fi

if [ -f "$target" ] && [ ! -L "$target" ] && grep -qxF -e "$line" -e "$tilde_line" "$target"; then
    echo "already imported: $target"
    exit 0
fi

if [ "$check_only" -eq 1 ]; then
    if [ -L "$target" ]; then
        echo "not installed: $target is the old link, to be replaced by a file importing $source_file"
    elif [ -e "$target" ]; then
        echo "not installed: $target does not import $source_file"
    else
        echo "not installed: $target does not exist"
    fi
    exit 1
fi

if [ -L "$target" ]; then
    rm "$target" || exit 1
    echo "removed the old link: $target"
fi

mkdir -p "$config_dir" || exit 1
if [ -s "$target" ]; then
    [ -n "$(tail -c 1 "$target")" ] && printf '\n' >> "$target"
    printf '\n%s\n' "$line" >> "$target" || exit 1
    echo "appended: $line to $target"
else
    printf '%s\n' "$line" > "$target" || exit 1
    echo "written: $target importing $source_file"
fi
