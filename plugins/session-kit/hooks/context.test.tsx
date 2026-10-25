import { expect, test } from 'claude-code/testing'

import type { SessionUsage } from 'claude-code'

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

test('the model is warned past half the window, every 25k tokens, and afresh after a compaction', async ($, on) => {
  let percent = 40
  on('session.usage', () => ({ value: usage(percent) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('tool.call', () => ({ result: {} }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const contextAt = async (p: number) => {
    percent = p
    const ran = await $.tool.call({ tool: 'Bash', command: 'ls' })

    return ran.context ?? []
  }

  expect(await contextAt(40)).toEqual([])
  expect((await contextAt(52))[0]).toMatch(/^Context at 520,000 tokens \(52% of 1,000,000\)\. Aim for a safe point/)
  expect(await contextAt(53)).toEqual([])
  expect((await contextAt(55))[0]).toMatch(/55%/)
  expect((await contextAt(66))[0]).toMatch(/End this turn at the next green commit/)
  expect((await contextAt(81))[0]).toMatch(/Stop starting anything new/)
  // Compacted: the figure fell below the last warning.
  expect(await contextAt(30)).toEqual([])
  expect((await contextAt(51))[0]).toMatch(/51%/)
})

test('the threshold and the step come from the options', { options: { threshold: 60, step: 100000 } }, async ($, on) => {
  let percent = 52
  on('session.usage', () => ({ value: usage(percent) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('tool.call', () => ({ result: {} }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const contextAt = async (p: number) => {
    percent = p
    const ran = await $.tool.call({ tool: 'Bash', command: 'ls' })

    return ran.context ?? []
  }

  expect(await contextAt(52)).toEqual([])
  expect((await contextAt(61))[0]).toMatch(/61%/)
  expect(await contextAt(70)).toEqual([])
  expect((await contextAt(72))[0]).toMatch(/72%/)
})

test('a denied call carries no warning', async ($, on) => {
  on('session.usage', () => ({ value: usage(90) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('tool.call', () => ({ deny: 'no' }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const ran = await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(ran.context).toBeUndefined()
})

test('the band shows the figure past the threshold and leaves the engine below it', async ($, on) => {
  let percent = 40
  on('session.usage', () => ({ value: usage(percent) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('tool.call', () => ({ result: {} }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  for (const surface of ['terminal', 'desktop'] as const) {
    percent = 40
    await $.tool.call({ tool: 'Bash', command: 'ls' })
    let ui = await $.ui.mount({ ...BAND, surface })
    expect((await ui.find({ type: 'Text', text: /engine/ }))?.text).toBe('engine')
    await ui.unmount()

    percent = 70
    await $.tool.call({ tool: 'Bash', command: 'ls' })
    ui = await $.ui.mount({ ...BAND, surface })
    expect((await ui.find({ type: 'Text', text: /Context 70%/ }))?.text).toMatch(/Context 70% of 1,000,000/)
    await ui.unmount()
  }
})
