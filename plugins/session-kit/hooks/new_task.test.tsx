import { expect, mock, test } from 'claude-code/testing'

import type { EngineInterface, On, SessionUsage, TurnCompleteInput } from 'claude-code'

const TOOL = 'mcp__session-kit__new_task'
const PROMPT = 'Now rewrite the README install section for the new name'

function usage(percent: number): SessionUsage {
  const tokens = Math.round((1_000_000 * percent) / 100)

  return { startedAt: 0, context: { tokens, window: 1_000_000, percent }, rateLimits: [] }
}

function turn(turnId: string): TurnCompleteInput {
  return { answer: 'done', durationMs: 10, isAborted: false, turnId, reason: 'answer' }
}

const BAND = {
  plugin: 'session-kit',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 4 }, view: {} },
} as const

// The engine beneath the plugin, recording what it asked. `holdsTask`: the
// context already holds a prompt of the person's and an answer of the model's.
function engine(on: On, { holdsTask = true } = {}) {
  const asked: string[] = []
  on('session.usage', () => ({ value: usage(40) }))
  on('session.turns', () => ({ value: holdsTask ? 2 : 0 }))
  on('session.messages', () => ({ value: holdsTask ? [{ role: 'assistant' as const, text: 'the last task', toolUses: [] }] : [] }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('tool.register', (_, e) => {
    asked.push(`register ${e.name}`)

    return { value: { tool: `mcp__session-kit__${e.name}` } }
  })
  on('command.run', (_, e) => {
    asked.push(`command ${e.command}${e.args === '' ? '' : ` ${e.args}`}`)

    return { text: 'ran' }
  })
  on('prompt.submit', (_, e) => {
    const asUser = e.origin?.kind === 'plugin' && e.origin.asUser === true
    asked.push(`prompt${asUser ? ' as user' : ''}: ${e.text}`)

    return { text: e.text }
  })
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('tool.call', () => ({ result: {} }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })

  return asked
}

test('with the chain on, new_task is registered beside clear_point', { options: { chain: true } }, async ($, on) => {
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(asked).toEqual(['register clear_point', 'register new_task'])
})

test('the signal tells the model to stop, and the band offers the handoff and the clear, or to keep going', { options: { chain: true } }, async ($, on) => {
  engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: PROMPT, wait: false, origin: { kind: 'composer' } })

  const signalled = await $.tool.call({ tool: TOOL, task: 'rewrite the README install section' })
  expect(signalled.deny).toBeUndefined()
  expect(typeof signalled.result).toBe('string')
  expect(signalled.result).toMatch(/End this turn/)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    expect((await ui.find({ type: 'Text', text: /New task/ }))?.text).toMatch(/rewrite the README install section/)
    expect(await ui.find({ type: 'Button', text: /Handoff and clear/ })).toBeDefined()
    expect(await ui.find({ type: 'Button', text: /Keep going here/ })).toBeDefined()
    // The offer draws above the band beneath it, never in its place.
    expect((await ui.find({ type: 'Text', text: /engine/ }))?.text).toBe('engine')
    await ui.unmount()
  }
})

test('keep going here sends the person\'s own prompt again and clears the offer', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: PROMPT, wait: false, origin: { kind: 'composer' } })
  await $.tool.call({ tool: TOOL, task: 'rewrite the README' })
  asked.length = 0

  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  await ui.press({ key: 'new-task-here' })
  await clock.settle()
  expect(asked).toEqual([`prompt as user: ${PROMPT}`])
  expect(await ui.find({ type: 'Text', text: /New task/ })).toBeUndefined()
  await ui.unmount()
})

test('a prompt that is not the person\'s own words is never the one sent again, and one from the phone is', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: PROMPT, wait: false, origin: { kind: 'composer' } })
  const resent = async () => {
    asked.length = 0
    const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
    await ui.press({ key: 'new-task-here' })
    await clock.settle()
    await ui.unmount()

    return asked
  }

  const others = [
    { kind: 'task-notification' },
    { kind: 'scheduled-trigger' },
    { kind: 'peer' },
    { kind: 'peer-send-message' },
    { kind: 'projects-relay' },
    { kind: 'coordinator' },
    { kind: 'observer' },
    { kind: 'observer-activity' },
    { kind: 'auto-continuation' },
    { kind: 'plugin', name: 'other' },
  ] as const
  for (const origin of others) {
    await $.prompt.submit({ text: `not theirs: ${origin.kind}`, wait: false, origin })
  }
  await $.tool.call({ tool: TOOL, task: 'rewrite the README' })
  expect(await resent()).toEqual([`prompt as user: ${PROMPT}`])

  await $.prompt.submit({ text: 'from the phone', wait: false, origin: { kind: 'bridge' } })
  await $.tool.call({ tool: TOOL, task: 'rewrite the README' })
  expect(await resent()).toEqual(['prompt as user: from the phone'])
})

test('handoff and clear writes the handoff, clears, and sends the person\'s own prompt again', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: PROMPT, wait: false, origin: { kind: 'composer' } })
  await $.tool.call({ tool: TOOL, task: 'rewrite the README' })
  asked.length = 0

  let ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  await ui.press({ key: 'new-task-clear' })
  await clock.settle()
  expect(asked).toEqual(['command session-kit:handoff'])
  expect((await ui.find({ type: 'Text', text: /handoff/ }))?.text).toMatch(/writing the handoff/)
  await ui.unmount()

  await $.turn.complete(turn('t-handoff'))
  await clock.settle()
  expect(asked).toEqual(['command session-kit:handoff', 'command clear', `prompt as user: ${PROMPT}`])

  ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  // The offer's own lines; the figure's line stays, since the turn end past the threshold draws it.
  expect(await ui.find({ type: 'Text', text: /^(New task|session-kit is|Clearing)/ })).toBeUndefined()
  await ui.unmount()
})

test('the prompt is sent again after a clear that starts the session\'s state over', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  // The host after a clear: the session's named values start over.
  let isCleared = false
  on('command.run', { command: 'clear' }, (_, e, next) => {
    isCleared = true

    return next(e)
  })
  on('state.get', { plugin: 'session-kit' }, (_, e, next) => (isCleared ? { value: { value: undefined, version: 0 } } : next(e)))
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: PROMPT, wait: false, origin: { kind: 'composer' } })
  await $.tool.call({ tool: TOOL, task: 'rewrite the README' })
  asked.length = 0

  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  await ui.press({ key: 'new-task-clear' })
  await clock.settle()
  await ui.unmount()
  await $.turn.complete(turn('t-handoff'))
  await clock.settle()
  expect(asked).toEqual(['command session-kit:handoff', 'command clear', `prompt as user: ${PROMPT}`])
})

test('dismissing the offer drops it and sends nothing, before or after the handoff starts', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: PROMPT, wait: false, origin: { kind: 'composer' } })
  asked.length = 0

  for (const surface of ['terminal', 'desktop'] as const) {
    await $.tool.call({ tool: TOOL, task: 'rewrite the README' })
    const ui = await $.ui.mount({ ...BAND, surface })
    await ui.press({ key: 'new-task-dismiss' })
    await clock.settle()
    expect(await ui.find({ type: 'Text', text: /New task/ })).toBeUndefined()
    await ui.unmount()
  }
  expect(asked).toEqual([])

  // Dismissed while the handoff runs: no clear follows it.
  await $.tool.call({ tool: TOOL, task: 'rewrite the README' })
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  await ui.press({ key: 'new-task-clear' })
  await clock.settle()
  await ui.press({ key: 'new-task-dismiss' })
  await ui.unmount()
  await $.turn.complete(turn('t-handoff'))
  await clock.settle()
  expect(asked).toEqual(['command session-kit:handoff'])
})

test('in a context that holds no task yet, new or just cleared, the signal is answered with nothing to clear and offers nothing', { options: { chain: true } }, async ($, on) => {
  mock.clock(on)
  engine(on, { holdsTask: false })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: PROMPT, wait: false, origin: { kind: 'composer' } })

  const answered = await $.tool.call({ tool: TOOL, task: 'rewrite the README install section' })
  expect(answered.deny).toBeUndefined()
  expect(answered.result).toMatch(/nothing to clear/)
  expect(answered.result).toMatch(/start on the prompt/i)
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /New task/ })).toBeUndefined()
  await ui.unmount()
})

test('a signal without a task is refused and offers nothing', { options: { chain: true } }, async ($, on) => {
  engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const answered = await $.tool.call({ tool: TOOL })
  expect(answered.deny).toMatch(/task/)
  expect(answered.result).toBeUndefined()
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /New task/ })).toBeUndefined()
  await ui.unmount()
})

// The engine's answer to a model request, registered before the session starts.
function answersSteps(on: On) {
  on('turn.step', async function* (_, e) {
    const usage = { input_tokens: 10, cache_read_input_tokens: 0, cache_creation_input_tokens: 0, output_tokens: 10, model: 'claude-fable-5-1' }
    yield { kind: 'stop', stopReason: 'end_turn', usage }

    return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn', usage }
  })
}

// A main-loop request sent at the session's effort, which the kit reads.
async function stepAt($: EngineInterface, effort: 'low' | 'medium' | 'high' | 'xhigh' | 'max') {
  for await (const _ of $.turn.step({ turnId: 't0', index: 0, model: 'claude-fable-5-1', effort, messageCount: 3 })) {
    // Read to its end, as the engine does.
  }
}

test('an effort the model proposes for the new task is set by the person\'s press, after the clear and before the prompt is sent again', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  let isCleared = false
  on('command.run', { command: 'clear' }, (_, e, next) => {
    isCleared = true

    return next(e)
  })
  on('state.get', { plugin: 'session-kit' }, (_, e, next) => (isCleared ? { value: { value: undefined, version: 0 } } : next(e)))
  const asked = engine(on)
  answersSteps(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await stepAt($, 'high')
  await $.prompt.submit({ text: PROMPT, wait: false, origin: { kind: 'composer' } })
  await $.tool.call({ tool: TOOL, task: 'rewrite the README', effort: 'low', effort_reason: 'a mechanical edit' })
  asked.length = 0

  let ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  expect((await ui.find({ type: 'Text', text: /New task/ }))?.text).toMatch(/effort low.*a mechanical edit/)
  expect(await ui.find({ type: 'Button', text: /Handoff and clear/ })).toBeDefined()
  await ui.press({ key: 'new-task-clear-effort' })
  await clock.settle()
  await ui.unmount()
  await $.turn.complete(turn('t-handoff'))
  await clock.settle()
  expect(asked).toEqual(['command session-kit:handoff', 'command clear', 'command effort low', `prompt as user: ${PROMPT}`])

  // Keeping on in this context never changes the effort: the change would write the whole context to the cache again.
  isCleared = false
  await $.prompt.submit({ text: PROMPT, wait: false, origin: { kind: 'composer' } })
  await $.tool.call({ tool: TOOL, task: 'rewrite the README', effort: 'low', effort_reason: 'a mechanical edit' })
  asked.length = 0
  ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  await ui.press({ key: 'new-task-here' })
  await clock.settle()
  await ui.unmount()
  expect(asked).toEqual([`prompt as user: ${PROMPT}`])
})
