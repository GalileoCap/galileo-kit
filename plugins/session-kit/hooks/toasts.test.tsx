import { expect, mock, test } from 'claude-code/testing'

import type { EngineInterface, MockClock, On, RenderSurface, SessionMeasureInput, SessionRateLimit, SessionUsage, TurnCompleteInput } from 'claude-code'

const WINDOW = 1_000_000
const MINUTE = 60_000
const CLEAR_POINT = 'mcp__session-kit__clear_point'
const NEW_TASK = 'mcp__session-kit__new_task'

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
  return { kind: 'five_hour', percentUsed, resetsAt: '2026-10-25T14:30:00Z' }
}

const BAND = {
  plugin: 'session-kit',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 4 }, view: {} },
} as const

type Host = {
  percent: number
  surfaces: RenderSurface[]
  // True for an engine that cannot say where it draws.
  cannotSay: boolean
}

// The engine beneath the plugin: the context at `host.percent`, drawing on `host.surfaces`, recording every toast.
function engine(on: On, host: Host) {
  const toasts: string[] = []
  on('session.usage', () => ({ value: usage(host.percent) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('session.surfaces', () => {
    if (host.cannotSay) {
      throw new Error('no surfaces here')
    }

    return { value: host.surfaces }
  })
  on('session.measure', (_, e) => ({ changed: e.changed }))
  on('session.turns', () => ({ value: 2 }))
  on('session.messages', () => ({ value: [{ role: 'assistant' as const, text: 'the last task', toolUses: [] }] }))
  on('tool.register', (_, e) => ({ value: { tool: `mcp__session-kit__${e.name}` } }))
  on('command.run', () => ({ text: 'ran' }))
  on('session.compact', () => ({ messages: [{ role: 'user' as const, text: 'the summary', toolUses: [] }] }))
  on('prompt.submit', (_, e) => ({ text: e.text }))
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('tool.call', () => ({ result: {} }))
  on('process.run', () => ({ value: { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('fs.exists', () => ({ value: false }))
  on('ui.toast', (_, e) => {
    toasts.push(e.text)

    return { value: undefined }
  })
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })

  return toasts
}

async function dismissOffer($: EngineInterface): Promise<void> {
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  await ui.press({ key: 'new-task-dismiss' })
  await ui.unmount()
}

// Every moment the band would show: a warning, a window at 80, a new task, a clear point signalled and run.
async function moments($: EngineInterface, clock: MockClock, host: Host, percent: number, window: number, id: string): Promise<void> {
  host.percent = percent
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  await $.session.measure(measured(percent, [fiveHour(window)]))
  await $.tool.call({ tool: NEW_TASK, task: 'rewrite the README' })
  await dismissOffer($)
  await $.tool.call({ tool: CLEAR_POINT, next_step: 'owner', note: 'approve the plan' })
  await $.turn.complete(turn(`${id}-signal`))
  await clock.settle()
  await $.turn.complete(turn(`${id}-handoff`))
  await clock.settle()
}

test('with a phone attached, the moments that matter go out as a toast, and with a terminal and the desktop alone none does', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const host: Host = { percent: 10, surfaces: ['terminal', 'desktop'], cannotSay: false }
  const toasts = engine(on, host)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: 'build it', wait: false, origin: { kind: 'composer' } })

  await moments($, clock, host, 25, 82, 'a')
  expect(toasts).toEqual([])

  host.surfaces.push('mobile')
  await $.prompt.submit({ text: 'go on', wait: false, origin: { kind: 'composer' } })
  await moments($, clock, host, 28, 95, 'b')
  expect(toasts).toEqual([
    'Context 280,000 tokens (28% of 1,000,000): find a clear point, commit, write the handoff, call clear_point.',
    expect.stringMatching(/^The 5-hour usage window is at 95% and resets at \d\d:\d\d\./),
    expect.stringMatching(/^New task: rewrite the README\. From a terminal or the desktop, the band offers/),
    'Clear point: the handoff, the compaction and the continue run when this turn ends.',
    'Compacted. The next step is yours: approve the plan',
  ])

  // A window that moves within a tier says nothing again; the cold-cache timer firing does.
  toasts.length = 0
  await $.session.measure(measured(28, [fiveHour(97)]))
  expect(toasts).toEqual([])
  await $.turn.start({ text: 'more', turnId: 'c' })
  await $.turn.complete(turn('c'))
  await clock.settle()
  await clock.advance(55 * MINUTE)
  expect(toasts).toEqual([expect.stringMatching(/cache goes cold/)])
})

test('VS Code draws no band either, and an engine that cannot say where it draws gets no toast', { options: { chain: true } }, async ($, on) => {
  const host: Host = { percent: 10, surfaces: ['vscode'], cannotSay: false }
  const toasts = engine(on, host)
  await $.session.start({ cwd: '/', surface: 'vscode', isInteractive: true })

  host.percent = 25
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(toasts).toEqual([expect.stringMatching(/^Context 250,000 tokens/)])

  toasts.length = 0
  host.cannotSay = true
  host.percent = 28
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(toasts).toEqual([])
})
