import { expect, test } from 'claude-code/testing'

import type { EngineInterface, On, SessionMeasureInput, SessionRateLimit, SessionUsage, TurnCompleteInput } from 'claude-code'

const WINDOW = 1_000_000
const RESETS_SOON = '2026-10-25T14:30:00Z'
const RESETS_IN_DAYS = '2026-10-28T09:00:00Z'

function usage(percent: number): SessionUsage {
  const tokens = Math.round((WINDOW * percent) / 100)

  return { startedAt: 0, context: { tokens, window: WINDOW, percent }, rateLimits: [] }
}

function turn(turnId: string): TurnCompleteInput {
  return { answer: 'done', durationMs: 10, isAborted: false, turnId, reason: 'answer' }
}

function measured(percent: number, windows: SessionRateLimit[]): SessionMeasureInput {
  return { ...usage(percent), rateLimits: windows, changed: ['rateLimits'] }
}

function fiveHour(percentUsed: number): SessionRateLimit {
  return { kind: 'five_hour', percentUsed, resetsAt: RESETS_SOON }
}

const BAND = {
  plugin: 'session-kit',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 4 }, view: {} },
} as const

// The engine beneath the plugin, with the context at `state.percent` and a line of its own in the band.
function engine(on: On, state: { percent: number }) {
  on('session.usage', () => ({ value: usage(state.percent) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('session.measure', (_, e) => ({ changed: e.changed }))
  on('tool.register', (_, e) => ({ value: { tool: `mcp__session-kit__${e.name}` } }))
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('tool.call', () => ({ result: {} }))
  // The checkout checks run git at each turn end and look for the handoff: no repository and no file here.
  on('process.run', () => ({ value: { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('fs.exists', () => ({ value: false }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
}

async function bandLine($: EngineInterface, pattern: RegExp, surface: 'terminal' | 'desktop' = 'desktop'): Promise<string | undefined> {
  const ui = await $.ui.mount({ ...BAND, surface })
  const row = await ui.find({ type: 'Text', text: pattern })
  await ui.unmount()

  return row?.text
}

async function press($: EngineInterface, key: string): Promise<void> {
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  await ui.press({ key })
  await ui.unmount()
}

test('a usage window draws a band row from 95%, naming the window and when it resets, above the band beneath, and below 95% draws nothing', async ($, on) => {
  engine(on, { percent: 10 })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await $.session.measure(measured(10, [fiveHour(94)]))
  expect(await bandLine($, /usage window/)).toBeUndefined()
  expect(await bandLine($, /engine/)).toBe('engine')

  await $.session.measure(measured(10, [fiveHour(95.5)]))
  for (const surface of ['terminal', 'desktop'] as const) {
    expect(await bandLine($, /usage window/, surface)).toMatch(/^The 5-hour usage window is at 95\.5% and resets at \d\d:\d\d\./)
    expect(await bandLine($, /engine/, surface)).toBe('engine')
  }
})

test('dismissed at 95, the row stays away until the window resets below where it was dismissed', async ($, on) => {
  engine(on, { percent: 10 })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await $.session.measure(measured(10, [fiveHour(96)]))
  expect(await bandLine($, /usage window/)).toMatch(/96%/)
  await press($, 'limit-dismiss-five_hour')
  expect(await bandLine($, /usage window/)).toBeUndefined()
  await $.session.measure(measured(10, [fiveHour(99)]))
  expect(await bandLine($, /usage window/)).toBeUndefined()
  // The window reset.
  await $.session.measure(measured(10, [fiveHour(3)]))
  expect(await bandLine($, /usage window/)).toBeUndefined()
  await $.session.measure(measured(10, [fiveHour(97)]))
  expect(await bandLine($, /usage window/)).toMatch(/97%/)
})

test('two windows draw two rows, each dismissed on its own, and a 7-day window names the day it resets', async ($, on) => {
  engine(on, { percent: 10 })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await $.session.measure(measured(10, [fiveHour(96), { kind: 'seven_day', percentUsed: 97, resetsAt: RESETS_IN_DAYS }]))
  expect(await bandLine($, /5-hour/)).toMatch(/96%/)
  expect(await bandLine($, /7-day/)).toMatch(/^The 7-day usage window is at 97% and resets on \d{1,2} [A-Z][a-z]{2} at \d\d:\d\d\./)

  await press($, 'limit-dismiss-five_hour')
  expect(await bandLine($, /5-hour/)).toBeUndefined()
  expect(await bandLine($, /7-day/)).toMatch(/97%/)
})

test('the figure row says how much the context grew in the last turn, read at the turn\'s end, and nothing after a compaction or before a second turn', { options: { chain: false } }, async ($, on) => {
  const state = { percent: 30 }
  engine(on, state)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const turnEnds = async (id: string, percent: number) => {
    state.percent = percent
    await $.turn.start({ text: 'go on', turnId: id })
    await $.turn.complete(turn(id))

    return { value: await bandLine($, /\/ 1M/), growth: await bandLine($, /last turn/) }
  }

  // The first turn's end gives the figure with no tool call read, and no growth yet.
  expect(await turnEnds('t1', 30)).toEqual({ value: '300k / 1M  30%', growth: undefined })
  expect(await turnEnds('t2', 34)).toEqual({ value: '340k / 1M  34%', growth: '+40k last turn' })
  // Compacted during the turn: the context shrank, so nothing grew.
  expect(await turnEnds('t3', 26)).toEqual({ value: '260k / 1M  26%', growth: undefined })
  expect((await turnEnds('t4', 29)).growth).toBe('+30k last turn')
})
