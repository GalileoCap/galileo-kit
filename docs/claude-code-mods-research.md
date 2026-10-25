# Claude Code plugins and mods: how they work, what they can do, how they update

Researched 2026-10-24 against Claude Code 2.1.296 (terminal) and 2.1.308 (the Desktop app's bundled copy). Sources: the official docs at code.claude.com/docs, the `plugin-authoring` skill's reference and API types shipped with 2.1.308, and the plugin state on this machine.

## Short answers

- Will plugins update under me? Only from marketplaces with auto-update on. That is on by default for Anthropic's official marketplaces (`claude-plugins-official` among them) and for marketplaces added from claude.ai, and off for every third-party marketplace. Three paths skip that switch. `command`-source plugins re-run their command once per session regardless of the setting. Plugins synced from your claude.ai account refresh at every terminal start. Any plugin loaded in place from a local folder runs whatever that folder holds at session start.
- When does an update take effect? For copied plugins, at the next launch or `/reload-plugins`. The files on disk change, the running session keeps the old version and shows `Plugin updated: <name> · Run /reload-plugins to apply`. A `command`-source plugin whose output changed is the exception: it is reloaded into the running session.
- What can a plugin do? Anything your user account can. The docs' security page opens with: "A Claude Code plugin you install can execute arbitrary code on your machine with your user privileges." Permission rules and the sandbox cover only the tool calls Claude makes. Code the plugin runs on its own escapes both.
- Are mods sandboxed? No. A mod runs JavaScript inside Claude Code's process, with `$` calls for files, processes, network, model calls, settings and the session.

## Vocabulary

| Term | What it is |
| --- | --- |
| Plugin | A folder with `.claude-plugin/plugin.json` (optional) and any of the components below. Installed from a marketplace, or loaded from a folder for one session. |
| Marketplace | A repository, URL or folder holding `.claude-plugin/marketplace.json`, which lists plugins and where to fetch each one. |
| Mod | A plugin whose `hooks/hooks.json` names a JS/TS hooks module (`{"modules": ["./register.ts"]}`) exporting `register(on, options)`. On by default since 2.1.287. In the mod docs "hook" means one of these in-process handlers, and the shell-command kind is a "settings hook". |
| Settings hook | A shell command, HTTP request or prompt run on a lifecycle event (`PreToolUse`, `PostToolUse`, `SessionStart` and others). Plugins ship them in `hooks/hooks.json`. `session-kit` is built from these. |

## What a plugin can contain, and what each part can reach

| Component | Where it runs | Reach |
| --- | --- | --- |
| Settings hooks (`hooks/hooks.json`) | Shell process, outside the sandbox | Full user privileges. Gets `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`, `CLAUDE_PROJECT_DIR` and `CLAUDE_PLUGIN_OPTION_<KEY>`, sensitive `userConfig` values included. Can block, rewrite or annotate tool calls and prompts. |
| Mod (hooks module) | Inside Claude Code's process, in its own JS environment with no Node or DOM. Everything external goes through `$`. | `$.fs` read and write anywhere you can, `$.process.run` and `spawn` (outside the sandbox), network, `$.model.complete` on your plan or key, `$.settings.read`, env vars, every prompt and tool call, `session.append` (rewrites the stored transcript), `prompt.compose` (rewrites the system prompt), `$.prompt.submit` (types prompts for you), approving tool calls, telemetry streams. Can redraw all of the UI except the permission prompt. |
| Monitors (`monitors/monitors.json`, experimental) | Background shell process, started at session start or on a skill's first run | Full user privileges, runs continuously. Not loaded for project-scoped plugins. |
| MCP servers (`.mcp.json` or `mcpServers`) | stdio process outside the sandbox, or a remote URL | Full user privileges for the process. Its tools go through permission rules when Claude calls them. May point at an `https://...mcpb` bundle that Claude Code downloads at load. |
| LSP servers (`.lsp.json`) | Process outside the sandbox | Full user privileges. Pushes diagnostics into context after edits. |
| `bin/` | Added to the Bash tool's `PATH` | Claude can run them, and each run is a Bash tool call under your permission rules. A `bin/` name can shadow a system command on that `PATH`. |
| Skills, commands, agents, output styles | Text in Claude's context | No code of their own. They steer what Claude does with the tools it has, which makes them the place prompt injection lives. |
| `settings.json` | Applied while enabled | Only `agent` and `subagentStatusLine` take effect. |
| Workflows, themes | Scripts and theme JSON | Workflows orchestrate subagents. |
| Node dependencies | Installed into the cache from `package.json` plus a lockfile | The install runs with `--ignore-scripts`, registry packages only, exact pins. The packages then run as part of hooks, mods or MCP servers, so a review has to cover them. |

### Mods versus your `session-kit` guard

From the mods overview: with managed settings, or a Team or Enterprise `/login` as the session's credential, a mod's approval does not get a call past your `ask` rules or `PreToolUse` hooks. Without either, "a mod can approve a call that an `ask` rule would prompt for, or that your `PreToolUse` hook blocked." The guard that enforces the **(refused)** rules is a `PreToolUse` settings hook (`hooks/guard.py`). On a personal login, any mod you install can override it. That is the strongest reason to read every mod's `tool.call` and `tool.check` hooks before installing it.

## How updates happen

### The version decides whether anything changes

Claude Code computes a version for each installed plugin and replaces the cached copy only when that version differs from the one in `installed_plugins.json`:

1. `version` in the plugin's `plugin.json`
2. else `version` in the marketplace entry
3. else from the source: the 12-character commit SHA for `github`, `url` and `git-subdir`, the SHA-256 for `archive`, and `unknown` for `npm` and for a local folder outside git

An author who sets `"version": "1.0.0"` and never bumps it ships nothing to existing users. One who omits `version` ships every commit.

### Background auto-update

- When: in an interactive session, at a random delay of up to ten minutes after your first message. It refreshes every marketplace with auto-update on and updates that marketplace's installed plugins on disk.
- Which marketplaces: the first setting found wins. First `autoUpdate` on the `extraKnownMarketplaces` entry in a settings file, then `autoUpdate` in `known_marketplaces.json` (written by the `/plugin` → Marketplaces → Enable/Disable auto-update toggle), then the default. The default is on for Anthropic's official names except `knowledge-work-plugins` and `first-party-plugins`, on for claude.ai marketplaces, and off for everything else.
- Kill switch: `DISABLE_UPDATES=1`, `DISABLE_AUTOUPDATER=1` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` turns the pass off, unless `FORCE_AUTOUPDATE_PLUGINS=1` is also set.
- Skipped: plugins whose entry declares a `headersHelper`. They appear in the Errors tab for a manual update.
- Mid-session: hooks, MCP and LSP servers keep the old path until `/reload-plugins`, and monitors keep it until restart. The previous version directory gets an `.orphaned_at` marker and is deleted 14 days later.

### Paths that change code without that switch

| Path | What happens |
| --- | --- |
| `command`-source plugin | The command you accepted at install re-runs once per session in the background, regardless of auto-update and `DISABLE_AUTOUPDATER`. If its output hash changed, the new version is installed and reloaded into the running session. A changed command needs your re-acceptance. |
| Plugins synced from claude.ai (`@synced`) | Sync once per terminal start in the background: new, updated and removed. `syncClaudeAiPlugins: false` turns it off. Org-required ones cannot be disabled. |
| Local-folder marketplace, relative-path entry | Loaded straight from the folder. Whatever the folder holds at session start or `/reload-plugins` runs, whatever the version string says. A `git pull` in that folder is an update. |
| `--plugin-dir`, `CLAUDE_CODE_PLUGIN_DIRS`, `~/.claude/skills/<name>` | Loaded from the folder and watched. Saving a file hot-reloads the mod. |
| `/plugin install name@marketplace` | Refreshes that marketplace's catalog first, regardless of auto-update. Installing a new plugin can pull a newer catalog. It leaves the other installed plugins at their versions. |
| `claude plugin marketplace update` with no name | Refreshes every catalog and leaves installed plugins alone. |
| Project `.claude/settings.json` in a cloned repo | Can enable plugins and declare marketplaces, after you accept that folder's trust dialog. A plugin with an external source is not fetched on that basis alone. You get an "enabled in project settings but isn't installed here" error instead. Project-scope plugins load without monitors and with per-server MCP approval. |
| `forceRemoveDeletedPlugins` in a marketplace | The marketplace owner can uninstall a delisted plugin from your machine at session start. |

### Your machine today

| Marketplace | Source | Auto-update |
| --- | --- | --- |
| `claude-plugins-official` | `anthropics/claude-plugins-official` | On (default). Catalog last refreshed 2026-10-24 14:10. |
| `galileo-kit` | `https://github.com/GalileoCap/galileo-kit.git` | Off (third-party default, no `autoUpdate` key set). |

- The Desktop app launches its bundled Claude Code with `DISABLE_AUTOUPDATER=1`. The variable is in this session's environment and in none of your shell profiles. In Desktop Code-tab sessions the background plugin pass never runs. A terminal `claude` session runs it for `claude-plugins-official`.
- Installed: `session-kit@galileo-kit` 0.5.1 (user scope plus project installs), and `pyright-lsp` and `typescript-lsp` 1.0.0 from the official marketplace (project scope, 26 installs each). The cache still holds `session-kit` 0.1.0 to 0.5.0.
- Synced from claude.ai: two copies of `cowork-plugin-management`.
- `session-kit` pins `"version"`, so a commit reaches you only after the version string is bumped and you update.

## Installing third-party mods

1. Third-party marketplaces are already off for auto-update. Code changes under you only if you turn that on, use `command` sources, sync from claude.ai, or `git pull` into a local folder marketplace.
2. Pinning belongs to the author, except through the marketplace you add. You can add a marketplace at a ref (`owner/repo#v1.2.0`), and the plugin entries inside it can still point at moving branches of other repositories. Your own fork holds every byte to something you reviewed.
3. Read before you install. `claude plugin validate <dir>` lists a mod's `hooks:` (events it handles, with `gating hook` lines for those that can refuse or approve) and `calls:` (what it asks `$` for: `fs`, `process`, network, `model`, `settings`, `session.append`, `prompt.submit`, telemetry streams). `claude --plugin-dir <dir> plugin details <name>` prints the component inventory without starting a session.
4. Load for one session first. `claude --plugin-dir <clone>` loads it without installing. `--safe-mode` or `"disableAllHooks": true` stops installed mods, and built-in mods keep running.

## Forking model

The `galileo-kit` marketplace already has the right shape. For each mod we adopt:

1. Clone upstream into a folder of the `session-kit` repository (it is already the marketplace), with upstream's URL noted for later diffs.
2. Review at a fixed commit. Set `"version"` in its `plugin.json` so changes ship only when you bump it.
3. List it in `marketplace.json` as a relative-path entry. Avoid `command` sources and `headersHelper`, and vendor any `.mcpb` bundle instead of referencing it by URL.
4. Auto-update on `galileo-kit` becomes safe to turn on once every plugin in it is yours: it then delivers only versions you reviewed and bumped.
5. To take upstream changes: fetch upstream, review the diff, merge, bump `version`, push, then `claude plugin update <name>@galileo-kit`.

## Porting `session-kit` to a mod, and folding forks into it

### What a port would gain

- An in-process guard. A `tool.call` or `tool.check` hook with a `.catch` that denies sits in the same chain as other mods, which a `PreToolUse` script does not. Whether your guard runs above or below a third-party mod's approval depends on mod ordering. The overview names "the order mods run in" under React to events, and that page needs reading before we count on it.
- UI instead of transcript text. Context pressure can be a band above the prompt or a status line entry. The test-run log can be a pane. Prose-tell findings can be a toast.
- Commands that answer with no model turn (`$.command.register`). `/session-kit:handoff` stays a skill since it needs the model, while a `/tells` or `/pressure` readout would cost no tokens.
- `$.state` and `$.store` for counters such as the 25k-token warning cadence, in place of files under the plugin data folder.
- Fewer process spawns. Each `PostToolUse` on `*` currently starts a Python process per tool call. An in-process hook avoids that.

### What it costs

- A rewrite from Python into TypeScript. The module has no Node, so the Python logic either moves into TS or stays as scripts that the mod runs with `$.process.run`. The second keeps the spawn cost.
- API churn. The reference calls the mods API "early access", one that "moves between releases". `guard.py` rides the stable settings-hook contract today.
- `bin/` (`session-tells`, `session-codeintel`) and the LSP shims stay as they are, since mods do not replace them.
- Reach. Mods run in the terminal, the Desktop Code tab and VS Code. Settings hooks also run in places mods draw nothing (`-p`, SDK), and both run there, so this is a wash for hooks and a loss only for anything drawn.

A port can be incremental. One plugin can hold both a `hooks.json` with settings hooks and a hooks module, so the first step is one mod-only feature (a context-pressure band, say) beside the existing Python hooks, with the guard moved later.

### Folding forked mods into `session-kit`

I would keep forks as separate plugins in the `galileo-kit` marketplace. Merging them into `session-kit` itself has three costs:

- One version bump ships every feature at once, so an upstream fix to one mod forces a release of all of them.
- Turning one feature off means a `userConfig` toggle you write and maintain, where a separate plugin is disabled from `/plugin`.
- A mod that hooks hot events (`ui.render`, `turn.step`) loads in every session that has `session-kit`, wanted or not.

Merging pays off for a mod that shares code or `$.state` with `session-kit`. Declaring `dependencies` in `plugin.json` gets most of that without the merge: a separate plugin can depend on `session-kit` and read the nouns it adds to `$`, typed through its contract file.

## Review checklist for each candidate mod

- `plugin.json`: is `version` present? `dependencies` (pulls in other plugins)? `userConfig` with `sensitive` fields (secrets it will receive)?
- `hooks/hooks.json`: every settings hook command and the script it runs, plus the `modules` entry for a mod.
- Mod module: the `claude plugin validate` output. Every `tool.call` and `tool.check` hook (can it approve or rewrite?), `prompt.compose` and `session.append` (can it change the system prompt or transcript?), `$.process`, `$.fs` writes, network targets, `$.model` calls (cost per turn), `telemetry.*` hooks, timers (`$.clock.every` is background cost).
- `.mcp.json` and `mcpServers`: commands, remote URLs, bundle URLs.
- `monitors`, `bin/`, `.lsp.json`.
- `package.json` and the lockfile: dependency tree size and provenance.
- Skills, agents, commands: injected instructions, and `allowedTools` grants on commands.
- Efficiency: hooks on hot events (`ui.render`, `turn.step`, `tool.call` with no matcher, `PostToolUse` on `*`), always-on context tokens (`claude plugin details` reports the `Always-on` count), model calls per turn.

## Sources

- [Plugin security and trust](https://code.claude.com/docs/en/plugins/security.md)
- [Mods overview](https://code.claude.com/docs/en/plugins/mods/overview.md)
- [Plugin loading reference](https://code.claude.com/docs/en/plugins/loading.md): versions, auto-update, in-place loading, synced plugins
- [Install and manage plugins](https://code.claude.com/docs/en/plugins/install.md)
- [Host and maintain a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace.md)
- [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference)
- [Create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
- `plugin-authoring` skill reference and `types/claude-code.d.ts`, bundled with Claude Code 2.1.308
- Local: `~/.claude/settings.json`, `~/.claude/plugins/known_marketplaces.json`, `~/.claude/plugins/installed_plugins.json`
