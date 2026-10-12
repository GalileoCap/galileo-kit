# Sourced by the commands in bin/: run a command of one of the plugin's uv
# packages in the environment its hooks use.

# plugin_data <plugin root>: the directory the package environments live in.
# CLAUDE_PLUGIN_DATA when set. A plugin that runs from Claude Code's cache,
# <config>/plugins/cache/<marketplace>/<plugin>/<version>, keeps them in
# <config>/plugins/data/<plugin>-<marketplace>, where its hooks keep theirs.
# Anywhere else, the plugin's own directory.
plugin_data() {
    if [ -n "${CLAUDE_PLUGIN_DATA:-}" ]; then
        printf '%s\n' "$CLAUDE_PLUGIN_DATA"
        return
    fi
    plugin_dir="$(dirname "$1")"
    market_dir="$(dirname "$plugin_dir")"
    cache_dir="$(dirname "$market_dir")"
    if [ "$(basename "$cache_dir")" = cache ] && [ "$(basename "$(dirname "$cache_dir")")" = plugins ]; then
        id="$(printf '%s-%s' "$(basename "$plugin_dir")" "$(basename "$market_dir")" | tr -c 'A-Za-z0-9_-' '-')"
        printf '%s/data/%s\n' "$(dirname "$cache_dir")" "$id"
    else
        printf '%s\n' "$1"
    fi
}

# run_package <package> <environment> <command> [arguments]: run <command> of
# the uv package in <plugin root>/<package>, its environment named
# <environment> in the plugin's data directory, from the caller's directory.
run_package() {
    package="$1"
    environment="$2"
    shift 2
    if ! command -v uv >/dev/null 2>&1; then
        echo "$(basename "$0"): needs uv on PATH (https://docs.astral.sh/uv/)" >&2
        exit 127
    fi
    root="$(cd "$(dirname "$0")/.." && pwd -P)"
    UV_PROJECT_ENVIRONMENT="$(plugin_data "$root")/$environment" \
        exec uv run --quiet --frozen --project "$root/$package" "$@"
}
