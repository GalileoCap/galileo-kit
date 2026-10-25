import { expect, mock, test } from 'claude-code/testing'

import type { On, SessionUsage, TurnCompleteInput } from 'claude-code'

import { backstop, journalPath } from './context'

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
    // new_task is registered beside it, proven in new_task.test.tsx.
    if (e.name === 'clear_point') {
      asked.push(`register ${e.name}`)
    }

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

test('off: no tool is registered and the warning names none', { options: { chain: false } }, async ($, on) => {
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(asked).toEqual([])

  const ran = await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(ran.context?.[0]).toMatch(/safe to compact/)
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
  // The engine's output schema for a registered tool takes a string: an object is refused at the call.
  expect(typeof signalled.result).toBe('string')
  expect(signalled.result).toMatch(/End this turn/)
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
    // The chain's line draws above the band beneath it, never in its place.
    expect((await ui.find({ type: 'Text', text: /engine/ }))?.text).toBe('engine')
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
  expect(answered.deny).toMatch(/next_step/)
  expect(answered.result).toBeUndefined()
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
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
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

test('a third chain since the person\'s last prompt is refused, a prompt that is not theirs changes nothing, and their next prompt lets one run again', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: 'build it', wait: false, origin: { kind: 'composer' } })
  const continues = () => asked.filter((a) => a.startsWith('prompt Continue')).length
  const chain = async (id: string) => {
    const signalled = await $.tool.call({ tool: TOOL, next_step: 'session', note: 'go on' })
    await $.turn.complete(turn(`${id}-1`))
    await clock.settle()
    await $.turn.complete(turn(`${id}-2`))
    await clock.settle()

    return signalled
  }

  expect((await chain('a')).deny).toBeUndefined()
  expect((await chain('b')).deny).toBeUndefined()
  expect(continues()).toBe(2)

  const third = await $.tool.call({ tool: TOOL, next_step: 'session', note: 'go on' })
  expect(third.deny).toMatch(/nobody at the prompt/)
  expect(third.result).toBeUndefined()
  await $.turn.complete(turn('c'))
  await clock.settle()
  expect(continues()).toBe(2)

  await $.prompt.submit({ text: 'a task finished', wait: false, origin: { kind: 'task-notification' } })
  expect((await $.tool.call({ tool: TOOL, next_step: 'session', note: 'go on' })).deny).toMatch(/nobody at the prompt/)

  await $.prompt.submit({ text: 'carry on', wait: false, origin: { kind: 'composer' } })
  expect((await chain('d')).deny).toBeUndefined()
  expect(continues()).toBe(3)
})

test('where no person is at the prompt, the chain compacts through /compact and then continues', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: null, isInteractive: false })

  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'run the checks' })
  await $.turn.complete(turn('t1'))
  await clock.settle()
  await $.turn.complete(turn('t2'))
  await clock.settle()

  // The engine's own compaction is refused in an SDK session, so it is never asked.
  expect(asked.filter((a) => a.startsWith('compact '))).toEqual([])
  expect(asked.slice(1, 3)).toEqual(['command session-kit:handoff', 'command compact'])
  expect(asked[3]).toMatch(/^prompt .*run the checks/)
})

test('every stage of a chain leaves a line in the session\'s chain file, which a host that draws no log line still has', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  const files: Record<string, string> = {}
  mock.env(on, { TMPDIR: '/var/tmp/t' })
  on('session.id', () => ({ value: 'sess-1' }))
  on('fs.read', (_, e) => {
    const text = files[e.path]
    if (text === undefined) {
      throw new Error(`ENOENT: ${e.path}`)
    }

    return { value: text }
  })
  on('fs.write', (_, e) => {
    files[e.path] = e.text

    return { value: undefined }
  })
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'next' })
  await $.turn.complete(turn('t1'))
  await clock.settle()
  await $.turn.complete(turn('t2'))
  await clock.settle()
  await clock.advance(1000)

  const journal = files[journalPath('/var/tmp/t', 'sess-1')] ?? ''
  const stages = [/writing the handoff/, /handoff command returned/, /compacting/, /sending the continue prompt/]
  let from = 0
  for (const stage of stages) {
    const at = journal.slice(from).search(stage)
    expect(at).toBeGreaterThanOrEqual(0)
    from += at + 1
  }
})

test('the backstop tells the engine\'s own compaction what a handoff keeps', async () => {
  const added = backstop(undefined)
  expect(added).toMatch(/CLAUDE\.local\.md/)
  expect(added).toMatch(/next step/)
  expect(added).toMatch(/decision/)
  expect(backstop('keep the plan')).toMatch(/^keep the plan\n/)
  expect(backstop('keep the plan')).toMatch(/next step/)
})

test('dismissing the band stops the chain where it stands, before the handoff or during the compaction', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on, { refuseCompactions: 1 })
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const dismiss = async () => {
    const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
    await ui.press({ key: 'chain-dismiss' })
    expect(await ui.find({ type: 'Text', text: /clear point|handoff|compact/i })).toBeUndefined()
    await ui.unmount()
  }

  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'next' })
  await dismiss()
  await $.turn.complete(turn('t1'))
  await clock.settle()
  expect(asked).toEqual(['register clear_point'])

  // The first compaction is refused, and the band is dismissed before the second try.
  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'next' })
  await $.turn.complete(turn('t2'))
  await clock.settle()
  await $.turn.complete(turn('t3'))
  await clock.settle()
  await dismiss()
  await clock.advance(2000)
  expect(asked).toEqual(['register clear_point', 'command session-kit:handoff'])
})
