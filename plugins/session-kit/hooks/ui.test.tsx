import { expect, mock, test } from 'claude-code/testing'

import type { EngineInterface, On, RenderSurface, SessionContextUsage, SessionUsage, TurnCompleteInput } from 'claude-code'

const WINDOW = 1_000_000
const MINUTE = 60_000
const SHORT_TURN_MS = 3000
const CLEAR_POINT = 'mcp__session-kit__clear_point'
const HANDOFF = 'session-kit:handoff'
const START = { cwd: '/', surface: 'terminal', isInteractive: true } as const

const BAND = {
  plugin: 'session-kit',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 4 }, view: {} },
} as const

// What the test controls beneath the plugin.
type State = {
  // The context the engine reports; undefined for an engine with no figure yet.
  tokens: number | undefined
  surfaces: RenderSurface[]
  // A command that throws when run.
  failing: { command: string; reason: string } | undefined
  // A /compact still running until this settles.
  held: Promise<void> | undefined
}

// What the engine beneath saw the plugin do.
type Seen = {
  clock: ReturnType<typeof mock.clock>
  ran: string[]
  prompts: string[]
  statuses: (string | undefined)[]
  toasts: string[]
  notified: string[]
  registered: string[]
  opened: { id: string; title: string | undefined }[]
}

function host(tokens: number | undefined): State {
  return { tokens, surfaces: ['terminal', 'desktop'], failing: undefined, held: undefined }
}

function context(tokens: number | undefined): SessionContextUsage {
  return tokens === undefined ? { window: WINDOW } : { tokens, window: WINDOW, percent: Math.round((tokens / WINDOW) * 100) }
}

function usage(tokens: number | undefined): SessionUsage {
  return { startedAt: 0, context: context(tokens), rateLimits: [] }
}

function turn(turnId: string, durationMs = 10): TurnCompleteInput {
  return { answer: 'done', durationMs, isAborted: false, turnId, reason: 'answer' }
}

// The engine beneath the plugin, with the context at `state.tokens` and a line of its own in every drawing.
function engine(on: On, state: State): Seen {
  const files: Record<string, string> = {}
  const seen: Seen = { clock: mock.clock(on), ran: [], prompts: [], statuses: [], toasts: [], notified: [], registered: [], opened: [] }
  mock.env(on, { TMPDIR: '/var/tmp/ui' })
  on('session.id', () => ({ value: 'sess-ui' }))
  on('session.usage', () => ({ value: usage(state.tokens) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('session.surfaces', () => ({ value: state.surfaces }))
  on('session.measure', (_, e) => ({ changed: e.changed }))
  on('session.turns', () => ({ value: 2 }))
  on('session.messages', () => ({ value: [{ role: 'assistant' as const, text: 'the last task', toolUses: [] }] }))
  on('tool.register', (_, e) => ({ value: { tool: `mcp__session-kit__${e.name}` } }))
  on('turn.start', (_, e) => ({ turnId: e.turnId }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('tool.call', () => ({ result: {} }))
  on('prompt.submit', (_, e) => {
    seen.prompts.push(e.text)

    return { text: e.text }
  })
  on('command.run', async (_, e) => {
    seen.ran.push(e.command)
    if (state.failing?.command === e.command) {
      throw new Error(state.failing.reason)
    }
    if (e.command === 'compact' && state.held !== undefined) {
      await state.held
    }

    return { text: 'ran' }
  })
  on('command.register', (_, e) => {
    seen.registered.push(e.name)

    return { value: { command: e.name } }
  })
  on('ui.open', (_, e) => {
    seen.opened.push({ id: e.id, title: e.title })

    return { value: { isPlaced: true } }
  })
  on('ui.toast', (_, e) => {
    seen.toasts.push(e.text)

    return { value: undefined }
  })
  on('ui.status', (_, e) => {
    seen.statuses.push(e.text)

    return { value: undefined }
  })
  on('ui.log', () => ({ value: undefined }))
  on('ui.notify', (_, e) => {
    seen.notified.push(e.text)

    return { value: { isSent: true as const, channel: 'terminal_bell' as const } }
  })
  // The checks at each turn end run git and look for the handoff: no repository and no file here.
  on('process.run', () => ({ value: { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }))
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
  // The engine's own line, and its turn line.
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>{e.component === 'TurnDuration' ? `${e.props.word} for ${Math.round(e.props.durationMs / 1000)}s` : 'engine'}</Text>
  })

  return seen
}

// What `find` and `findAll` describe of an element.
type FoundElement = { type: string; key: string | undefined; props: Record<string, unknown>; text: string }

type Snapshot = { texts: FoundElement[]; buttons: FoundElement[] }

async function snap($: EngineInterface, surface: 'terminal' | 'desktop' = 'desktop', isWorking = false): Promise<Snapshot> {
  const ui = await $.ui.mount({ ...BAND, props: { ...BAND.props, isWorking }, surface })
  const drawn = { texts: await ui.findAll({ type: 'Text' }), buttons: await ui.findAll({ type: 'Button' }) }
  await ui.unmount()

  return drawn
}

function textOf(texts: FoundElement[], pattern: RegExp): FoundElement | undefined {
  return texts.find((t) => pattern.test(t.text))
}

function buttonOf(drawn: Snapshot, key: string): FoundElement | undefined {
  return drawn.buttons.find((b) => b.key === key)
}

async function press($: EngineInterface, seen: Seen, key: string): Promise<void> {
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  expect(await ui.find({ type: 'Button', key })).toBeDefined()
  await ui.press({ key })
  await seen.clock.settle()
  await ui.unmount()
}

// A turn of the person's: it starts, reads the context once, and ends.
async function personsTurn($: EngineInterface, seen: Seen, id: string): Promise<void> {
  await $.turn.start({ text: 'go on', turnId: id })
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  await $.turn.complete(turn(id))
  await seen.clock.settle()
}

// The turn the handoff command starts, which the engine would run and end.
async function handoffTurn($: EngineInterface, seen: Seen, id: string): Promise<void> {
  await $.turn.start({ text: '', turnId: id })
  await $.turn.complete(turn(id))
  await seen.clock.settle()
}

test('Handoff and compact is the person\'s own signal: the handoff, then when its turn ends the compaction, then the chain waits on the owner with no continue prompt', { timeoutMs: 3000 }, async ($, on) => {
  const state = host(312_000)
  const seen = engine(on, state)
  let finish = () => {}
  state.held = new Promise<void>((resolve) => {
    finish = resolve
  })
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'ls' })

  await press($, seen, 'context-chain')
  expect(seen.ran).toEqual([HANDOFF])
  let drawn = await snap($)
  expect(textOf(drawn.texts, /^session-kit is writing the handoff\./)).toBeDefined()
  // The chain row replaces the context row.
  expect(textOf(drawn.texts, /^Context$/)).toBeUndefined()

  await handoffTurn($, seen, 'h')
  expect(seen.ran).toEqual([HANDOFF, 'compact'])
  expect(textOf((await snap($)).texts, /^session-kit is compacting the context\./)).toBeDefined()

  finish()
  await seen.clock.settle()
  drawn = await snap($)
  expect(textOf(drawn.texts, /^Compacted\. The next step is yours: go on from the handoff, written at your request/)).toBeDefined()
  expect(seen.prompts).toEqual([])
  expect(seen.ran).toEqual([HANDOFF, 'compact'])
})

test('a handoff that does not run stops the chain and leaves a Failed row above the others, with Try again and Dismiss, until dismissed', { timeoutMs: 3000 }, async ($, on) => {
  const state = host(312_000)
  const seen = engine(on, state)
  state.failing = { command: HANDOFF, reason: 'boom' }
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'ls' })

  await press($, seen, 'context-chain')
  for (const surface of ['terminal', 'desktop', 'desktop'] as const) {
    const drawn = await snap($, surface)
    const label = textOf(drawn.texts, /^Failed$/)
    expect(label?.props.bold).toBe(true)
    expect(label?.props.color).toBe('error')
    expect(textOf(drawn.texts, /the handoff did not run \(.+\), so the chain stopped/)).toBeDefined()
    expect(buttonOf(drawn, 'failure-retry')?.text).toBe('Try again')
    expect(buttonOf(drawn, 'failure-dismiss')?.text).toBe('Dismiss')
    expect(textOf(drawn.texts, /^session-kit is writing/)).toBeUndefined()
    expect(drawn.texts.findIndex((t) => t.text === 'Failed')).toBeLessThan(drawn.texts.findIndex((t) => t.text === 'engine'))
  }
  // A band that draws it needs no toast.
  expect(seen.toasts.filter((t) => /did not run/.test(t))).toEqual([])

  await press($, seen, 'failure-dismiss')
  expect(textOf((await snap($)).texts, /^Failed$/)).toBeUndefined()
})

test('Try again resumes the chain where it stopped: a handoff that failed is run again, a compaction that failed is run again alone', { timeoutMs: 3000 }, async ($, on) => {
  const state = host(312_000)
  const seen = engine(on, state)
  state.failing = { command: HANDOFF, reason: 'boom' }
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'ls' })

  await press($, seen, 'context-chain')
  state.failing = undefined
  await press($, seen, 'failure-retry')
  expect(seen.ran).toEqual([HANDOFF, HANDOFF])
  expect(textOf((await snap($)).texts, /^Failed$/)).toBeUndefined()

  state.failing = { command: 'compact', reason: 'nope' }
  await handoffTurn($, seen, 'h')
  expect(seen.ran).toEqual([HANDOFF, HANDOFF, 'compact'])
  expect(textOf((await snap($)).texts, /the compaction did not run \(.+\), so the chain stopped/)).toBeDefined()

  state.failing = undefined
  await press($, seen, 'failure-retry')
  expect(seen.ran).toEqual([HANDOFF, HANDOFF, 'compact', 'compact'])
  expect(textOf((await snap($)).texts, /go on from the handoff, written at your request/)).toBeDefined()
})

test('a chain that ends its compaction waiting on the owner is notified, and one that continues by itself says nothing', { timeoutMs: 3000 }, async ($, on) => {
  const seen = engine(on, host(312_000))
  await $.session.start(START)

  await $.tool.call({ tool: CLEAR_POINT, next_step: 'session', note: 'next' })
  await handoffTurn($, seen, 't1')
  await handoffTurn($, seen, 't2')
  expect(seen.prompts.length).toBe(1)
  expect(seen.notified).toEqual([])

  await personsTurn($, seen, 'p')
  await seen.clock.advance(55 * MINUTE)
  await handoffTurn($, seen, 'h')
  expect(seen.notified.filter((t) => /^session-kit: compacted, the next step is yours/.test(t))).toHaveLength(1)
})

test('the turn line is the engine\'s plus the context percent recorded at the end of the turn with that duration, and exactly the engine\'s for a duration no turn had', { timeoutMs: 3000 }, async ($, on) => {
  const state = host(312_000)
  const seen = engine(on, state)
  await $.session.start(START)
  const line = async (durationMs: number) => {
    const ui = await $.ui.mount({ plugin: 'session-kit', component: 'TurnDuration', surface: 'terminal', props: { word: 'Baked', durationMs } })
    const texts = await ui.findAll({ type: 'Text' })
    await ui.unmount()

    return texts
  }

  // A figure is known, but no turn has ended.
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect((await line(SHORT_TURN_MS)).map((t) => t.text)).toEqual(['Baked for 3s'])

  await $.turn.start({ text: 'one', turnId: 't1' })
  await $.turn.complete(turn('t1', SHORT_TURN_MS))
  state.tokens = 400_000
  await $.turn.start({ text: 'two', turnId: 't2' })
  await $.turn.complete(turn('t2', 5000))
  await seen.clock.settle()

  const first = await line(SHORT_TURN_MS)
  expect(first[0]?.text).toBe('Baked for 3s')
  const ctx = textOf(first, / · ctx 31%/)
  expect(ctx).toBeDefined()
  expect(ctx?.props.dimColor).toBe(true)
  expect(textOf(await line(5000), / · ctx 40%/)).toBeDefined()
  expect((await line(7777)).map((t) => t.text)).toEqual(['Baked for 8s'])
})

