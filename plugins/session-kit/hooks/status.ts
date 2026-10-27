// The kit's status line under the prompt: the context figure, each usage
// window and the cold-cache timer, kept on every surface so the numbers are in
// view before the band has anything to say. It is written only when its text
// changes, and never when the `statusLine` option is off.

import { atom, read } from 'claude-code'
import type { EngineInterface, SessionRateLimit } from 'claude-code'

import { statusText } from './lines'

const NO_WINDOWS: SessionRateLimit[] = []

const coldTimerAt = atom({ plugin: 'session-kit', key: 'coldTimerAt' } as const, 0)
const figure = atom({ plugin: 'session-kit', key: 'contextFigure' } as const, null)
const rateLimits = atom({ plugin: 'session-kit', key: 'rateLimits' } as const, NO_WINDOWS)
const turnGrowth = atom({ plugin: 'session-kit', key: 'turnGrowth' } as const, 0)

let isOn = true
// What the line says now; a symbol before the first write, so a first `undefined` still clears.
const UNSET = Symbol('unset')
let shown: string | undefined | typeof UNSET = UNSET

export function holdStatus(on: boolean): void {
  isOn = on
  shown = UNSET
}

export async function refreshStatus($: EngineInterface): Promise<void> {
  if (!isOn) {
    return
  }
  const text = statusText(await read($, figure), await read($, turnGrowth), await read($, rateLimits), await read($, coldTimerAt))
  if (text === shown) {
    return
  }
  shown = text
  $.ui.status(text)
}
