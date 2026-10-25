// The timeline, in-process: one JSON line per turn start and end, tool call,
// tool execution and session end, buffered in memory and written
// at each main-loop turn end and at the session's end as a new file,
// `~/.claude/session-kit/measure/<session id>/<epoch ms>.jsonl`, since the
// engine's file system has no append. The kit's Python readers join the files
// to the transcripts by session id, and the arithmetic is theirs.
//
// The kit's own cost is what only the kit can record. `kit.tsx` registers a
// stopwatch before each concern and one after the last, and the hooks of one
// module nest in the order they are registered, so each stopwatch times its
// concern and everything beneath it. The difference between two adjacent
// stopwatches is one concern's own time and the context it added, the last is
// the time beneath the kit (other plugins, the permission prompt, the tool),
// and `classic.PostToolUse` gives the tool's own execution apart.
//
// The lines:
//   turn.start  turn, agent
//   tool        id, tool, agent, turn (the loop's, from its turn.start), ms
//               (around the call), kitMs (per concern), beneathMs, added
//               (per concern: entries and chars of context), error, denied
//   tool.exec   id, tool, ms (the tool's execution), failed
//   turn.end    turn, agent, reason, durationMs, usage, ms, kitMs, beneathMs,
//               and on the main loop the context figure and costUsd
//   memory      files (path, type, tokens): the engine's estimate of each
//               memory file a turn loads, read at the first main-loop turn
//               end of a context (a new session, or one compacted)
//   session.end reason
//   session     from, reason: the first line of a session a clear or a
//               resume started in the same process, naming the one before
// Every line carries `at`, epoch milliseconds, read from the module's own
// clock so a tool call costs no call on `$`. A compaction has no line: the
// transcript's `compact_boundary` records each one with more than a hook
// sees.
//
// The `measure` option off registers nothing. A line that cannot be written
// is dropped, so the timeline never holds a session up.

import type { EngineInterface, On, Register } from 'claude-code'

type Options = Parameters<Register>[1]
type Line = { at: number; ev: string } & Record<string, unknown>
type Lap = { ms: number; entries: number; chars: number }
type Split = { kitMs: Record<string, number>; beneathMs?: number; added?: Record<string, { entries: number; chars: number }> }

const BENEATH = 'beneath'
// Past this many lines a call writes them at once, well under the engine's 4 MiB write.
const FLUSH_LINES = 2000

// Per tool call and per turn, the stopwatches' laps by concern, the innermost first.
const toolLaps = new Map<string, Map<string, Lap>>()
const turnLaps = new Map<string, Map<string, Lap>>()
// Per loop ('' the main one), the turn under way, which a tool call does not carry.
const loopTurns = new Map<string, string>()
let lines: Line[] = []
let lastWriteAt = 0
let memoryReadIn = ''
let lastTurnTokens = 0

function isOn(options: Options): boolean {
  return options.measure !== false
}

function round(ms: number): number {
  return Math.round(ms * 100) / 100
}

function loop(agentId: string | undefined): { agent?: string } {
  return agentId === undefined ? {} : { agent: agentId }
}

export function timelinePath(home: string, sessionId: string, at: number): string {
  const safe = sessionId.replace(/[^\w-]/g, '_') || 'session'

  return `${home.replace(/\/+$/, '')}/.claude/session-kit/measure/${safe}/${at}.jsonl`
}

function note(laps: Map<string, Map<string, Lap>>, key: string, name: string, ms: number, context: readonly string[] | undefined): void {
  const by = laps.get(key) ?? new Map<string, Lap>()
  by.set(name, { ms, entries: context?.length ?? 0, chars: context?.reduce((n, text) => n + text.length, 0) ?? 0 })
  laps.set(key, by)
}

function take(laps: Map<string, Map<string, Lap>>, key: string): Map<string, Lap> {
  const by = laps.get(key) ?? new Map<string, Lap>()
  laps.delete(key)

  return by
}

/** Each concern's own time and context from the laps of adjacent stopwatches, and what lies beneath the kit. */
function split(laps: Map<string, Lap>): Split {
  const outermostFirst = [...laps.entries()].reverse()
  const kitMs: Record<string, number> = {}
  const added: Record<string, { entries: number; chars: number }> = {}
  let beneathMs: number | undefined
  outermostFirst.forEach(([name, lap], i) => {
    const inner = outermostFirst[i + 1]?.[1] ?? { ms: 0, entries: 0, chars: 0 }
    const entries = lap.entries - inner.entries
    if (entries !== 0) {
      added[name] = { entries, chars: lap.chars - inner.chars }
    }
    if (name === BENEATH) {
      beneathMs = round(lap.ms)
    } else {
      kitMs[name] = round(lap.ms - inner.ms)
    }
  })

  return { kitMs, ...(beneathMs === undefined ? {} : { beneathMs }), ...(Object.keys(added).length === 0 ? {} : { added }) }
}

async function write($: EngineInterface, sessionId?: string): Promise<void> {
  if (lines.length === 0) {
    return
  }
  const taken = lines
  lines = []
  try {
    const home = await $.env.get('HOME')
    if (home === undefined || home === '') {
      return
    }
    const id = sessionId ?? (await $.session.id())
    const at = Math.max(Date.now(), lastWriteAt + 1)
    lastWriteAt = at
    await $.fs.write(timelinePath(home, id, at), `${taken.map((line) => JSON.stringify(line)).join('\n')}\n`)
  } catch {
    // The lines are dropped: the kit is never the reason a session fails.
  }
}

/** The main loop's turn end: the context figure and the cost on its line, the memory files once per context, then the file. */
async function endOfTurn($: EngineInterface, line: Line): Promise<void> {
  let tokens: number | undefined
  let figure = {}
  try {
    const { context, cost } = await $.session.usage()
    tokens = context.tokens
    figure = { ...(tokens === undefined ? {} : { context: { tokens, window: context.window, percent: context.percent } }), ...(cost === undefined ? {} : { costUsd: Math.round(cost.usd * 1e6) / 1e6 }) }
  } catch {
    // The line goes without the figure.
  }
  lines.push({ ...line, ...figure })
  let id: string | undefined
  try {
    id = await $.session.id()
    // A new session, or a context smaller than the last turn's (a compaction), loads its memory files afresh.
    if (id !== memoryReadIn || (tokens !== undefined && tokens < lastTurnTokens)) {
      const files = (await $.session.usage({ breakdown: 'summary', columns: 40 })).context.breakdown?.memoryFiles ?? []
      lines.push({ at: Date.now(), ev: 'memory', files: files.map((f) => ({ path: f.path, type: f.type, tokens: f.tokens })) })
      memoryReadIn = id
    }
    lastTurnTokens = tokens ?? lastTurnTokens
  } catch {
    // No memory line this turn: the next main-loop turn end tries again.
  }
  await write($, id)
}

/** A stopwatch on the tool calls and the turn ends: it times everything registered after it, and what that added. */
export function lap(on: On, options: Options, name: string): void {
  if (!isOn(options)) {
    return
  }
  on('tool.call', { tool: /./ }, async ($, e, next) => {
    const started = performance.now()
    const ran = await next(e)
    note(toolLaps, e.tool_use_id, name, performance.now() - started, ran.context)

    return ran
  }).catch(($, e, next) => next(e))

  on('turn.complete', { turnId: /./ }, async ($, e, next) => {
    const started = performance.now()
    const done = await next(e)
    note(turnLaps, e.turnId, name, performance.now() - started, undefined)

    return done
  }).catch(($, e, next) => next(e))
}

/** The stopwatch after the last concern: what it times is beneath the kit. */
export function lapBeneath(on: On, options: Options): void {
  lap(on, options, BENEATH)
}

export const register: Register = (on, options) => {
  if (!isOn(options)) {
    return
  }

  on('turn.start', { turnId: /./ }, async ($, e, next) => {
    loopTurns.set(e.agentId ?? '', e.turnId)
    lines.push({ at: Date.now(), ev: 'turn.start', turn: e.turnId, ...loop(e.agentId) })

    return next(e)
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: /./ }, async ($, e, next) => {
    const started = performance.now()
    const ran = await next(e)
    const ms = performance.now() - started
    const turn = loopTurns.get(e.agentId ?? '')
    lines.push({
      at: Date.now(),
      ev: 'tool',
      id: e.tool_use_id,
      tool: e.tool,
      ...loop(e.agentId),
      ...(turn === undefined ? {} : { turn }),
      ms: round(ms),
      ...split(take(toolLaps, e.tool_use_id)),
      ...(ran.isError === true ? { error: true } : {}),
      ...(ran.deny === undefined ? {} : { denied: true }),
    })
    if (lines.length >= FLUSH_LINES) {
      await write($)
    }

    return ran
  }).catch(($, e, next) => next(e))

  on('classic.PostToolUse', async ($, e, next) => {
    if (e.duration_ms !== undefined) {
      lines.push({ at: Date.now(), ev: 'tool.exec', id: e.tool_use_id, tool: e.tool_name, ms: e.duration_ms })
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  on('classic.PostToolUseFailure', async ($, e, next) => {
    if (e.duration_ms !== undefined) {
      lines.push({ at: Date.now(), ev: 'tool.exec', id: e.tool_use_id, tool: e.tool_name, ms: e.duration_ms, failed: true })
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  on('turn.complete', { turnId: /./ }, async ($, e, next) => {
    const started = performance.now()
    const done = await next(e)
    const line: Line = {
      at: Date.now(),
      ev: 'turn.end',
      turn: e.turnId,
      ...loop(e.agentId),
      reason: e.reason,
      durationMs: e.durationMs,
      ...(e.usage === undefined ? {} : { usage: e.usage }),
      ms: round(performance.now() - started),
      ...split(take(turnLaps, e.turnId)),
    }
    if (e.agentId === undefined) {
      await endOfTurn($, line)
    } else {
      lines.push(line)
    }

    return done
  }).catch(($, e, next) => next(e))

  // Written before the engine's end step, which may be the process's last.
  on('session.end', async ($, e, next) => {
    lines.push({ at: Date.now(), ev: 'session.end', reason: e.reason })
    await write($, e.sessionId)
    if (e.reason === 'clear' || e.reason === 'resume') {
      lines.push({ at: Date.now(), ev: 'session', from: e.sessionId, reason: e.reason })
    }

    return next(e)
  }).catch(($, e, next) => next(e))
}
