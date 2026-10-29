// A question the session put to the person in the next-step box waits from
// that turn until the person's next prompt. Nothing of the kit's starts a turn
// or a compaction over it; the cold timer, which cannot wait, carries it across
// into the handoff and onto the band, with its buttons.

import { expect, mock, test } from 'claude-code/testing'

import type { EngineInterface, On, SessionUsage, TurnCompleteInput } from 'claude-code'

const WINDOW = 1_000_000
const MINUTE = 60_000
const WRAP_UP = 'mcp__ccd_turn__wrap_up'
const CLEAR_POINT = 'mcp__session-kit__clear_point'

const QUESTION = 'Which Overview should draw value against spend?'
const ACTIONS = [
  { label: 'The team one', message: 'Draw it on the team Overview.' },
  { label: 'Both', message: 'Draw it on both Overviews.' },
]

const BAND = {
  plugin: 'session-kit',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 4 }, view: {} },
} as const

function usage(percent: number): SessionUsage {
  const tokens = Math.round((WINDOW * percent) / 100)

  return { startedAt: 0, context: { tokens, window: WINDOW, percent }, rateLimits: [] }
}

function reply(turnId: string, answer = 'done'): TurnCompleteInput {
  return { answer, durationMs: 10, isAborted: false, turnId, reason: 'answer' }
}

// The engine beneath the plugin: what the kit asked of it, and the prompts it sent.
function engine(on: On, percent: number) {
  const asked: string[] = []
  const sent: { text: string; asUser: boolean }[] = []
  on('session.usage', () => ({ value: usage(percent) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('tool.register', (_, e) => ({ value: { tool: `mcp__session-kit__${e.name}` } }))
  on('command.run', (_, e) => {
    asked.push(e.args === '' || e.args === undefined ? `command ${e.command}` : `command ${e.command} ${e.args}`)

    return { text: 'ran' }
  })
  on('session.compact', () => {
    asked.push('compact')

    return { messages: [{ role: 'user' as const, text: 'the summary', toolUses: [] }] }
  })
  on('prompt.submit', (_, e) => {
    if (e.origin?.kind === 'plugin') {
      sent.push({ text: e.text, asUser: e.origin.asUser === true })
    }

    return { text: e.text, context: e.context }
  })
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('tool.call', () => ({ result: {} }))
  on('ui.status', () => ({ value: undefined }))
  on('ui.log', () => ({ value: undefined }))
  on('fs.exists', () => ({ value: false }))
  on('process.run', () => ({ value: { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })

  return { asked, sent }
}

async function asks($: EngineInterface): Promise<void> {
  await $.tool.call({ tool: WRAP_UP, recap: 'The Overview is drawn.', ask: QUESTION, actions: ACTIONS, blocked: true })
}

const START = { cwd: '/', surface: 'desktop', isInteractive: true } as const

test('a clear point in the turn that asked waits: no handoff and no compaction while the question is pending', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const { asked } = engine(on, 55)
  await $.session.start(START)

  await $.turn.start({ text: 'draw the Overview', turnId: 't1' })
  await asks($)
  await $.tool.call({ tool: CLEAR_POINT, next_step: 'owner', note: 'the owner picks the Overview' })
  await $.turn.complete(reply('t1'))
  await clock.settle()
  expect(asked).toEqual([])
})

test('a missed tagged item is not prompted over a pending question', async ($, on) => {
  const clock = mock.clock(on)
  const { sent } = engine(on, 10)
  await $.session.start(START)

  await $.prompt.submit({ text: 'Do: draw the Overview\nDo: name the axis', wait: false, origin: { kind: 'composer' } })
  await $.turn.start({ text: '', turnId: 't1' })
  await asks($)
  await $.turn.complete(reply('t1', 'Do-1 Done: drawn'))
  await clock.settle()
  expect(sent).toEqual([])
})

test('the cold timer carries a pending question across: word for word into the handoff, then on the band with its buttons until answered', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const { asked, sent } = engine(on, 30)
  await $.session.start(START)

  await $.turn.start({ text: 'draw the Overview', turnId: 't1' })
  await asks($)
  await $.turn.complete(reply('t1'))
  await clock.settle()
  await clock.advance(55 * MINUTE)

  const handoff = asked.find((a) => a.startsWith('command session-kit:handoff')) ?? ''
  expect(handoff).toContain(QUESTION)
  expect(handoff).toContain(ACTIONS[0].label)
  expect(handoff).toContain(ACTIONS[1].label)

  await $.turn.start({ text: '', turnId: 't-handoff' })
  await $.turn.complete(reply('t-handoff'))
  await clock.settle()
  expect(asked.some((a) => a.startsWith('command compact'))).toBe(true)

  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  const texts = (await ui.findAll({ type: 'Text' })).map((t) => t.text).join(' | ')
  expect(texts).toContain(QUESTION)
  await ui.press({ key: 'question-1' })
  await clock.settle()
  await ui.unmount()
  expect(sent.at(-1)).toEqual({ text: ACTIONS[1].message, asUser: true })

  const after = await $.ui.mount({ ...BAND, surface: 'desktop' })
  const left = (await after.findAll({ type: 'Text' })).map((t) => t.text).join(' | ')
  await after.unmount()
  expect(left).not.toContain(QUESTION)
})
