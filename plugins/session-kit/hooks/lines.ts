// The words and figures the kit shows the person, as plain functions of the
// kit's state: the clock, compact numbers, the usage windows, the chain's and
// the offer's lines, the status line and the pane's bars. Nothing here reads
// the engine.

import type { SessionRateLimit } from 'claude-code'

import type { ChainState, ContextFigure, NewTaskState } from '../types'

export const LIMIT_WARN = 80
export const LIMIT_FIRM = 95
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const BAR_CELLS = 20

export function clockTime(when: Date): string {
  return `${String(when.getHours()).padStart(2, '0')}:${String(when.getMinutes()).padStart(2, '0')}`
}

/** 312,000 as `312k`, 1,000,000 as `1M`, 1,500,000 as `1.5M`. */
export function compact(n: number): string {
  if (n >= 1_000_000) {
    const millions = n / 1_000_000

    return Number.isInteger(millions) ? `${millions}M` : `${Math.round(millions * 10) / 10}M`
  }

  return n >= 1000 ? `${Math.round(n / 1000)}k` : String(n)
}

/** A bar of `BAR_CELLS` cells, filled in proportion to `percent`. */
export function bar(percent: number): string {
  const filled = Math.max(0, Math.min(BAR_CELLS, Math.round((percent * BAR_CELLS) / 100)))

  return '█'.repeat(filled) + '░'.repeat(BAR_CELLS - filled)
}

export function clip(text: string, max: number): string {
  const flat = text.trim()

  return flat.length > max ? `${flat.slice(0, max - 1)}…` : flat
}

/** The text with its end made a full stop. */
export function sentence(text: string): string {
  return `${text.trim().replace(/[\s.:;,!]+$/, '')}.`
}

function limitName(kind: string): string {
  switch (kind) {
    case 'five_hour':
      return 'The 5-hour usage window'
    case 'seven_day':
      return 'The 7-day usage window'
    case 'spend_limit':
      return 'The spend limit'
    default:
      return `The ${kind.replace(/_/g, ' ')} window`
  }
}

function windowShort(kind: string): string {
  switch (kind) {
    case 'five_hour':
      return '5h'
    case 'seven_day':
      return '7d'
    case 'spend_limit':
      return 'spend'
    default:
      return kind.replace(/_/g, ' ')
  }
}

function resetDate(w: SessionRateLimit): Date | null {
  if (w.resetsAt === undefined) {
    return null
  }
  const when = new Date(w.resetsAt)

  return Number.isNaN(when.getTime()) ? null : when
}

/** A 5-hour window resets within the day, so its time is enough; any other names the day too. */
function resetClause(w: SessionRateLimit): string {
  const when = resetDate(w)
  if (when === null) {
    return ''
  }

  return w.kind === 'five_hour'
    ? ` and resets at ${clockTime(when)}`
    : ` and resets on ${when.getDate()} ${MONTHS[when.getMonth()]} at ${clockTime(when)}`
}

/** `resets 14:30` for a 5-hour window, `resets 28 Oct 09:00` for any other; empty when the engine gave no time. */
function resetShort(w: SessionRateLimit): string {
  const when = resetDate(w)
  if (when === null) {
    return ''
  }

  return w.kind === 'five_hour' ? ` resets ${clockTime(when)}` : ` resets ${when.getDate()} ${MONTHS[when.getMonth()]} ${clockTime(when)}`
}

/** A window as the pane draws it: its short name, the percent, a bar, and when it resets. */
export function windowRow(w: SessionRateLimit): string {
  return `${windowShort(w.kind)}  ${w.percentUsed}%  ${bar(w.percentUsed)}${resetShort(w)}`
}

export function limitLine(w: SessionRateLimit): string {
  return `${limitName(w.kind)} is at ${w.percentUsed}%${resetClause(w)}.`
}

/** 0 below the warning, 1 from 80%, 2 from 95%. */
export function limitTier(percentUsed: number): number {
  if (percentUsed >= LIMIT_FIRM) {
    return 2
  }

  return percentUsed >= LIMIT_WARN ? 1 : 0
}

/** Whether a window's band row draws: from `floor` and not dismissed, or dismissed below 95 and now past it. */
export function showsLimit(w: SessionRateLimit, mark: number | undefined, floor: number): boolean {
  if (w.percentUsed < floor) {
    return false
  }

  return mark === undefined || (mark < LIMIT_FIRM && w.percentUsed >= LIMIT_FIRM)
}

export function sameWindows(a: SessionRateLimit[], b: SessionRateLimit[]): boolean {
  return a.length === b.length && a.every((w, i) => w.kind === b[i]?.kind && w.percentUsed === b[i]?.percentUsed && w.resetsAt === b[i]?.resetsAt)
}

/** What the kit pins under the prompt: the context with its growth, each usage window, and when the cold-cache timer runs; undefined when nothing is known. */
export function statusText(now: ContextFigure | null, grewBy: number, windows: readonly SessionRateLimit[], coldAt: number): string | undefined {
  const parts: string[] = []
  if (now !== null) {
    parts.push(`ctx ${now.percent}% ${compact(now.tokens)}${grewBy > 0 ? ` (+${compact(grewBy)})` : ''}`)
  }
  for (const w of windows) {
    parts.push(`${windowShort(w.kind)} ${w.percentUsed}%${w.percentUsed >= LIMIT_WARN ? resetShort(w) : ''}`)
  }
  if (coldAt !== 0) {
    parts.push(`compacts at ${clockTime(new Date(coldAt))}`)
  }

  return parts.length === 0 ? undefined : parts.join(' · ')
}

export function stageLine(state: ChainState): string {
  switch (state.stage) {
    case 'requested':
      return 'Clear point: the handoff, the compaction and the continue run when this turn ends.'
    case 'handoff':
      return 'session-kit is writing the handoff.'
    case 'compacting':
      return 'session-kit is compacting the context.'
    case 'waiting':
      return state.stopped === undefined
        ? `Compacted. The next step is yours: ${state.note}`
        : `Compacted. The next step is yours: ${sentence(state.note)} The chain stopped since ${state.stopped}`
  }
}

function proposal(effort: { level: string; reason: string }): string {
  return effort.reason === '' ? effort.level : `${effort.level}: ${effort.reason}`
}

export function newTaskLine(state: NewTaskState): string {
  switch (state.stage) {
    case 'offered':
      return state.effort === undefined ? `New task: ${state.task}` : `New task: ${state.task}. Proposed effort ${proposal(state.effort)}`
    case 'handoff':
      return 'session-kit is writing the handoff before the clear.'
    case 'clearing':
      return 'Clearing the context, then sending your prompt again.'
  }
}

/** The cold-cache row's words: when the kit runs the handoff and the compaction on its own. */
export function coldText(at: number): string {
  return `handoff and compact at ${clockTime(new Date(at))}, before it goes cold`
}
