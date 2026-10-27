import { expect, mock, test } from 'claude-code/testing'

import type { EngineInterface, MockClock, On, SessionUsage, TurnCompleteInput } from 'claude-code'

const WINDOW = 1_000_000
const MINUTE = 60_000

function usage(percent: number): SessionUsage {
  const tokens = Math.round((WINDOW * percent) / 100)

  return { startedAt: 0, context: { tokens, window: WINDOW, percent }, rateLimits: [] }
}

function turn(turnId: string): TurnCompleteInput {
  return { answer: 'done', durationMs: 10, isAborted: false, turnId, reason: 'answer' }
}

const BAND = {
  plugin: 'session-kit',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 4 }, view: {} },
} as const

// The engine beneath the plugin, recording what the chain asked of it, with the context at `state.percent`.
function engine(on: On, state: { percent: number }) {
  const asked: string[] = []
  on('session.usage', () => ({ value: usage(state.percent) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('tool.register', (_, e) => ({ value: { tool: `mcp__session-kit__${e.name}` } }))
  on('command.run', (_, e) => {
    asked.push(`command ${e.command}`)

    return { text: 'ran' }
  })
  on('session.compact', () => {
    asked.push('compact')

    return { messages: [{ role: 'user' as const, text: 'the summary', toolUses: [] }] }
  })
  on('prompt.submit', (_, e) => {
    asked.push(`prompt ${e.text}`)

    return { text: e.text }
  })
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('tool.call', () => ({ result: {} }))
  // The checkout checks run git at each turn end: no repository here.
  on('process.run', () => ({ value: { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })

  return asked
}

// A turn of the person's: it starts, reads the context once, and ends.
// A subagent's result, its cache writes split by lifetime.
function subagent(lifetime: '5m' | '1h') {
  return {
    result: {
      agentId: 'a1',
      content: [],
      totalToolUseCount: 0,
      totalDurationMs: 1,
      totalTokens: 100,
      usage: {
        input_tokens: 1,
        output_tokens: 1,
        cache_creation_input_tokens: 100,
        cache_read_input_tokens: 0,
        server_tool_use: null,
        service_tier: null,
        cache_creation: { ephemeral_1h_input_tokens: lifetime === '1h' ? 100 : 0, ephemeral_5m_input_tokens: lifetime === '5m' ? 100 : 0 },
      },
    },
  }
}

async function delegatingTurn($: EngineInterface, clock: MockClock, id: string): Promise<void> {
  await $.turn.start({ text: 'delegate', turnId: id })
  await $.tool.call({ tool: 'Agent', prompt: 'look around' })
  await $.turn.complete(turn(id))
  await clock.settle()
}

async function personsTurn($: EngineInterface, clock: MockClock, id: string): Promise<void> {
  await $.turn.start({ text: 'go on', turnId: id })
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  await $.turn.complete(turn(id))
  await clock.settle()
}

test('left alone past the floor, the kit writes the handoff and compacts five minutes before the cache goes cold, and stops there', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on, { percent: 30 })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await personsTurn($, clock, 't1')
  await clock.advance(54 * MINUTE)
  expect(asked).toEqual([])
  await clock.advance(1 * MINUTE)
  expect(asked).toEqual(['command session-kit:handoff'])

  // The handoff turn ends: the compaction follows, and no continue prompt.
  await $.turn.start({ text: '', turnId: 't-handoff' })
  await $.turn.complete(turn('t-handoff'))
  await clock.settle()
  expect(asked).toEqual(['command session-kit:handoff', 'command compact'])
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  expect((await ui.find({ type: 'Text', text: /next step/ }))?.text).toMatch(/yours/)
  await ui.unmount()

  // The handoff turn's own end arms nothing: hours on, nothing more ran.
  await clock.advance(180 * MINUTE)
  expect(asked).toEqual(['command session-kit:handoff', 'command compact'])
})

test('a turn that starts before the lead disarms the timer, and the next turn end arms it afresh from that moment', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on, { percent: 30 })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await personsTurn($, clock, 't1')
  await clock.advance(30 * MINUTE)
  await $.turn.start({ text: 'more', turnId: 't2' })
  await clock.advance(60 * MINUTE)
  expect(asked).toEqual([])

  await $.tool.call({ tool: 'Bash', command: 'ls' })
  await $.turn.complete(turn('t2'))
  await clock.settle()
  await clock.advance(54 * MINUTE)
  expect(asked).toEqual([])
  await clock.advance(1 * MINUTE)
  expect(asked).toEqual(['command session-kit:handoff'])
})

test('below the floor nothing arms, and the floor and the lead are options', { options: { chain: true, cacheFloorTokens: 100_000, cacheLeadMinutes: 20 } }, async ($, on) => {
  const clock = mock.clock(on)
  const state = { percent: 5 }
  const asked = engine(on, state)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await personsTurn($, clock, 't1')
  await clock.advance(180 * MINUTE)
  expect(asked).toEqual([])

  state.percent = 15
  await personsTurn($, clock, 't2')
  await clock.advance(39 * MINUTE)
  expect(asked).toEqual([])
  await clock.advance(1 * MINUTE)
  expect(asked).toEqual(['command session-kit:handoff'])
})

test('by default the floor is the warning\'s own trigger', { options: { chain: true, thresholdTokens: 400_000 } }, async ($, on) => {
  const clock = mock.clock(on)
  const state = { percent: 30 }
  const asked = engine(on, state)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await personsTurn($, clock, 't1')
  await clock.advance(180 * MINUTE)
  expect(asked).toEqual([])

  state.percent = 40
  await personsTurn($, clock, 't2')
  await clock.advance(55 * MINUTE)
  expect(asked).toEqual(['command session-kit:handoff'])
})

test('a 5-minute cache arms no timer, until a subagent\'s result says the cache is an hour\'s', { options: { chain: true, cacheMinutes: 5 } }, async ($, on) => {
  const clock = mock.clock(on)
  on('tool.call', { tool: 'Agent' }, () => subagent('1h'))
  const asked = engine(on, { percent: 30 })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await personsTurn($, clock, 't1')
  await clock.advance(180 * MINUTE)
  expect(asked).toEqual([])

  await delegatingTurn($, clock, 't2')
  await clock.advance(55 * MINUTE)
  expect(asked).toEqual(['command session-kit:handoff'])
})

test('with the lifetime option at 0 the timer is off, whatever the engine says', { options: { chain: true, cacheMinutes: 0 } }, async ($, on) => {
  const clock = mock.clock(on)
  on('tool.call', { tool: 'Agent' }, () => subagent('1h'))
  const asked = engine(on, { percent: 30 })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await delegatingTurn($, clock, 't1')
  await clock.advance(180 * MINUTE)
  expect(asked).toEqual([])
})

test('a subagent\'s result that wrote a 5-minute cache replaces the hour the option gives', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  on('tool.call', { tool: 'Agent' }, () => subagent('5m'))
  const asked = engine(on, { percent: 30 })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await delegatingTurn($, clock, 't1')
  await clock.advance(180 * MINUTE)
  expect(asked).toEqual([])
})

test('the band names when the chain runs, above the band beneath it, and Dismiss stops it until the next turn ends', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on, { percent: 30 })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await personsTurn($, clock, 't1')
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    const row = await ui.find({ type: 'Text', text: /before it goes cold/ })
    expect(row?.text).toMatch(/handoff and compact at \d\d:\d\d/)
    // The context figure's line is there too, and the band beneath.
    expect((await ui.find({ type: 'Text', text: /300k \/ 1M/ }))?.text).toBe('300k / 1M  30%')
    expect((await ui.find({ type: 'Text', text: /engine/ }))?.text).toBe('engine')
    await ui.unmount()
  }

  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  await ui.press({ key: 'cold-dismiss' })
  expect(await ui.find({ type: 'Text', text: /before it goes cold/ })).toBeUndefined()
  await ui.unmount()
  await clock.advance(180 * MINUTE)
  expect(asked).toEqual([])

  await personsTurn($, clock, 't2')
  await clock.advance(55 * MINUTE)
  expect(asked).toEqual(['command session-kit:handoff'])
})
