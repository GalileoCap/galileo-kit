// The owner's working window (A92), for the owner alone: nothing here
// reaches a model (C5). With ~/.claude/session-kit/load/settings.json in
// place, the owner's prompt outside its window waits while the band asks for
// a one-line reason. A work prompt's window is the work hours, and a personal
// project's is the waking slot, so the sleeping hours hold every prompt. The
// reason sends the prompt on as it came, is logged in holds.jsonl with the
// session and its kind, and opens a pass that lets every session's prompts
// through for passMinutes. The wait is a process that ends when the reason
// file holds text, since a hook's own time is bounded and a `$` call in
// flight is not (the probe of 2026-10-29). An interrupt, the ✕, or ten
// minutes with no reason puts the prompt back in the box instead. A prompt
// from the phone, which draws no band, goes on and is logged with no reason.
// Each prompt that goes on is also matched against the owner's focus list,
// ~/.claude/session-kit/focus.md, by its folder (A94): logged in
// prompts-<monday>.jsonl, and named on the status line with the week's share
// on focus. The hold rides on context.tsx's prompt.submit hook, the kit's outermost.
// Anything that fails lets the prompt through (C1).

import { atom, update } from 'claude-code'
import type { EngineInterface, PromptOrigin } from 'claude-code'

import type { LoadFocus, LoadHeld, LoadPass } from '../types'
import { clip } from './lines'
import { withHeld } from './presend'

type Kind = 'work' | 'personal'

type Span = { days: readonly string[]; hours: readonly string[] }

export type LoadSettings = { timeZone: string; work: Span; personal: Span & { folders: readonly string[] }; passMinutes: number }

const loadHeld = atom({ plugin: 'session-kit', key: 'loadHeld' } as const, null)
const loadPass = atom({ plugin: 'session-kit', key: 'loadPass' } as const, null)
const loadFocus = atom({ plugin: 'session-kit', key: 'loadFocus' } as const, null)

const MINUTE_MS = 60000
const WAIT_MS = 10 * MINUTE_MS
const RETURNED = '\u0000returned'
const WAIT_SCRIPT = 'while [ ! -s "$0" ]; do sleep 0.3; done'
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
 * Holds the owner's prompt outside its window until a reason comes: null lets
 * it on, and a text is the drop's reason, the prompt then back in the box.
 */
export async function hold($: EngineInterface, text: string, origin: PromptOrigin | undefined, signal: AbortSignal): Promise<string | null> {
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
  // Waits for the reason; null when the prompt went back to the box instead.
  const awaitReason = async (file: string): Promise<string | null> => {
    const giveBack = () => void $.fs.write(file, RETURNED)
    signal.addEventListener('abort', giveBack)
    try {
      await $.process.run(['/bin/sh', '-c', WAIT_SCRIPT, file], { timeoutMs: WAIT_MS })
      const reason = (await $.fs.read(file)).trim()

      return reason === RETURNED ? null : reason
    } catch {
      return null
    } finally {
      signal.removeEventListener('abort', giveBack)
    }
  }
  // Holds the prompt outside its window; null lets it on.
  const gate = async (settings: LoadSettings, line: { at: number; session: string; cwd: string; kind: Kind }): Promise<string | null> => {
    if (inWindow(settings, line.kind, line.at)) {
      return null
    }
    const pass = (await readJson(`${dir}/pass.json`)) as LoadPass | null // Written by this module alone.
    if (pass !== null && pass.until > line.at) {
      await update($, loadPass, () => ({ until: pass.until, label: clockLabel(pass.until, settings.timeZone) }))

      return null
    }
    if (origin?.kind === 'bridge') {
      await append(`${dir}/holds.jsonl`, { ...line, reason: null, via: 'phone', outcome: 'sent' })

      return null
    }
    const file = `${dir}/reason-${line.session}`
    await $.fs.write(file, '')
    const held: LoadHeld = { kind: line.kind, preview: clip(text, 80), file }
    await update($, loadHeld, () => held)
    const reason = await awaitReason(file)
    await update($, loadHeld, () => null)
    if (reason === null) {
      await append(`${dir}/holds.jsonl`, { ...line, reason: null, via: 'band', outcome: 'returned' })
      const box = (await $.prompt.read()).text
      await $.prompt.fill({ text: withHeld(box, text), mode: 'replace' })

      return 'Held outside your window: the prompt is back in the box.'
    }
    const until = (await $.clock.now()) + settings.passMinutes * MINUTE_MS
    await append(`${dir}/holds.jsonl`, { ...line, reason, via: 'band', outcome: 'sent' })
    await $.fs.write(`${dir}/pass.json`, JSON.stringify({ until, session: line.session, reason }))
    await update($, loadPass, () => ({ until, label: clockLabel(until, settings.timeZone) }))

    return null
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
      return null
    }
    dir = `${home}/.claude/session-kit/load`
    const settings = (await readJson(`${dir}/settings.json`)) as LoadSettings | null // The owner's own file, read as the kit wrote its shape.
    if (settings === null) {
      return null
    }
    const line = { at: await $.clock.now(), session: await $.session.id(), cwd: await $.session.cwd() }
    const returned = await gate(settings, { ...line, kind: kindOf(settings, line.cwd, home) })
    if (returned === null) {
      await tally(home, settings.timeZone, line)
    }

    return returned
  } catch {
    return null
  }
}

/** The band's reason field: a reason sends the held prompt on. */
export function giveReason($: EngineInterface, held: LoadHeld, reason: string): void {
  if (reason.trim() !== '') {
    void $.fs.write(held.file, reason.trim())
  }
}

/** The band's ✕: the held prompt goes back to the box. */
export function returnHeld($: EngineInterface, held: LoadHeld): void {
  void $.fs.write(held.file, RETURNED)
}
