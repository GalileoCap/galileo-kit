import { expect, mock, test } from 'claude-code/testing'

import type { ContextMemoryFile, On, SessionContextBreakdown, TurnCompleteInput } from 'claude-code'

// The timeline is read by the kit's Python readers (session-transcripts,
// session-rulebook), so its files and lines are a contract these tests hold.

const HOME = '/home/me'
const DIR = `${HOME}/.claude/session-kit/measure`
const CONCERNS = ['facts', 'context', 'presend', 'tags', 'band', 'pane', 'test_log', 'doc_length', 'nudge', 'checkout', 'suppressions']
const CLAUDE_MD: ContextMemoryFile = { path: '/proj/CLAUDE.md', type: 'Project', tokens: 900 }
const HANDOFF: ContextMemoryFile = { path: '/proj/CLAUDE.local.md', type: 'Local', tokens: 1500 }
const USAGE = { input_tokens: 10, output_tokens: 300, cache_read_input_tokens: 110_000, cache_creation_input_tokens: 9_990, model: 'claude-fable-5-1' }

type Line = Record<string, unknown>

function breakdown(memoryFiles: ContextMemoryFile[]): SessionContextBreakdown {
  return {
    categories: [],
    totalTokens: 0,
    maxTokens: 1_000_000,
    rawMaxTokens: 1_000_000,
    autocompactSource: 'model-default',
    percentage: 0,
    gridRows: [],
    model: 'claude-fable-5-1',
    memoryFiles,
    mcpTools: [],
    agents: [],
    isAutoCompactEnabled: true,
    apiUsage: null,
  }
}

// The engine beneath the plugin: a session whose id, context and memory files the test moves.
function engine(on: On) {
  const files: Record<string, string> = {}
  const now = { id: 'sess-1', tokens: 120_000, memory: [CLAUDE_MD] }
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/proj' }))
  on('session.id', () => ({ value: now.id }))
  on('session.usage', (_, e) => ({
    value: {
      startedAt: 0,
      context: {
        tokens: now.tokens,
        window: 1_000_000,
        percent: Math.round(now.tokens / 10_000),
        ...(e.breakdown === undefined ? {} : { breakdown: breakdown(now.memory) }),
      },
      rateLimits: [],
      cost: { usd: 1.5 },
    },
  }))
  mock.clock(on, { now: 1_700_000_000_000 })
  mock.env(on, { HOME, TMPDIR: '/var/tmp/t' })
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
  on('ui.log', () => ({ value: undefined }))
  on('tool.call', (_, e) => {
    if (e.tool === 'Bash' && e.command.includes('pytest')) {
      return { isError: true, result: 'FAILED tests/test_a.py::test_b', text: 'FAILED tests/test_a.py::test_b' }
    }

    return { result: {} }
  })
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('session.end', (_, e) => ({ sessionId: e.sessionId }))

  return { files, now }
}

/** The session's timeline: its files in the order written, each as its lines. */
function timeline(files: Record<string, string>, sessionId: string): Line[][] {
  const prefix = `${DIR}/${sessionId}/`

  return Object.keys(files)
    .filter((path) => path.startsWith(prefix) && /^\d+\.jsonl$/.test(path.slice(prefix.length)))
    .sort()
    .map((path) => (files[path] ?? '').split('\n').filter((line) => line !== '').map((line): Line => JSON.parse(line)))
}

function turn(turnId: string, extra: Partial<TurnCompleteInput> = {}): TurnCompleteInput {
  return { answer: 'done', durationMs: 5000, isAborted: false, turnId, reason: 'answer', usage: USAGE, ...extra }
}

function kitTimes(line: Line | undefined): string[] {
  const times = line?.kitMs

  return typeof times === 'object' && times !== null ? Object.keys(times) : []
}

test('a main-loop turn end writes the lines since the last as a new file of the session, each tool call timed through every concern of the kit with what each added', async ($, on) => {
  const { files } = engine(on)
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })

  await $.turn.start({ text: 'go', turnId: 't1' })
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  const failed = await $.tool.call({ tool: 'Bash', command: 'uv run pytest' })
  expect(failed.context?.length).toBe(1)
  await $.tool.call({ tool: 'Read', file_path: '/proj/a.md', agentId: 'agent-1' })
  // A subagent's turn end is a line, and writes nothing yet.
  await $.turn.complete(turn('a1', { agentId: 'agent-1' }))
  expect(timeline(files, 'sess-1')).toEqual([])

  await $.turn.complete(turn('t1'))
  const written = timeline(files, 'sess-1')
  expect(written.length).toBe(1)
  const lines = written[0] ?? []
  expect(lines.map((l) => l.ev)).toEqual(['turn.start', 'tool', 'tool', 'tool', 'turn.end', 'turn.end', 'memory'])
  expect(lines.every((l) => typeof l.at === 'number')).toBe(true)

  const [start, ls, pytest, read, subagentEnd, end, memory] = lines
  expect(start).toMatchObject({ turn: 't1' })
  expect(ls).toMatchObject({ tool: 'Bash', turn: 't1' })
  expect(typeof ls?.id).toBe('string')
  expect(typeof ls?.ms).toBe('number')
  expect(typeof ls?.beneathMs).toBe('number')
  expect(kitTimes(ls)).toEqual(CONCERNS)
  expect(ls?.added).toBeUndefined()
  expect(ls?.error).toBeUndefined()
  // The failed run's context is the test log's, one entry, counted with its length.
  expect(pytest).toMatchObject({ tool: 'Bash', turn: 't1', error: true, added: { test_log: { entries: 1 } } })
  expect(Object.keys(pytest?.added ?? {})).toEqual(['test_log'])
  expect(read).toMatchObject({ tool: 'Read', agent: 'agent-1' })
  expect(read?.turn).toBeUndefined()
  expect(subagentEnd).toMatchObject({ turn: 'a1', agent: 'agent-1', reason: 'answer' })
  expect(subagentEnd?.context).toBeUndefined()
  expect(end).toMatchObject({ turn: 't1', reason: 'answer', durationMs: 5000, usage: USAGE, context: { tokens: 120_000, window: 1_000_000 }, costUsd: 1.5 })
  expect(kitTimes(end)).toEqual(CONCERNS)
  expect(memory).toMatchObject({ files: [CLAUDE_MD] })

  // The next turn's file holds its own lines alone, and the memory files are not read again within the context.
  await $.turn.start({ text: 'more', turnId: 't2' })
  await $.turn.complete(turn('t2'))
  expect(timeline(files, 'sess-1').map((file) => file.map((l) => l.ev))).toEqual([
    ['turn.start', 'tool', 'tool', 'tool', 'turn.end', 'turn.end', 'memory'],
    ['turn.start', 'turn.end'],
  ])
})

test('the memory files are read again after a compaction and after a clear, and the session a clear starts names the one it came from', async ($, on) => {
  const { files, now } = engine(on)
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })
  await $.turn.start({ text: 'go', turnId: 't1' })
  await $.turn.complete(turn('t1'))

  // A compaction leaves the context smaller than the last turn's end.
  now.tokens = 20_000
  now.memory = [CLAUDE_MD, HANDOFF]
  await $.turn.start({ text: 'Continue.', turnId: 't2' })
  await $.turn.complete(turn('t2'))
  const compacted = timeline(files, 'sess-1')[1] ?? []
  expect(compacted.map((l) => l.ev)).toEqual(['turn.start', 'turn.end', 'memory'])
  expect(compacted[2]).toMatchObject({ files: [CLAUDE_MD, HANDOFF] })

  // The context grows: no reading.
  now.tokens = 30_000
  await $.turn.start({ text: 'more', turnId: 't3' })
  await $.turn.complete(turn('t3'))
  expect(timeline(files, 'sess-1')[2]?.map((l) => l.ev)).toEqual(['turn.start', 'turn.end'])

  // The clear writes what the old session holds to its own directory.
  await $.turn.start({ text: 'and this', turnId: 't4' })
  await $.session.end({ reason: 'clear', sessionId: 'sess-1', resume: { id: 'sess-1' } })
  const ended = timeline(files, 'sess-1')[3] ?? []
  expect(ended.map((l) => l.ev)).toEqual(['turn.start', 'session.end'])
  expect(ended[1]).toMatchObject({ reason: 'clear' })

  now.id = 'sess-2'
  now.tokens = 10_000
  await $.turn.start({ text: 'a new task', turnId: 't5' })
  await $.turn.complete(turn('t5'))
  const fresh = timeline(files, 'sess-2')
  expect(fresh.map((file) => file.map((l) => l.ev))).toEqual([['session', 'turn.start', 'turn.end', 'memory']])
  expect(fresh[0]?.[0]).toMatchObject({ from: 'sess-1', reason: 'clear' })
  expect(timeline(files, 'sess-1').length).toBe(4)
})

test('the measure option off writes no timeline', { options: { measure: false } }, async ($, on) => {
  const { files } = engine(on)
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })
  await $.turn.start({ text: 'go', turnId: 't1' })
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  await $.turn.complete(turn('t1'))
  expect(Object.keys(files).filter((path) => path.startsWith(DIR))).toEqual([])
})
