# Review: cache-tax

| | |
| --- | --- |
| Upstream | https://github.com/karanb192/cache-tax |
| Reviewed at | `e4940afcc62c109bd667bae1b996bee765021759` (tag `v2.3.1`, 2026-10-22) |
| Served by | marketplace `karanb192/claude-code-mods` at `fb1f9c0`, entry `{"source": "github", "repo": "karanb192/cache-tax"}` with no ref or SHA |
| Version | `"version": "2.3.1"` in `plugin.json`, so installed copies change only on a bump |
| Reviewed on | 2026-10-24, Claude Code 2.1.296 (`claude plugin validate`, `plugin details`), API types and prices from the 2.1.308 bundle |
| Not run | `claude plugin test` and `tsc`, because both execute or build from the clone before this review existed |

## What it does

Claude Code's main prompt cache lives one hour. A message sent after it lapses re-writes all of its context at the 1-hour cache-write rate (2x base input), which on a 300k context of Fable 5.1 is about $6. cache-tax does three things about that.

1. Guard. On a `prompt.submit` from a person, when its own clock says the cache is cold and the context is at least 50k tokens, it drops the message once and shows the estimated price. Sending it again goes through. `/cache-tax guard warn` turns the drop into a logged line.
2. Keepwarm. `/keepwarm [6h | 90m | always | off | status]` arms a window. After 50 idle minutes inside it, a timer sends `$.model.fork` with the prompt `Reply with the single word: warm`. The fork replays the main thread's last request, so it reads the cached prefix and resets its timer. It stops when the reply shows the prefix was already gone (zero reads, or writes of a tenth of the reads or more).
3. Score. After each turn it detects a cold write (writes of at least half the previous context) and logs its price. A detected cold write arms keepwarm for three hours (six with `always`) without being asked.

It draws a row above the prompt in the terminal and the Desktop Code tab, and falls back to the status line elsewhere.

## Inventory

| Path | Lines | Role |
| --- | --- | --- |
| `.claude-plugin/plugin.json` | 9 | Name, version 2.3.1, MIT. No `dependencies`, no `userConfig`. |
| `hooks/hooks.json` | 6 | `{"modules": ["./register.ts"]}` only. No settings hooks. |
| `hooks/register.ts` | 786 | The mod. Read in full. |
| `hooks/status-icons.ts` | 31 | Six inline SVGs and six base64 PNGs. Decoded: each PNG has a valid header and is about 3.3 kB, each SVG is 359 bytes with no script, link or external reference. |
| `tests/register.test.ts` | 2286 | Mock-engine tests. Imports only `claude-code/testing`, `claude-code` types and the module. No network, file or process calls. |
| `tools/generate-status-icons.py` | 32 | Maintainer script that runs `rsvg-convert`. Not loaded by the mod. |
| `site/`, `docs/`, `.github/` | | Landing page (one inline script), a 5 MB video, a Pages deploy workflow. The mod never loads them. An install copies them into the plugin cache: about 7 MB of the 16 MB clone. |

`claude --plugin-dir … plugin details cache-tax`: no skills, agents, settings hooks, MCP or LSP servers. Always-on context cost about 0 tokens.

## Checklist: malicious behaviour

| Item | Finding |
| --- | --- |
| `plugin.json` | `version` present. No `dependencies`, no `userConfig`, so it receives no secrets. |
| Settings hooks | None. |
| `tool.call` / `tool.check` | None. It cannot approve, deny or rewrite a tool call, so it cannot override the `session-kit` `PreToolUse` guard on any login type. |
| `prompt.compose`, `session.append` | None. It never changes the system prompt or the stored transcript. |
| `prompt.submit` | Gating. It reads `e.origin.kind` and whether the text starts with `/` (line 663), never keeps or logs the text, and either passes it on untouched or returns `{ drop }`. Prompts from `task-notification`, `scheduled-trigger`, peers, coordinators and observers are never dropped, only logged (line 20), so it cannot lose a prompt no person can resend. |
| Other gating hooks | `config.set{key=theme}` passes the result through and reads whether the theme starts with `light`. `classic.SessionStart` and `session.compact` call `next` first and only update state. The validator notes none of the four has a `.catch`. A throw makes the engine skip the hook, so the prompt goes through unguarded, which fails open. |
| `$.fs`, `$.process`, network, `$.settings` | None. |
| `$.model` | `$.model.fork` only, from `ping` (line 383), with a constant prompt. Nothing from a tool result, file or prompt reaches it. |
| Env | Reads `NO_COLOR`, writes nothing. |
| Telemetry hooks | None. |
| `$.store` | Keys `deadline:<session id>`, `every:<session id>`, `always`, `guard`. Numbers, a boolean and a string. |
| MCP, monitors, `bin/`, LSP | None. |
| `package.json`, lockfile | None. No dependencies. |
| Skills, agents, commands | Two mod commands (`/keepwarm`, `/cache-tax`) answered in-process with text. No injected instructions, no `allowedTools`. |
| Update path | Third-party marketplace, so auto-update is off by default. The entry follows the repository's default branch, and `"version"` gates it, so new code reaches an install only through `claude plugin update` after a bump. |

Nothing malicious. The mod's own threat model in its README matches the code line for line.

## Checklist: inefficiency and defects

| Item | Finding | Weight |
| --- | --- | --- |
| Sonnet 5.5 price row | `['sonnet-5-5', 0.1, 4, 10]` (line 36). The bundled API docs give Sonnet 5.5 cache reads at $0.20 per MTok (0.1x of $2 base). The mod uses $0.10. On Sonnet 5.5 the card's warm-turn price and each ping's cost read at half, and the break-even shows 40 pings where 20 is right, which makes keepwarm look twice as cheap as it is. Every other row matches: Fable 5.1 ($0.25 / $20 / $50), Fable 5 ($1 / $20 / $50), Opus 5.5 ($0.20 / $8 / $20), Opus 5 and 4.5 to 4.8 ($0.50 / $10 / $25), Opus 4 and 4.1 ($1.50 / $30 / $75), Sonnet 5 ($0.20 / $4 / $10), Sonnet 4.x ($0.30 / $6 / $15), Haiku 5.5 with its long-prompt tier, Haiku 4.5 and 3.5. | Defect, upstreamable |
| Ping output is uncapped | `ModelForkRequest` takes only `prompt`, so a ping cannot set `max_tokens` or effort. A model that thinks before answering "warm" bills that thinking at the output rate, $50 per MTok on Fable 5.1. The README discloses it. The API's own keep-alive (`max_tokens: 0`) is out of reach from a mod. | Engine limit |
| Auto-arm after a cold write | A detected cold write opens a three-hour window without a command (line 762). Inside it, every 50 idle minutes costs one ping. On Fable 5.1 at 300k tokens a ping reads about $0.08 plus its output, so a break that ends the day costs up to three pings. Cheap next to a $6 write, but it spends without an opt-in, and on a subscription nobody has documented how reads count against the 5-hour and weekly limits. | Policy choice |
| Fixed one-hour clock | `TTL_MS` is a constant. On an API key, usage credits or a cloud provider the main cache defaults to five minutes unless `promptCacheTtl` is `"1h"`. There the guard believes the cache warm for 55 minutes after it went cold, so it under-warns, and keepwarm cannot help. The mod does not read the setting. | Limit |
| Hot events | `ui.render{AbovePrompt}` runs on every redraw of the band, with one `$.clock.now()` and a short tree. `turn.step` runs per model request, with one clock read. `turn.complete` adds a `$.store.get` and a `$.session.usage()` per turn. All in-process, no spawn, no transcript reads. | Fine |
| Store growth | `session.end` cleans up only on `/clear` or resume. A session that exits normally with `always` on leaves `deadline:<id>` behind, and only that same id's next start prunes it. One small key per such session, forever. | Minor |
| Install size | The plugin cache gets the site, the video and the fonts, about 7 MB, none of it used at runtime. | Minor |
| Double guard | It detects its own settings-hook twin by the `cache-tax:status` command. Any other cold-send guard (one we add to `session-kit`, say) would fire alongside it unseen. | Note |

Not verified: whether the engine puts a dropped prompt's text back in the input box. The README's recording shows a resend, and the type docs say only that the hook's text is shown as the reason.

## Overlap with `session-kit`'s context guard

`session-kit` warns about context fill: `hooks/context_pressure.py`, a `PostToolUse` hook on `*`. cache-tax prices cache expiry. They measure the same context-token figure along different axes.

| | `context_pressure.py` | cache-tax |
| --- | --- | --- |
| Question | Is the window filling? | Has the cache lapsed, and what will the next send cost? |
| Audience | Claude, through `additionalContext`, plus a `systemMessage` | The person, through a band, a log line or a dropped prompt |
| Trigger | After every tool call from half the window, again every 25k tokens | Each prompt, each model request, each turn, a timer |
| Context figure | Parses the last assistant `usage` from the transcript's last 256 kB | `$.session.usage().context.tokens`, the engine's own number |
| Cost per event | A Python process plus a 256 kB read per tool call | An in-process call |
| Advice | Commit, write `CLAUDE.local.md`, tell the owner it is safe to compact | Resend to pay, or `/clear` and start from a note |

Where they meet: a large context with a lapsed cache is the cheapest moment to run `/session-kit:handoff` and `/clear` instead of paying the write. cache-tax's refusal already says "start from a note" without naming a way to write one, and `session-kit` has that way.

### What could move into `session-kit`

1. A cold-send guard as a `UserPromptSubmit` settings hook. A settings hook can block a prompt (the type docs list "a settings hook's block beneath" as one way a prompt is dropped), and the transcript carries each message's timestamp and usage, which `context_pressure.py` already parses. One spawn per prompt instead of per tool call. Its refusal would name `/session-kit:handoff` then `/clear`. It cannot be installed beside cache-tax without a double guard.
2. One band for both signals, once `session-kit` has its first mod: context fill and cache state side by side above the prompt, both read from `$.session.usage()`. That is the band the deferred port in `PLAN.md` already names, and it would retire the per-tool-call Python spawn.
3. Keepwarm only works as a mod (`$.model.fork`, `$.clock.after`). It would come with the port, or stay in cache-tax.

### What could go upstream

- The Sonnet 5.5 cache-read price, as a one-line PR with a test row.
- An optional handoff command in the refusal text, configurable, for anyone with a note-writing skill.
- Reading `promptCacheTtl` through `$.settings.read` to choose the one-hour or five-minute clock. That adds `settings` to its reach, which the author may decline.

## Verdict: fork

The code is safe to install as it stands. It has no tool-call hooks, no file, process or network reach beyond one fork per idle stretch, and its threat model is accurate. The reason to fork is control over what runs and when it changes.

- The Sonnet 5.5 row is wrong today. Upstream will likely take a PR, but a fork carries the fix now.
- The owner wants to fold the cache signal into `session-kit`'s context guard. A fork at a fixed commit is the base for that, and the fork's refusal can name `/session-kit:handoff`.
- Upstream is busy (four releases in five weeks, each reworking subtle event races). A pinned fork takes those as reviewed diffs.

Shape, per `CLAUDE.md`: a separate plugin in `galileo-kit` with a relative-path entry and `"version": "2.3.1-galileo.1"`, without `site/`, `docs/` and `.github/`. It moves into `session-kit` only once the shared band exists and the two share state.

Changes for the first fork release, each for the owner to confirm:

1. Sonnet 5.5 cache read at $0.20, with a test. Also sent upstream.
2. The refusal names `/session-kit:handoff` then `/clear` as the alternative to paying.
3. Auto-arm after a cold write: keep it, or make it opt-in behind `/keepwarm auto`.

If the owner would rather not maintain a fork yet, "install as is" is a sound fallback: add the `claude-code-mods` marketplace (auto-update stays off), install `cache-tax` only, and send the price PR.
