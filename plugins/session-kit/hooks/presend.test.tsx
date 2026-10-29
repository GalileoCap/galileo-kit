import { expect, test } from 'claude-code/testing'

import type { EngineInterface, On, RenderSurface } from 'claude-code'

import { world } from './world.test-helper'

const BAND = {
  plugin: 'session-kit',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 4 }, view: {} },
} as const

const START = { cwd: '/proj', surface: 'desktop', isInteractive: true } as const
const FOUND = '{"findings": ["\\"Do M27 before\\": M27 has no name"], "rewrite": "Do: M27 (the timeline) before installing"}'

type Engine = { reached: string[]; asked: string[]; box: { text: string }; answer: string | Error; surfaces: RenderSurface[] }

// The engine beneath: what reached the model, what Haiku was asked, the prompt box, and where the session is drawn.
function engine(on: On): Engine {
  const made: Engine = { reached: [], asked: [], box: { text: '' }, answer: '{"findings": []}', surfaces: ['desktop'] }
  on('prompt.submit', (_, e) => {
    made.reached.push(e.text)

    return { text: e.text, context: e.context }
  })
  on('model.complete', (_, e) => {
    made.asked.push(e.prompt)
    if (made.answer instanceof Error) {
      throw made.answer
    }

    return { value: { isAnswered: true, text: made.answer, usage: { inputTokens: 0, outputTokens: 0, costUsd: 0 } } }
  })
  on('prompt.fill', (_, e) => {
    made.box.text = e.text

    return { isFilled: true, text: e.text, cursor: e.text.length }
  })
  on('prompt.read', () => ({ value: { text: made.box.text, cursor: made.box.text.length } }))
  on('session.surfaces', () => ({ value: made.surfaces }))
  on('session.messages', () => ({ value: [] }))
  on('process.run', () => ({ value: { exitCode: 1, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('ui.log', () => ({ value: undefined }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })

  return made
}

function typed(text: string) {
  return { text, wait: false, origin: { kind: 'composer' as const } }
}

async function band($: EngineInterface) {
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  const texts = (await ui.findAll({ type: 'Text' })).map((t) => t.text).join(' | ')
  const buttons = (await ui.findAll({ type: 'Button' })).map((b) => b.key ?? '')
  await ui.unmount()

  return { texts, buttons }
}

async function press($: EngineInterface, key: string) {
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  await ui.press({ key })
  await ui.unmount()
}

test('a ?? message Haiku finds something in is held and put back in the box, and Send as is sends the box once, unchecked', async ($, on) => {
  const w = world(on)
  const e = engine(on)
  e.answer = FOUND
  await $.session.start(START)

  const sent = await $.prompt.submit(typed('?? Do M27 before installing'))
  await w.clock.settle()
  expect(sent.drop).toMatch(/Held by the pre-send check/)
  expect(e.reached).toEqual([])
  expect(e.asked[0]).toMatch(/<<<\nDo M27 before installing\n>>>/)
  expect(e.box.text).toBe('Do M27 before installing')
  const drawn = await band($)
  expect(drawn.texts).toMatch(/M27 has no name/)
  expect(drawn.buttons).toEqual(expect.arrayContaining(['presend-send', 'presend-rewrite', 'presend-dismiss']))

  e.box.text = 'Do M27 before installing, as planned'
  await press($, 'presend-send')
  await w.clock.settle()
  expect(e.asked.length).toBe(1)
  expect(e.reached).toEqual(['Do M27 before installing, as planned'])
  expect(e.box.text).toBe('')
  expect((await band($)).texts).not.toMatch(/M27 has no name/)
})

test('Use the rewrite fills the box with it, and the next message goes through unchecked', async ($, on) => {
  const w = world(on)
  const e = engine(on)
  e.answer = FOUND
  await $.session.start(START)

  await $.prompt.submit(typed('?? Do M27 before installing'))
  await w.clock.settle()
  await press($, 'presend-rewrite')
  await w.clock.settle()
  expect(e.box.text).toBe('Do: M27 (the timeline) before installing')
  await $.prompt.submit(typed('?? Do: M27 (the timeline) before installing'))
  expect(e.asked.length).toBe(1)
  expect(e.reached).toEqual(['Do-1: M27 (the timeline) before installing'])
})

test('four bullets are checked and three are not; nothing found, a failing Haiku and a surface with no band let the message through', async ($, on) => {
  world(on)
  const e = engine(on)
  await $.session.start(START)

  await $.prompt.submit(typed('- one\n- two\n- three'))
  expect(e.asked.length).toBe(0)
  await $.prompt.submit(typed('- one\n- two\n- three\n- four'))
  expect(e.asked.length).toBe(1)
  expect(e.reached.length).toBe(2)

  e.answer = new Error('rate limited')
  await $.prompt.submit(typed('?? Do it'))
  expect(e.reached.at(-1)).toBe('Do it')

  e.answer = FOUND
  e.surfaces = ['desktop', 'mobile']
  await $.prompt.submit(typed('?? Do M27'))
  expect(e.asked.length).toBe(2)
  expect(e.reached.at(-1)).toBe('Do M27')
})
