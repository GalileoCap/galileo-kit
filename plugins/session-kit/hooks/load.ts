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
// The hold rides on context.tsx's prompt.submit hook, the kit's outermost.
// Anything that fails lets the prompt through (C1).

import { atom, update } from 'claude-code'
import type { EngineInterface, PromptOrigin } from 'claude-code'

import type { LoadHeld, LoadPass } from '../types'
import { clip } from './lines'
import { withHeld } from './presend'

type Kind = 'work' | 'personal'

type Span = { days: readonly string[]; hours: readonly string[] }

export type LoadSettings = { timeZone: string; work: Span; personal: Span & { folders: readonly string[] }; passMinutes: number }

const loadHeld = atom({ plugin: 'session-kit', key: 'loadHeld' } as const, null)
const loadPass = atom({ plugin: 'session-kit', key: 'loadPass' } as const, null)

const MINUTE_MS = 60000
const WAIT_MS = 10 * MINUTE_MS
const RETURNED = '\u0000returned'
const WAIT_SCRIPT = 'while [ ! -s "$0" ]; do sleep 0.3; done'

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

export function kindOf(settings: LoadSettings, cwd: string, home: string): Kind {
  const under = (folder: string) => {
    const root = folder.replace(/^~(?=\/|$)/, home).replace(/\/$/, '')

    return cwd === root || cwd.startsWith(`${root}/`)
  }

  return settings.personal.folders.some(under) ? 'personal' : 'work'
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
  const appendLog = async (line: object) => {
    const path = `${dir}/holds.jsonl`
    await $.fs.write(path, `${await readText(path)}${JSON.stringify(line)}\n`)
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
    const now = await $.clock.now()
    const cwd = await $.session.cwd()
    const kind = kindOf(settings, cwd, home)
    if (inWindow(settings, kind, now)) {
      return null
    }
    const pass = (await readJson(`${dir}/pass.json`)) as LoadPass | null // Written by this module alone.
    if (pass !== null && pass.until > now) {
      await update($, loadPass, () => ({ until: pass.until, label: clockLabel(pass.until, settings.timeZone) }))

      return null
    }
    const session = await $.session.id()
    const line = { at: now, session, cwd, kind }
    if (origin?.kind === 'bridge') {
      await appendLog({ ...line, reason: null, via: 'phone', outcome: 'sent' })

      return null
    }
    const file = `${dir}/reason-${session}`
    await $.fs.write(file, '')
    const held: LoadHeld = { kind, preview: clip(text, 80), file }
    await update($, loadHeld, () => held)
    const reason = await awaitReason(file)
    await update($, loadHeld, () => null)
    if (reason === null) {
      await appendLog({ ...line, reason: null, via: 'band', outcome: 'returned' })
      const box = (await $.prompt.read()).text
      await $.prompt.fill({ text: withHeld(box, text), mode: 'replace' })

      return 'Held outside your window: the prompt is back in the box.'
    }
    const until = (await $.clock.now()) + settings.passMinutes * MINUTE_MS
    await appendLog({ ...line, reason, via: 'band', outcome: 'sent' })
    await $.fs.write(`${dir}/pass.json`, JSON.stringify({ until, session, reason }))
    await update($, loadPass, () => ({ until, label: clockLabel(until, settings.timeZone) }))

    return null
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
