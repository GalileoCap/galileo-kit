// Each session keeps a record of itself under ~/.claude/session-kit/sessions/,
// read across sessions by what counts the owner's load: whether it is working
// or waiting on the owner, whether a question of its waits, and a beat a
// reader tells a closed session by. The file's fields are a contract.

import { expect, mock, test } from 'claude-code/testing'

import type { On, TurnCompleteInput } from 'claude-code'

const HOME = '/home/me'
const DIR = `${HOME}/.claude/session-kit/sessions`
const MINUTE = 60_000
const T0 = 1_700_000_000_000
const START = { cwd: '/proj', surface: 'desktop', isInteractive: true } as const

type Record = { id: string; cwd: string; state: string; since: number; beat: number; question: boolean }

function engine(on: On) {
  const files: { [path: string]: string } = {}
  const now = { id: 'sess-1' }
  const clock = mock.clock(on, { now: T0 })
  mock.env(on, { HOME })
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.end', (_, e) => ({ sessionId: e.sessionId }))
  on('session.cwd', () => ({ value: '/proj' }))
  on('session.id', () => ({ value: now.id }))
  on('session.usage', () => ({ value: { startedAt: 0, context: { tokens: 100_000, window: 1_000_000, percent: 10 }, rateLimits: [] } }))
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
  on('fs.exists', (_, e) => ({ value: e.path in files }))
  on('process.run', () => ({ value: { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('tool.register', (_, e) => ({ value: { tool: `mcp__session-kit__${e.name}` } }))
  on('tool.call', () => ({ result: {} }))
  on('prompt.submit', (_, e) => ({ text: e.text, context: e.context }))
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('ui.status', () => ({ value: undefined }))
  on('ui.log', () => ({ value: undefined }))

  const record = (id: string): Record => JSON.parse(files[`${DIR}/${id}.json`] ?? 'null')

  return { clock, now, record }
}

function reply(turnId: string, agentId?: string): TurnCompleteInput {
  return { answer: 'done', durationMs: 10, isAborted: false, turnId, reason: 'answer', ...(agentId === undefined ? {} : { agentId }) }
}

test('a main-loop turn marks the session working, its end waiting on the owner, with a question when one waits; a subagent writes nothing', async ($, on) => {
  const { clock, record } = engine(on)
  await $.session.start(START)
  expect(record('sess-1')).toMatchObject({ id: 'sess-1', cwd: '/proj', state: 'waiting', question: false })

  await clock.advance(5_000)
  await $.turn.start({ text: 'go', turnId: 't1' })
  expect(record('sess-1')).toMatchObject({ state: 'working', since: T0 + 5_000 })

  await $.turn.start({ text: 'look', turnId: 'a1', agentId: 'agent-1' })
  await $.turn.complete(reply('a1', 'agent-1'))
  expect(record('sess-1')).toMatchObject({ state: 'working' })

  await clock.advance(5_000)
  await $.tool.call({ tool: 'mcp__ccd_turn__wrap_up', recap: 'Drawn.', ask: 'Which one?', actions: [{ label: 'A' }] })
  await $.turn.complete(reply('t1'))
  expect(record('sess-1')).toMatchObject({ state: 'waiting', since: T0 + 10_000, question: true })

  await $.prompt.submit({ text: 'A', wait: false, origin: { kind: 'composer' } })
  await $.turn.start({ text: 'A', turnId: 't2' })
  await $.turn.complete(reply('t2'))
  expect(record('sess-1')).toMatchObject({ state: 'waiting', question: false })
})

test('a live session beats each minute, so a closed one is told by its age; a clear ends the old record as the new one starts', async ($, on) => {
  const { clock, now, record } = engine(on)
  await $.session.start(START)
  await clock.advance(3 * MINUTE)
  const beaten = record('sess-1')
  expect(beaten.beat).toBeGreaterThanOrEqual(T0 + 2 * MINUTE)
  expect(beaten.since).toBe(T0)

  await $.session.end({ reason: 'clear', sessionId: 'sess-1', resume: { id: 'sess-1' } })
  now.id = 'sess-2'
  await $.session.start(START)
  const ended = record('sess-1')
  expect(ended).toMatchObject({ state: 'ended' })
  expect(record('sess-2')).toMatchObject({ id: 'sess-2', state: 'waiting' })

  await clock.advance(2 * MINUTE)
  expect(record('sess-1').beat).toBe(ended.beat)
  expect(record('sess-2').beat).toBeGreaterThan(T0 + 3 * MINUTE)
})
