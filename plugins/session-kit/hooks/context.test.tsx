import { expect, test } from 'claude-code/testing'

import type { On, SessionUsage } from 'claude-code'

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

test('the model is warned from 250,000 tokens, every 25k, firmer at twice and at three times that, and afresh after a compaction', async ($, on) => {
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
  expect((await contextAt(51))[0]).toMatch(/End this turn at the next green commit/)
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
    expect((await ui.find({ type: 'Text', text: /Context 300,000/ }))?.text).toMatch(/Context 300,000 tokens \(30% of 1,000,000\)/)
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
    const row = await ui.find({ type: 'Text', text: /Context|engine/ })
    await ui.unmount()

    return row?.text
  }

  expect(await bandAt(30)).toMatch(/Context 300,000/)
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  await ui.press({ key: 'context-dismiss' })
  await ui.unmount()
  expect(await bandAt(30)).toBe('engine')
  expect(await bandAt(32)).toBe('engine')
  expect(await bandAt(33)).toMatch(/Context 330,000/)
  const again = await $.ui.mount({ ...BAND, surface: 'terminal' })
  await again.press({ key: 'context-dismiss' })
  await again.unmount()
  expect(await bandAt(34)).toBe('engine')
  // Compacted: the figure fell below where it was dismissed.
  expect(await bandAt(5)).toBe('engine')
  expect(await bandAt(26)).toMatch(/Context 260,000/)
})
