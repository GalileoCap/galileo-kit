import { expect, mock, test } from 'claude-code/testing'

import type { On, SessionUsage, TurnCompleteInput } from 'claude-code'

import { backstop } from './context'

const WINDOW = 1_000_000
const TOOL = 'mcp__session-kit__clear_point'

function usage(percent: number): SessionUsage {
  const tokens = Math.round((WINDOW * percent) / 100)

  return { startedAt: 0, context: { tokens, window: WINDOW, percent }, rateLimits: [] }
}

function turn(turnId: string, reason: TurnCompleteInput['reason'] = 'answer'): TurnCompleteInput {
  const ended = { answer: 'done', durationMs: 10, isAborted: reason === 'aborted', turnId }

  return reason === 'refusal'
    ? { ...ended, reason, refusal: { category: null, explanation: null } }
    : { ...ended, reason }
}

const BAND = {
  plugin: 'session-kit',
  component: 'AbovePrompt',
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 5,
    bodyColumns: 80,
    scroll: { offset: 0, bodyRows: 4 },
    view: {},
  },
} as const

// The engine beneath the plugin, recording what the chain asked of it.
function engine(on: On, { percent = 55, refuseCompactions = 0 } = {}) {
  const asked: string[] = []
  let refusals = refuseCompactions
  on('session.usage', () => ({ value: usage(percent) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('tool.register', (_, e) => {
    asked.push(`register ${e.name}`)

    return { value: { tool: `mcp__session-kit__${e.name}` } }
  })
  on('command.run', (_, e) => {
    asked.push(`command ${e.command}`)

    return { text: 'handoff written' }
  })
  on('session.compact', (_, e) => {
    if (refusals > 0) {
      refusals -= 1
      throw new Error('a turn is running')
    }
    asked.push(`compact ${e.instructions ?? ''}`)

    return { messages: [{ role: 'user' as const, text: 'the summary', toolUses: [] }] }
  })
  on('prompt.submit', (_, e) => {
    asked.push(`prompt ${e.text}`)

    return { text: e.text }
  })
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('tool.call', () => ({ result: {} }))

  return asked
}

test('off by default: no tool is registered and the warning names none', async ($, on) => {
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(asked).toEqual([])

  const ran = await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(ran.context?.[0]).toMatch(/tell the user it is safe to compact/)
  expect(ran.context?.[0]).not.toMatch(/clear_point/)
})

test('on: the model signals, the mod writes the handoff, compacts and continues', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(asked).toEqual(['register clear_point'])

  const warned = await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(warned.context?.[0]).toMatch(/clear_point/)

  const signalled = await $.tool.call({ tool: TOOL, next_step: 'session', note: 'run the checks' })
  expect(signalled.deny).toBeUndefined()
  expect(JSON.stringify(signalled.result)).toMatch(/End this turn/)
  // The warning does not ride on the signal itself.
  expect(signalled.context).toBeUndefined()

  // Nothing runs while the turn goes on.
  expect(asked.length).toBe(1)

  await $.turn.complete(turn('t1'))
  await clock.settle()
  expect(asked[1]).toBe('command session-kit:handoff')
  expect(asked.length).toBe(2)

  await $.turn.complete(turn('t2'))
  await clock.settle()
  expect(asked[2]).toMatch(/^compact .*CLAUDE\.local\.md/)
  expect(asked[3]).toMatch(/^prompt .*CLAUDE\.local\.md.*run the checks/)
  expect(asked.length).toBe(4)

  // The continue turn ends: the chain is over, nothing more runs.
  await $.turn.complete(turn('t3'))
  await clock.settle()
  expect(asked.length).toBe(4)
})

test('when the next step is the owner\'s, the chain stops after the compaction and the band says so', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await $.tool.call({ tool: TOOL, next_step: 'owner', note: 'approve O14 to O16' })
  await $.turn.complete(turn('t1'))
  await clock.settle()
  await $.turn.complete(turn('t2'))
  await clock.settle()
  expect(asked[2]).toMatch(/^compact /)
  expect(asked.length).toBe(3)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    const row = await ui.find({ type: 'Text', text: /next step/ })
    expect(row?.text).toMatch(/yours.*approve O14 to O16/)
    await ui.unmount()
  }

  // The owner's next turn clears the notice.
  await $.turn.complete(turn('t3'))
  await clock.settle()
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /next step/ })).toBeUndefined()
  await ui.unmount()
})

test('an interrupted turn cancels the chain', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'next' })
  await $.turn.complete(turn('t1', 'aborted'))
  await clock.settle()
  await $.turn.complete(turn('t2'))
  await clock.settle()
  expect(asked).toEqual(['register clear_point'])
})

test('a signal without a next step is refused and starts nothing', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const answered = await $.tool.call({ tool: TOOL, note: 'next' })
  expect(answered.deny).toBeUndefined()
  expect(JSON.stringify(answered.result)).toMatch(/next_step/)
  await $.turn.complete(turn('t1'))
  await clock.settle()
  expect(asked).toEqual(['register clear_point'])
})

test('a compaction refused while the turn still runs is tried again', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on, { refuseCompactions: 2 })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'next' })
  await $.turn.complete(turn('t1'))
  await clock.settle()
  await $.turn.complete(turn('t2'))
  await clock.settle()
  expect(asked.length).toBe(2)
  await clock.advance(2000)
  expect(asked[2]).toMatch(/^compact /)
  expect(asked[3]).toMatch(/^prompt /)
})

test('the band shows each stage of the chain', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const bandSays = async (pattern: RegExp) => {
    const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
    const row = await ui.find({ type: 'Text', text: pattern })
    await ui.unmount()

    return row?.text
  }

  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'next' })
  expect(await bandSays(/clear point/i)).toMatch(/when this turn ends/)
  await $.turn.complete(turn('t1'))
  await clock.settle()
  expect(await bandSays(/handoff/i)).toMatch(/writing the handoff/)
})

test('the backstop tells the engine\'s own compaction what a handoff keeps', async () => {
  const added = backstop(undefined)
  expect(added).toMatch(/CLAUDE\.local\.md/)
  expect(added).toMatch(/next step/)
  expect(added).toMatch(/decision/)
  expect(backstop('keep the plan')).toMatch(/^keep the plan\n/)
  expect(backstop('keep the plan')).toMatch(/next step/)
})
