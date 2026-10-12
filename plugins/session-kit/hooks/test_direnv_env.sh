#!/bin/bash
# Cases for direnv_env.sh, against a stand-in direnv and a throwaway project.
# Run it: bash plugins/session-kit/hooks/test_direnv_env.sh

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
failed=0
total=0

expect() {  # label, want, got
    total=$((total + 1))
    if [ "$2" = "$3" ]; then echo "  ok   $1"; else echo "  FAIL $1 (want $2, got $3)"; failed=$((failed + 1)); fi
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

mkdir -p "$work/tools" "$work/project" "$work/plugin root/bin"
cat >"$work/tools/direnv" <<'EOF'
#!/bin/sh
echo "export PATH='/flake/bin:/usr/bin:/bin';"
EOF
chmod +x "$work/tools/direnv"
touch "$work/project/.envrc"

run_hook() {  # the env file the hook writes, sourced from a PATH of /start
    : >"$work/env"
    PATH="$work/tools:$PATH" CLAUDE_ENV_FILE="$work/env" CLAUDE_PROJECT_DIR="$work/project" \
        CLAUDE_PLUGIN_ROOT="$work/plugin root" bash "$here/direnv_env.sh" </dev/null >/dev/null
    PATH=/start /bin/bash -c ". \"$work/env\"; printf '%s' \"\$PATH\""
}

path="$(run_hook)"
case "$path" in /flake/bin:*) got=first ;; *) got="$path" ;; esac
expect "the project's PATH comes first" first "$got"
case ":$path:" in *":$work/plugin root/bin:"*) got=present ;; *) got="$path" ;; esac
expect "the plugin's bin stays on PATH after the export" present "$got"
case "$path" in *":$work/plugin root/bin") got=last ;; *) got="$path" ;; esac
expect "the plugin's bin comes last" last "$got"

rm "$work/project/.envrc"
: >"$work/env"
CLAUDE_ENV_FILE="$work/env" CLAUDE_PROJECT_DIR="$work/project" CLAUDE_PLUGIN_ROOT="$work/plugin root" \
    bash "$here/direnv_env.sh" </dev/null >/dev/null
[ -s "$work/env" ]; expect "a project with no .envrc is left alone" 1 $?

echo "$((total - failed))/$total passed"
[ "$failed" -eq 0 ]
