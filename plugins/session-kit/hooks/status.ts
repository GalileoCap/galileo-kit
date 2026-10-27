// The kit's status line under the prompt: the context figure with the time
// since the person's last own message, each usage window and the cold-cache
// timer, kept on every surface so the numbers are in
// view before the band has anything to say. It is written only when its text
// changes, and never when the `statusLine` option is off.

import { atom, read } from 'claude-code'
import type { EngineInterface, SessionRateLimit, Timer } from 'claude-code'

import { statusText } from './lines'

const NO_WINDOWS: SessionRateLimit[] = []

const coldTimerAt = atom({ plugin: 'session-kit', key: 'coldTimerAt' } as const, 0)
const figure = atom({ plugin: 'session-kit', key: 'contextFigure' } as const, null)
const rateLimits = atom({ plugin: 'session-kit', key: 'rateLimits' } as const, NO_WINDOWS)
const lastPromptAt = atom({ plugin: 'session-kit', key: 'lastPromptAt' } as const, 0)
const turnGrowth = atom({ plugin: 'session-kit', key: 'turnGrowth' } as const, 0)

const MINUTE_MS = 60000

let isOn = true
// The tick that redraws the line when the minute of the time since the person's last message turns.
let tick: Timer | null = null
// What the line says now; a symbol before the first write, so a first `undefined` still clears.
const UNSET = Symbol('unset')
let shown: string | undefined | typeof UNSET = UNSET

export function holdStatus(on: boolean): void {
  isOn = on
  if (!on) {
    tick?.cancel()
    tick = null
  }
  shown = UNSET
}

export async function refreshStatus($: EngineInterface): Promise<void> {
  if (!isOn) {
    return
  }
  const saidAt = await read($, lastPromptAt)
  const since = saidAt === 0 ? null : (await $.clock.now()) - saidAt
  if (since !== null && tick === null) {
    tick = $.clock.after(MINUTE_MS - (since % MINUTE_MS), () => {
      tick = null
      void refreshStatus($)
    })
  }
  const text = statusText(await read($, figure), await read($, turnGrowth), since, await read($, rateLimits), await read($, coldTimerAt))
  if (text === shown) {
    return
  }
  shown = text
  $.ui.status(text)
}
