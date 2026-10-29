import { expect, test } from 'claude-code/testing'

import type { EngineInterface, On, SessionUsage } from 'claude-code'

const WINDOW = 1_000_000

function usage(percent: number): SessionUsage {
  const tokens = Math.round((WINDOW * percent) / 100)

  return { startedAt: 0, context: { tokens, window: WINDOW, percent }, rateLimits: [] }
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

function engine(on: On, state: { percent: number }, deny = false) {
  on('session.usage', () => ({ value: usage(state.percent) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('tool.call', () => (deny ? { deny: 'no' } : { result: {} }))
}

test('the model is warned from 250,000 tokens, every 25k, firmer from 300,000 and told to stop from 400,000, each tier at once, and afresh after a compaction', async ($, on) => {
  const state = { percent: 10 }
  engine(on, state)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const contextAt = async (p: number) => {
    state.percent = p
    const ran = await $.tool.call({ tool: 'Bash', command: 'ls' })

    return ran.context ?? []
  }

  expect(await contextAt(20)).toEqual([])
  expect((await contextAt(25))[0]).toMatch(/^Context at 250,000 tokens \(25% of 1,000,000\)\. Aim for a safe point/)
  expect(await contextAt(26)).toEqual([])
  expect((await contextAt(28))[0]).toMatch(/280,000 tokens/)
  // Inside the 25k step after the warning at 280,000, a tier that rises still warns.
  expect(await contextAt(29)).toEqual([])
  expect((await contextAt(30))[0]).toMatch(/300,000 tokens.*End this turn at the next green commit/)
  expect(await contextAt(31)).toEqual([])
  expect((await contextAt(33))[0]).toMatch(/End this turn at the next green commit/)
  expect((await contextAt(39))[0]).toMatch(/End this turn at the next green commit/)
  expect((await contextAt(40))[0]).toMatch(/400,000 tokens.*Stop starting anything new/)
  expect(await contextAt(41)).toEqual([])
  expect((await contextAt(76))[0]).toMatch(/Stop starting anything new/)
  // Compacted: the figure fell below the last warning.
  expect(await contextAt(5)).toEqual([])
  expect((await contextAt(26))[0]).toMatch(/260,000 tokens/)
})

test('a percent of the window is the alternative, with the token count off', { options: { thresholdTokens: 0, threshold: 60, step: 100000 } }, async ($, on) => {
  const state = { percent: 52 }
  engine(on, state)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const contextAt = async (p: number) => {
    state.percent = p
    const ran = await $.tool.call({ tool: 'Bash', command: 'ls' })

    return ran.context ?? []
  }

  expect(await contextAt(52)).toEqual([])
  expect((await contextAt(61))[0]).toMatch(/61%/)
  expect(await contextAt(70)).toEqual([])
  expect((await contextAt(72))[0]).toMatch(/72%/)
})

test('with both set, the one reached first warns', { options: { thresholdTokens: 300000, threshold: 20 } }, async ($, on) => {
  const state = { percent: 19 }
  engine(on, state)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  expect((await $.tool.call({ tool: 'Bash', command: 'ls' })).context).toBeUndefined()
  state.percent = 25
  expect((await $.tool.call({ tool: 'Bash', command: 'ls' })).context?.[0]).toMatch(/250,000 tokens/)
})

test('a denied call carries no warning', async ($, on) => {
  engine(on, { percent: 90 }, true)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const ran = await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(ran.context).toBeUndefined()
})

test('the band shows the count past the threshold, above the bands beneath it, and leaves the engine alone below it', async ($, on) => {
  const state = { percent: 10 }
  engine(on, state)
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  for (const surface of ['terminal', 'desktop'] as const) {
    state.percent = 10
    await $.tool.call({ tool: 'Bash', command: 'ls' })
    let ui = await $.ui.mount({ ...BAND, surface })
    expect((await ui.find({ type: 'Text', text: /engine/ }))?.text).toBe('engine')
    await ui.unmount()

    state.percent = 30
    await $.tool.call({ tool: 'Bash', command: 'ls' })
    ui = await $.ui.mount({ ...BAND, surface })
    expect((await ui.find({ type: 'Text', text: /300k \/ 1M/ }))?.text).toBe('300k / 1M  30%')
    // The band beneath, another plugin's or the engine's, is drawn under the kit's and never hidden by it.
    expect((await ui.find({ type: 'Text', text: /engine/ }))?.text).toBe('engine')
    await ui.unmount()
  }
})

test('a dismissed band stays away until the figure moves a step on, and comes back after a compaction', async ($, on) => {
  const state = { percent: 30 }
  engine(on, state)
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const bandAt = async (p: number) => {
    state.percent = p
    await $.tool.call({ tool: 'Bash', command: 'ls' })
    const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
    const row = await ui.find({ type: 'Text', text: /\/ 1M|engine/ })
    await ui.unmount()

    return row?.text
  }

  expect(await bandAt(30)).toMatch(/^300k \/ 1M  30%/)
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  await ui.press({ key: 'context-dismiss' })
  await ui.unmount()
  expect(await bandAt(30)).toBe('engine')
  expect(await bandAt(32)).toBe('engine')
  expect(await bandAt(33)).toMatch(/^330k \/ 1M/)
  const again = await $.ui.mount({ ...BAND, surface: 'terminal' })
  await again.press({ key: 'context-dismiss' })
  await again.unmount()
  expect(await bandAt(34)).toBe('engine')
  // Compacted: the figure fell below where it was dismissed.
  expect(await bandAt(5)).toBe('engine')
  // Past the trigger and below the firmer tier, the figure is the status line's alone.
  expect(await bandAt(29)).toBe('engine')
  expect(await bandAt(30)).toMatch(/^300k \/ 1M/)
})

// The engine beneath a step of reads: its own figure at 100,000 tokens, which
// moves only when it measures again, each Read answering with `sizes[file]`
// characters, and each step answered over 100,000 tokens with 1,000 written.
function reads(on: On, sizes: Record<string, number>) {
  on('session.usage', () => ({ value: usage(10) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('tool.register', (_, e) => ({ value: { tool: `mcp__session-kit__${e.name}` } }))
  on('tool.call', (_, e) => ({ result: {}, text: 'x'.repeat(e.tool === 'Read' ? sizes[e.file_path] ?? 0 : 0) }))
  on('turn.step', async function* (_, e) {
    const usage = { input_tokens: 1000, cache_read_input_tokens: 99_000, cache_creation_input_tokens: 0, output_tokens: 1000, model: 'claude-fable-5-1' }
    yield { kind: 'stop', stopReason: 'tool_use', usage }

    return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'tool_use', usage }
  })
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
}

async function warned($: EngineInterface, file: string): Promise<string | undefined> {
  return (await $.tool.call({ tool: 'Read', file_path: file })).context?.[0]
}

test('between the engine\'s measurements the warning fires on the last request\'s context, its output and the tool output landed since, at 3.5 characters a token', async ($, on) => {
  reads(on, { '/a': 350_000, '/b': 350_000, '/c': 35_000, '/d': 70_000 })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const step = $.turn.step({ turnId: 't1', index: 0, model: 'claude-fable-5-1', messageCount: 3 })
  for await (const _ of step) {
    // Read to its end, as the engine does.
  }

  // One step of parallel reads, with no request between them: the engine's figure stays at 100,000.
  expect(await warned($, '/a')).toBeUndefined()
  expect(await warned($, '/b')).toMatch(/^Context at 301,000 tokens \(30% of 1,000,000\)\. End this turn at the next green commit/)
  expect(await warned($, '/c')).toBeUndefined()
  expect(await warned($, '/d')).toMatch(/^Context at 331,000 tokens \(33% of 1,000,000\)/)
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  expect((await ui.find({ type: 'Text', text: /\/ 1M/ }))?.text).toMatch(/^331k \/ 1M  33%/)
  await ui.unmount()
})
