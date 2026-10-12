#!/bin/bash
# Put the project's direnv environment in front of every Bash command.
#
# Registered on SessionStart, CwdChanged and FileChanged (.envrc, flake.nix,
# flake.lock). Claude Code sources $CLAUDE_ENV_FILE before each Bash command.
# SessionStart's writes last the session, but CwdChanged clears what
# CwdChanged and FileChanged wrote, so all three events export again.
#
# The export is computed from the project root with direnv's own state
# unset, so it is the whole environment every time and not a diff against
# whatever the app started with: writing it twice equals writing it once.
#
# A project with no .envrc is left alone, silently. A project with one where
# direnv is missing or the file is not allowed gets one line saying so, and
# the session carries on with the machine's tools. This hook never blocks.

[ -n "${CLAUDE_ENV_FILE:-}" ] || exit 0
root="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -f "$root/.envrc" ] || exit 0

refuse() {
    # One line for the person, as JSON so every event shows it. The reason is
    # direnv's own last line, with anything JSON would choke on removed.
    reason=$(printf '%s' "$1" | tr -d '"\\' | tr '\n\t' '  ')
    printf '{"systemMessage":"The direnv environment is NOT loaded: Bash runs the machine'"'"'s tools, not the project'"'"'s pinned ones. %s. Fix: with direnv on the app'"'"'s PATH, run direnv allow in %s, then /clear."}\n' \
        "$reason" "$root"
    exit 0
}

command -v direnv >/dev/null 2>&1 || refuse "direnv is not on the app's PATH"

err=$(mktemp "${TMPDIR:-/tmp}/claude-kit-direnv.XXXXXX")
exports=$(cd "$root" \
    && env -u DIRENV_DIR -u DIRENV_DIFF -u DIRENV_WATCHES -u DIRENV_FILE \
        direnv export bash 2>"$err")
status=$?
last=$(sed 's/\x1b\[[0-9;]*m//g' "$err" | grep '^direnv: error' | tail -n 1)
rm -f "$err"

# A blocked .envrc still prints direnv's bookkeeping and exits 1, so success
# is the exit status and a PATH, not merely some output.
[ "$status" -eq 0 ] || refuse "${last:-direnv export exited $status}"
case "$exports" in
    *"export PATH="*) ;;
    *) refuse "direnv exported no PATH from $root" ;;
esac

printf '%s\n' "$exports" >>"$CLAUDE_ENV_FILE"
# direnv's PATH replaces the whole PATH, so the plugin's own commands go back
# on its end, behind the project's tools.
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
    printf 'export PATH="$PATH":%q\n' "$CLAUDE_PLUGIN_ROOT/bin" >>"$CLAUDE_ENV_FILE"
fi
exit 0
