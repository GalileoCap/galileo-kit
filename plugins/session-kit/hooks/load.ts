// The owner's working window (A92, A95, superseded by A96): for the owner
// alone, nothing here reaches a model (C5). With
// ~/.claude/session-kit/load/settings.json in place, the owner's prompt
// outside its window, or into one session more than the active ones allow,
// goes on at once, and the band asks why in a line. A work prompt's window
// is the work hours, and a personal project's is the waking slot. The
// question is logged in holds.jsonl as asked, and the answer or the ✕ adds
// a line of its own. A reason given for the window opens a pass that spares
// every session the question for passMinutes. A prompt from the phone, which
// draws no band, is logged with no reason. Each prompt is also matched
// against the owner's focus list, ~/.claude/session-kit/focus.md, by its
// folder (A94): logged in prompts-<monday>.jsonl, and named on the status
// line with the week's share on focus. It rides on context.tsx's
// prompt.submit hook. Anything that fails lets the prompt through (C1).

import { atom, read, update } from 'claude-code'
import type { EngineInterface, PromptOrigin } from 'claude-code'

import type { LoadAsk, LoadFocus, LoadPass } from '../types'
import { clip } from './lines'
import type { SessionRecord } from './registry'

type Kind = 'work' | 'personal'

type Span = { days: readonly string[]; hours: readonly string[] }

/** How many other sessions may be active before a prompt into one more is held, and the minutes after its turn a session stays active. */
export type SessionLimit = { max: number; idleMinutes: number }

export type LoadSettings = { timeZone: string; work: Span; personal: Span & { folders: readonly string[] }; passMinutes: number; sessions?: SessionLimit }

const loadAsk = atom({ plugin: 'session-kit', key: 'loadAsk' } as const, null)
const loadPass = atom({ plugin: 'session-kit', key: 'loadPass' } as const, null)
const loadFocus = atom({ plugin: 'session-kit', key: 'loadFocus' } as const, null)

const MINUTE_MS = 60000
// One wait's bound, `$.process.run`'s own; the wait starts again while the question is up.
const WAIT_MS = 10 * MINUTE_MS
const DISMISSED = '\u0000dismissed'
const WAIT_SCRIPT = 'while [ ! -s "$0" ]; do sleep 1; done'
// The registry's records, one a line; read through the shell, as a listing call would put the calls line past its cut.
const LIST_SCRIPT = 'for f in "$0"/*.json; do [ -f "$f" ] && cat "$f" && echo; done'
const LIST_MS = 5000
// A record whose beat is older than this is a session that quit.
const ALIVE_MS = 2 * MINUTE_MS
// A day runs from 04:00, as the week review counts it.
const DAY_CUTOFF_MS = 4 * 60 * MINUTE_MS
const WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

/** One must-have of the focus list: its name, and the folders it covers as the owner wrote them. */
export type FocusItem = { name: string; folders: string[] }

/** The focus list: the Monday its heading names, null without one, and its must-haves. */
export type FocusList = { week: string | null; items: FocusItem[] }

/** The weekday and the minute of the day at `ms`, in the owner's time zone. */
export function localTime(ms: number, timeZone: string): { day: string; minute: number } {
  const parts = new Intl.DateTimeFormat('en-US', { timeZone, weekday: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(ms)
  const part = (type: string) => parts.find((p) => p.type === type)?.value ?? ''

  return { day: part('weekday').toLowerCase(), minute: Number(part('hour')) * 60 + Number(part('minute')) }
}

function minuteOf(hhmm: string): number {
  const [h, m] = hhmm.split(':')

  return Number(h) * 60 + Number(m)
}

function within(span: Span, at: { day: string; minute: number }): boolean {
  return (
    span.days.includes(at.day) &&
    span.hours.some((range) => {
      const [from, to] = range.split('-')

      return at.minute >= minuteOf(from ?? '') && at.minute < minuteOf(to ?? '')
    })
  )
}

/** Whether `cwd` is `folder` or inside it, a leading `~` read as `home`. */
export function isUnder(folder: string, cwd: string, home: string): boolean {
  const root = folder.replace(/^~(?=\/|$)/, home).replace(/\/$/, '')

  return cwd === root || cwd.startsWith(`${root}/`)
}

export function kindOf(settings: LoadSettings, cwd: string, home: string): Kind {
  return settings.personal.folders.some((folder) => isUnder(folder, cwd, home)) ? 'personal' : 'work'
}

/** The Monday of the week `ms` falls in, as YYYY-MM-DD in the owner's time zone. */
export function mondayOf(ms: number, timeZone: string): string {
  const parts = new Intl.DateTimeFormat('en-US', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' }).formatToParts(ms - DAY_CUTOFF_MS)
  const part = (type: string) => parts.find((p) => p.type === type)?.value ?? ''
  const back = WEEKDAYS.indexOf(part('weekday').toLowerCase())

  return new Date(Date.UTC(Number(part('year')), Number(part('month')) - 1, Number(part('day')) - back)).toISOString().slice(0, 10)
}

/**
 * Reads the focus list: a heading `# Week of YYYY-MM-DD`, then a `- ` line
 * per must-have, its name and its folders, each starting with `~/` or `/`.
 */
export function parseFocus(text: string): FocusList {
  const heading = /^#\s*Week of (\d{4}-\d{2}-\d{2})\s*$/m.exec(text)
  const items = text
    .split('\n')
    .filter((line) => /^\s*[-*]\s+/.test(line))
    .map((line) => {
      const words = line
        .replace(/^\s*[-*]\s+/, '')
        .split(/\s+/)
        .map((word) => word.replace(/`/g, '').replace(/[,;]$/, ''))
      const isPath = (word: string) => /^(~|~?\/)/.test(word)

      return {
        name: words
          .filter((word) => !isPath(word))
          .join(' ')
          .replace(/[\s:,\-–—]+$/, ''),
        folders: words.filter(isPath),
      }
    })

  return { week: heading?.[1] ?? null, items }
}

/** The name of the first must-have whose folders hold `cwd`; null when none does. */
export function focusOf(list: FocusList, cwd: string, home: string): string | null {
  return list.items.find((item) => item.folders.some((folder) => isUnder(folder, cwd, home)))?.name ?? null
}

/** Whether a session counts toward the owner's load: alive, and working or within `idleMinutes` of its last turn's end. */
export function isActive(record: SessionRecord, now: number, limit: SessionLimit): boolean {
  const ended = record.turnEnded ?? 0 // A record from before turnEnded was written counts only while it works.

  return record.state !== 'ended' && now - record.beat < ALIVE_MS && (record.state === 'working' || (ended > 0 && now - ended < limit.idleMinutes * MINUTE_MS))
}

/** The other active sessions, sidechats left out, when they reach the limit and this one is neither among them nor a sidechat; empty otherwise. */
export function crowdOf(records: readonly SessionRecord[], session: string, now: number, limit: SessionLimit): SessionRecord[] {
  if (records.some((r) => r.id === session && r.side === true)) {
    return []
  }
  const active = records.filter((r) => r.side !== true && isActive(r, now, limit))
  const others = active.filter((r) => r.id !== session)

  return others.length >= limit.max && others.length === active.length ? others : []
}

/** The focus tag as the status line names it. */
export function focusLabel(focus: LoadFocus): string {
  if (focus.tag === 'stale') {
    return "the focus list is not this week's"
  }
  const share = `${Math.round((100 * focus.on) / Math.max(focus.total, 1))}% on this week`

  return focus.tag === 'on' ? `on focus: ${focus.name}, ${share}` : `off focus, ${share}`
}

export function inWindow(settings: LoadSettings, kind: Kind, ms: number): boolean {
  return within(kind === 'personal' ? settings.personal : settings.work, localTime(ms, settings.timeZone))
}

/** The hours and minutes of `ms` in the owner's time zone, as the status line names the pass's end. */
export function clockLabel(ms: number, timeZone: string): string {
  const { minute } = localTime(ms, timeZone)

  return `${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`
}

/**
 * Asks the owner why, for a prompt outside its window or into one session past
 * the active ones. The prompt has already gone on: the band's row waits for a
 * reason or the ✕, and the session never waits on it.
 */
export async function askWhy($: EngineInterface, text: string, origin: PromptOrigin | undefined): Promise<void> {
  // Local closures keep the validator's calls line under its cut (docs/PLAN.md, Deferred).
  const readText = async (path: string) => ((await $.fs.exists(path)) ? await $.fs.read(path) : '')
  const readJson = async (path: string): Promise<unknown> => {
    const text = await readText(path)

    return text === '' ? null : JSON.parse(text)
  }
  const append = async (path: string, line: object) => {
    const text = `${await readText(path)}${JSON.stringify(line)}\n`
    await $.fs.write(path, text)

    return text
  }
  // The other active sessions when this prompt would be one more past the limit.
  const crowd = async (limit: SessionLimit, timeZone: string, home: string, line: { at: number; session: string }): Promise<string[]> => {
    const listed = await $.process.run(['/bin/sh', '-c', LIST_SCRIPT, `${home}/.claude/session-kit/sessions`], { timeoutMs: LIST_MS })
    const records = listed.stdout.split('\n').flatMap((l): SessionRecord[] => {
      try {
        return l.trim() === '' ? [] : [JSON.parse(l) as SessionRecord] // Written by registry.ts alone.
      } catch {
        return [] // A record cut by a write in flight: the next prompt reads it whole.
      }
    })

    return crowdOf(records, line.session, line.at, limit).map((r) => {
      const where = r.cwd.replace(home, '~')

      return r.state === 'working' ? `${where}: working` : `${where}: waiting since ${clockLabel(r.turnEnded, timeZone)}`
    })
  }
  // Puts the question on the band for a prompt outside its window or into one session more than the limit.
  const gate = async (settings: LoadSettings, home: string, line: { at: number; session: string; cwd: string; kind: Kind }) => {
    if ((await read($, loadAsk)) !== null) {
      return
    }
    let window = !inWindow(settings, line.kind, line.at)
    const pass = window ? ((await readJson(`${dir}/pass.json`)) as LoadPass | null) : null // Written by this module alone.
    if (pass !== null && pass.until > line.at) {
      await update($, loadPass, () => ({ until: pass.until, label: clockLabel(pass.until, settings.timeZone) }))
      window = false
    }
    const others = settings.sessions === undefined ? [] : await crowd(settings.sessions, settings.timeZone, home, line)
    if (!window && others.length === 0) {
      return
    }
    const entry = { ...line, held: [...(window ? ['window'] : []), ...(others.length > 0 ? ['sessions'] : [])], active: others.length }
    if (origin?.kind === 'bridge') {
      await append(`${dir}/holds.jsonl`, { ...entry, reason: null, via: 'phone', outcome: 'sent' })

      return
    }
    await append(`${dir}/holds.jsonl`, { ...entry, reason: null, via: 'band', outcome: 'asked' })
    const file = `${dir}/reason-${line.session}`
    await $.fs.write(file, '')
    const ask: LoadAsk = { kind: line.kind, window, crowd: others, preview: clip(text, 80), file }
    await update($, loadAsk, () => ask)
    void settle(settings, file, entry, window)
  }
  // Waits, apart from the session, for the band's answer, then logs it; a reason for the window opens the pass.
  const settle = async (settings: LoadSettings, file: string, entry: { session: string }, window: boolean) => {
    try {
      let answer = ''
      while (answer === '') {
        await $.process.run(['/bin/sh', '-c', WAIT_SCRIPT, file], { timeoutMs: WAIT_MS }).catch(() => null) // The wait's bound: the loop waits again.
        answer = (await readText(file)).trim()
      }
      const reason = answer === DISMISSED ? null : answer
      await append(`${dir}/holds.jsonl`, { ...entry, reason, via: 'band', outcome: reason === null ? 'dismissed' : 'answered' })
      if (reason !== null && window) {
        const until = (await $.clock.now()) + settings.passMinutes * MINUTE_MS
        await $.fs.write(`${dir}/pass.json`, JSON.stringify({ until, session: entry.session, reason }))
        await update($, loadPass, () => ({ until, label: clockLabel(until, settings.timeZone) }))
      }
    } catch {
      // Nothing to do: the answer goes unlogged and the next prompt outside the window asks again (C1).
    }
  }
  // Counts a prompt that goes on against this week's focus list, which is copied beside the log for the week's review.
  const tally = async (home: string, timeZone: string, line: { at: number; session: string; cwd: string }) => {
    const listText = await readText(`${home}/.claude/session-kit/focus.md`)
    if (listText === '') {
      await update($, loadFocus, () => null)

      return
    }
    const monday = mondayOf(line.at, timeZone)
    const list = parseFocus(listText)
    if (list.week !== monday) {
      const stale: LoadFocus = { tag: 'stale', name: null, on: 0, total: 0 }
      await update($, loadFocus, () => stale)

      return
    }
    const copy = `${dir}/focus-${monday}.md`
    if ((await readText(copy)) !== listText) {
      await $.fs.write(copy, listText)
    }
    const name = focusOf(list, line.cwd, home)
    const log = await append(`${dir}/prompts-${monday}.jsonl`, { ...line, focus: name })
    const total = log.split('\n').filter((l) => l !== '').length
    const off = log.split('"focus":null').length - 1
    const focus: LoadFocus = { tag: name === null ? 'off' : 'on', name, on: total - off, total }
    await update($, loadFocus, () => focus)
  }
  let dir = ''
  try {
    const home = await $.env.get('HOME')
    if (home === undefined) {
      return
    }
    dir = `${home}/.claude/session-kit/load`
    const settings = (await readJson(`${dir}/settings.json`)) as LoadSettings | null // The owner's own file, read as the kit wrote its shape.
    if (settings === null) {
      return
    }
    const line = { at: await $.clock.now(), session: await $.session.id(), cwd: await $.session.cwd() }
    await gate(settings, home, { ...line, kind: kindOf(settings, line.cwd, home) })
    await tally(home, settings.timeZone, line)
  } catch {
    // Nothing to do: the prompt has gone on, and the next one asks again (C1).
  }
}

/** The band's answer: a reason, or null for the ✕; the wait under way logs it. */
export function answerAsk($: EngineInterface, ask: LoadAsk, reason: string | null): void {
  const why = reason?.trim() ?? null
  if (why !== '') {
    void $.fs.write(ask.file, why ?? DISMISSED)
    void update($, loadAsk, () => null)
  }
}
