# Owed

What a change leaves to do outside the code, one entry per change, under the moment it is due. Entries are only ever added. `session-owed --since <ref>` lists what a range of history owes.

## At the install of session-kit 0.35.0

### main, b9b49e7 and before: the terminal's engine at 2.1.308

From 0.28.0 on, the hooks module shares `gitOutput` across files (`e7c005e`), which the terminal's `claude` 2.1.296 refuses, so a terminal session would load none of the kit's in-process hooks. The nix-darwin repository moves `nixpkgs-unstable` to a revision carrying claude-code 2.1.308 in its commit `73b6118`, built and checked: the kit validates and its 67 engine tests pass on that binary. The switch needs the owner's password:

```bash
sudo darwin-rebuild switch --flake ~/.config/nix-darwin
```

Then `command claude --version` prints 2.1.308. The `chain` option in `~/.config/nix-darwin/claude/settings.json` is the owner's uncommitted change there, and with it on the chain and the cold-cache timer (`A49`) run after the install.

### main, b9b49e7: pushed

The marketplace clone under `~/.claude/plugins/marketplaces/galileo-kit` pulls from GitHub, so the nineteen commits from 0.22.0 to 0.35.0 reach it only once `main` is pushed (`git push origin main`), on the owner's word.

### main, b9b49e7: the plugin updated in every scope

The kit is installed at user scope and at project scope in ten projects, each recorded at 0.21.1 in `~/.claude/plugins/installed_plugins.json`. Run with `command`, past the shell's alias:

```bash
command claude plugin marketplace update galileo-kit
command claude plugin update session-kit@galileo-kit --scope user
```

Then from each project that records a project-scope install, `command claude plugin update session-kit@galileo-kit --scope project`. Whether the user-scope update moves the project entries too is unverified, so `installed_plugins.json` is read after it. Running sessions keep 0.21.1 until `/reload-plugins` or a restart, the desktop app's included.

## After the install of session-kit 0.35.0

### main, b9b49e7: what only a real session proves

Each of these ran in the engine's tests alone: the facts section after a handoff (`A63`), the projected context figure (`A62`), a chain in a terminal session, the cold-cache timer (`A49`), the Haiku judge's verdicts (`A54`), and `/effort` run by the new-task offer's press in the desktop app (`A65`). `docs/PLAN.md`, Next item 8, holds the owner's two reviews: the usage-window line (`A50`) and facts on the UI.

## At the install of session-kit 0.35.1

### main, A66: the test log's fix pushed and updated

`A66` (a test run is what the guard calls one, and a stale run is said once) reaches a session only through the marketplace: `main` pushed on the owner's word, then the marketplace and the plugin updated as for 0.35.0. This repository's runner entry is now `claude plugin test`, so its engine tests are logged once the terminal's `claude` is 2.1.308.

## At the install of session-kit 0.35.2

### main, C2: the timeline's classic hooks removed

`measure.ts` no longer hooks `classic.PostToolUse` or `classic.PostToolUseFailure`, which the organization's security default sends past the kit (`C2`). It reaches a session only after `main` is pushed on the owner's word and the plugin is updated at user scope and in each project install, as for 0.35.1. Until then every session on 0.35.1 shows the two skip notices once each.
