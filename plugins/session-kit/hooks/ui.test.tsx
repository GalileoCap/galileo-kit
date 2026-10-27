import { expect, mock, test } from 'claude-code/testing'

import type { EngineInterface, On, RenderSurface, SessionContextUsage, SessionMeasureInput, SessionRateLimit, SessionUsage, TurnCompleteInput } from 'claude-code'

const WINDOW = 1_000_000
const MINUTE = 60_000
const SHORT_TURN_MS = 3000
const CLEAR_POINT = 'mcp__session-kit__clear_point'
const NEW_TASK = 'mcp__session-kit__new_task'
const HANDOFF = 'session-kit:handoff'
const RESETS_SOON = '2026-10-25T14:30:00Z'
const RESETS_IN_DAYS = '2026-10-28T09:00:00Z'
const START = { cwd: '/', surface: 'terminal', isInteractive: true } as const

const BAND = {
  plugin: 'session-kit',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 4 }, view: {} },
} as const

const PANE = {
  plugin: 'session-kit',
  component: 'Pane',
  requestId: 'kit',
  props: { title: 'session-kit', isFocused: false, bodyColumns: 60, placement: 'dock', scroll: { offset: 0, bodyRows: 40 }, view: {} },
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

function measured(tokens: number | undefined, windows: SessionRateLimit[]): SessionMeasureInput {
  return { context: context(tokens), rateLimits: windows, changed: ['rateLimits'] }
}

function fiveHour(percentUsed: number): SessionRateLimit {
  return { kind: 'five_hour', percentUsed, resetsAt: RESETS_SOON }
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

async function paneTexts($: EngineInterface, surface: RenderSurface = 'terminal'): Promise<FoundElement[]> {
  const ui = await $.ui.mount({ ...PANE, surface })
  const texts = await ui.findAll({ type: 'Text' })
  await ui.unmount()

  return texts
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

function stageLines(texts: FoundElement[]): FoundElement[] {
  return texts.filter((t) => /^\d\d:\d\d /.test(t.text))
}

test('past the trigger the band has a context row of separate Text nodes: a bold label coloured by how far past, the figures compact, and no sentence', { timeoutMs: 3000 }, async ($, on) => {
  const state = host(260_000)
  engine(on, state)
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'ls' })

  for (const surface of ['terminal', 'desktop'] as const) {
    const drawn = await snap($, surface)
    const label = textOf(drawn.texts, /^Context$/)
    expect(label?.props.bold).toBe(true)
    expect(label?.props.color).toBe('warning')
    expect(textOf(drawn.texts, /^260k \/ 1M {2}26%$/)).toBeDefined()
    expect(textOf(drawn.texts, /find a clear point/)).toBeUndefined()
  }

  state.tokens = 300_000
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  const drawn = await snap($)
  expect(textOf(drawn.texts, /^Context$/)?.props.color).toBe('error')
  expect(textOf(drawn.texts, /^300k \/ 1M {2}30%$/)).toBeDefined()
})

test('the row says in dim text how much the last turn grew the context, and nothing when it did not', { timeoutMs: 3000, options: { chain: false } }, async ($, on) => {
  const state = host(300_000)
  const seen = engine(on, state)
  await $.session.start(START)
  const turnEnds = async (id: string, tokens: number) => {
    state.tokens = tokens
    await $.turn.start({ text: 'go on', turnId: id })
    await $.turn.complete(turn(id))
    await seen.clock.settle()

    return (await snap($)).texts
  }

  expect(textOf(await turnEnds('t1', 300_000), /last turn/)).toBeUndefined()
  const grown = textOf(await turnEnds('t2', 312_000), /\+12k last turn/)
  expect(grown).toBeDefined()
  expect(grown?.props.dimColor).toBe(true)
  // The context shrank: nothing grew.
  expect(textOf(await turnEnds('t3', 280_000), /last turn/)).toBeUndefined()
})

test('the row\'s buttons are Handoff, Handoff and compact and Dismiss in that order, and only Dismiss while a turn runs', { timeoutMs: 3000 }, async ($, on) => {
  engine(on, host(312_000))
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'ls' })

  const idle = await snap($)
  expect(idle.buttons.map((b) => b.key)).toEqual(['context-handoff', 'context-chain', 'context-dismiss'])
  expect(idle.buttons.map((b) => b.text)).toEqual(['Handoff', 'Handoff and compact', 'Dismiss'])
  expect((await snap($, 'desktop', true)).buttons.map((b) => b.key)).toEqual(['context-dismiss'])
})

test('Handoff runs the handoff command once and starts no chain', { timeoutMs: 3000 }, async ($, on) => {
  const seen = engine(on, host(312_000))
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'ls' })

  await press($, seen, 'context-handoff')
  expect(seen.ran).toEqual([HANDOFF])
  await handoffTurn($, seen, 'h')
  expect(seen.ran).toEqual([HANDOFF])
  expect(seen.prompts).toEqual([])
})

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

test('the cold timer, once armed, has a Cache row naming when the chain runs, with Run chain now only while no turn runs', { timeoutMs: 3000 }, async ($, on) => {
  const seen = engine(on, host(312_000))
  await $.session.start(START)
  await personsTurn($, seen, 't1')

  const idle = await snap($)
  expect(textOf(idle.texts, /^Cache$/)).toBeDefined()
  expect(textOf(idle.texts, /^handoff and compact at \d\d:\d\d, before it goes cold/)).toBeDefined()
  expect(buttonOf(idle, 'cold-run')?.text).toBe('Run chain now')
  expect(buttonOf(idle, 'cold-dismiss')?.text).toBe('Dismiss')

  const working = await snap($, 'desktop', true)
  expect(buttonOf(working, 'cold-run')).toBeUndefined()
  expect(buttonOf(working, 'cold-dismiss')).toBeDefined()
})

test('Run chain now disarms the timer and starts the same chain as Handoff and compact', { timeoutMs: 3000 }, async ($, on) => {
  const seen = engine(on, host(312_000))
  await $.session.start(START)
  await personsTurn($, seen, 't1')

  await press($, seen, 'cold-run')
  expect(seen.ran).toEqual([HANDOFF])
  await handoffTurn($, seen, 'h')
  expect(seen.ran).toEqual([HANDOFF, 'compact'])
  expect(textOf((await snap($)).texts, /go on from the handoff, written at your request/)).toBeDefined()
  expect(seen.prompts).toEqual([])

  // The timer would have fired at 55 minutes.
  await seen.clock.advance(180 * MINUTE)
  expect(seen.ran).toEqual([HANDOFF, 'compact'])
})

test('a usage window draws a row only from 95%, as an error-coloured sentence', { timeoutMs: 3000 }, async ($, on) => {
  engine(on, host(100_000))
  await $.session.start(START)

  for (const percent of [80, 94]) {
    await $.session.measure(measured(100_000, [fiveHour(percent)]))
    expect(textOf((await snap($)).texts, /usage window/)).toBeUndefined()
  }
  await $.session.measure(measured(100_000, [fiveHour(96)]))
  for (const surface of ['terminal', 'desktop'] as const) {
    const row = textOf((await snap($, surface)).texts, /usage window/)
    expect(row?.text).toMatch(/^The 5-hour usage window is at 96% and resets at \d\d:\d\d\./)
    expect(row?.props.color).toBe('error')
  }
})

test('dismissed at 95 or more, a window stays away until it resets below where it was dismissed', { timeoutMs: 3000 }, async ($, on) => {
  const seen = engine(on, host(100_000))
  await $.session.start(START)
  const row = async () => textOf((await snap($)).texts, /usage window/)

  await $.session.measure(measured(100_000, [fiveHour(96)]))
  expect(await row()).toBeDefined()
  await press($, seen, 'limit-dismiss-five_hour')
  expect(await row()).toBeUndefined()
  await $.session.measure(measured(100_000, [fiveHour(99)]))
  expect(await row()).toBeUndefined()
  // The window reset, and no row draws below 95.
  await $.session.measure(measured(100_000, [fiveHour(3)]))
  await $.session.measure(measured(100_000, [fiveHour(85)]))
  expect(await row()).toBeUndefined()
  await $.session.measure(measured(100_000, [fiveHour(96)]))
  expect(await row()).toBeDefined()
})

test('with the status line off the band draws the window row from 80% as before, and the kit never calls ui.status', { timeoutMs: 3000, options: { statusLine: false } }, async ($, on) => {
  const seen = engine(on, host(312_000))
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  const row = async () => textOf((await snap($)).texts, /usage window/)

  await $.session.measure(measured(312_000, [fiveHour(79)]))
  expect(await row()).toBeUndefined()
  await $.session.measure(measured(312_000, [fiveHour(80.5)]))
  expect((await row())?.text).toMatch(/^The 5-hour usage window is at 80\.5% and resets at \d\d:\d\d\./)
  await press($, seen, 'limit-dismiss-five_hour')
  expect(await row()).toBeUndefined()
  await $.session.measure(measured(312_000, [fiveHour(90)]))
  expect(await row()).toBeUndefined()
  await $.session.measure(measured(312_000, [fiveHour(95)]))
  expect(await row()).toBeDefined()
  expect(seen.statuses).toEqual([])
})

test('the status line joins the figure and one segment per window with a dot, resets from 80%, and calls ui.status only when the text changed', { timeoutMs: 3000 }, async ($, on) => {
  const state = host(undefined)
  const seen = engine(on, state)
  await $.session.start(START)

  // No figure yet: the windows alone, and nothing at all once they are gone.
  await $.session.measure(measured(undefined, [fiveHour(62)]))
  await $.session.measure(measured(undefined, []))
  expect(seen.statuses.slice(-2)).toEqual(['5h 62%', undefined])

  state.tokens = 312_000
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(seen.statuses.at(-1)).toBe('ctx 31% 312k')
  const windows: SessionRateLimit[] = [
    fiveHour(62),
    { kind: 'seven_day', percentUsed: 20, resetsAt: RESETS_IN_DAYS },
    { kind: 'spend_limit', percentUsed: 10 },
    { kind: 'extra_usage', percentUsed: 5 },
  ]
  await $.session.measure(measured(312_000, windows))
  expect(seen.statuses.at(-1)).toBe('ctx 31% 312k · 5h 62% · 7d 20% · spend 10% · extra usage 5%')

  await $.session.measure(measured(312_000, [fiveHour(85), { kind: 'seven_day', percentUsed: 82, resetsAt: RESETS_IN_DAYS }]))
  const segments = (seen.statuses.at(-1) ?? '').split(' · ')
  expect(segments[1]).toMatch(/^5h 85% resets \d\d:\d\d$/)
  expect(segments[2]).toMatch(/^7d 82% resets \d{1,2} [A-Z][a-z]{2} \d\d:\d\d$/)

  const calls = seen.statuses.length
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(seen.statuses.length).toBe(calls)
})

test('the status line adds the last turn\'s growth after the figure and the time the cold timer compacts at while it is armed', { timeoutMs: 3000 }, async ($, on) => {
  const state = host(300_000)
  const seen = engine(on, state)
  await $.session.start(START)
  await personsTurn($, seen, 't1')
  state.tokens = 312_000
  await personsTurn($, seen, 't2')
  expect(seen.statuses.at(-1)).toMatch(/^ctx 31% 312k \(\+12k\) · compacts at \d\d:\d\d$/)

  await press($, seen, 'cold-dismiss')
  expect(seen.statuses.at(-1)).toBe('ctx 31% 312k (+12k)')
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

test('a clear that does not run after the new task\'s handoff shows a Failed row with Dismiss alone', { timeoutMs: 3000 }, async ($, on) => {
  const state = host(100_000)
  const seen = engine(on, state)
  await $.session.start(START)
  await $.prompt.submit({ text: 'Now rewrite the README install section', wait: false, origin: { kind: 'composer' } })
  await $.tool.call({ tool: NEW_TASK, task: 'rewrite the README install section' })

  await press($, seen, 'new-task-clear')
  state.failing = { command: 'clear', reason: 'denied' }
  await handoffTurn($, seen, 'h')
  const drawn = await snap($)
  expect(textOf(drawn.texts, /^Failed$/)).toBeDefined()
  expect(textOf(drawn.texts, /the clear did not run/)).toBeDefined()
  expect(buttonOf(drawn, 'failure-dismiss')).toBeDefined()
  expect(buttonOf(drawn, 'failure-retry')).toBeUndefined()
})

test('where no band is drawn a failure goes out as a toast with the session-kit prefix, and where one is drawn it does not', { timeoutMs: 3000 }, async ($, on) => {
  const state = host(312_000)
  const seen = engine(on, state)
  state.failing = { command: HANDOFF, reason: 'boom' }
  await $.session.start(START)
  const failures = () => seen.toasts.filter((t) => /did not run/.test(t))

  await personsTurn($, seen, 't1')
  await seen.clock.advance(55 * MINUTE)
  expect(seen.ran).toEqual([HANDOFF])
  expect(failures()).toEqual([])
  await press($, seen, 'failure-dismiss')

  state.surfaces = ['mobile']
  await personsTurn($, seen, 't2')
  await seen.clock.advance(55 * MINUTE)
  expect(failures()).toEqual([expect.stringMatching(/^session-kit: the handoff did not run \(.+\), so the chain stopped/)])
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

test('a chain that fails unattended is notified', { timeoutMs: 3000 }, async ($, on) => {
  const state = host(312_000)
  const seen = engine(on, state)
  state.failing = { command: HANDOFF, reason: 'boom' }
  await $.session.start(START)

  await personsTurn($, seen, 't1')
  await seen.clock.advance(55 * MINUTE)
  expect(seen.notified.filter((t) => /did not run/.test(t))).toHaveLength(1)
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

test('the kit command opens the pane only when run, and the pane draws the context on every surface', { timeoutMs: 3000 }, async ($, on) => {
  const seen = engine(on, host(312_000))
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(seen.registered).toContain('kit')
  expect(seen.opened).toEqual([])

  const ran = await $.command.run({ command: 'kit', args: '', origin: { kind: 'composer' }, presentation: { isFullscreen: false, columns: 80 } })
  expect(typeof ran.text).toBe('string')
  expect(seen.opened).toEqual([{ id: 'kit', title: 'session-kit' }])

  for (const surface of ['terminal', 'desktop', 'vscode', 'mobile'] as const) {
    expect(textOf(await paneTexts($, surface), /^312,000 \/ 1,000,000 tokens \(31%\)$/)).toBeDefined()
  }
})

test('the pane with nothing going on: the context bar, no windows, no timer, an idle chain, a missing handoff and no test run', { timeoutMs: 3000 }, async ($, on) => {
  engine(on, host(312_000))
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'ls' })

  const texts = await paneTexts($)
  const bar = textOf(texts, /^[█░]{20}$/)?.text ?? ''
  expect([...bar].filter((c) => c === '█')).toHaveLength(6)
  for (const line of [/^No usage windows$/, /^No timer$/, /^Idle$/, /^Handoff: missing$/, /^Uncommitted: 0 files$/, /^Last test: none$/]) {
    expect(textOf(texts, line)).toBeDefined()
  }
})

test('the pane lists a window with its bar and reset time, and when the cold timer compacts', { timeoutMs: 3000 }, async ($, on) => {
  const seen = engine(on, host(312_000))
  await $.session.start(START)
  await personsTurn($, seen, 't1')
  await $.session.measure(measured(312_000, [fiveHour(62)]))

  const texts = await paneTexts($)
  expect(textOf(texts, /^5h {2}62% {2}█{12}░{8}/)).toBeDefined()
  expect(textOf(texts, /resets \d\d:\d\d/)).toBeDefined()
  expect(textOf(texts, /^Compacts at \d\d:\d\d$/)).toBeDefined()
  expect(textOf(texts, /^No usage windows$/)).toBeUndefined()
  expect(textOf(texts, /^No timer$/)).toBeUndefined()
})

test('the pane names the chain\'s state in the band\'s words and lists its stages, the handoff command before the compaction', { timeoutMs: 3000 }, async ($, on) => {
  const state = host(312_000)
  const seen = engine(on, state)
  state.held = new Promise<void>(() => {})
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'ls' })

  await press($, seen, 'context-chain')
  await handoffTurn($, seen, 'h')
  const texts = await paneTexts($)
  expect(textOf(texts, /^session-kit is compacting the context\.$/)).toBeDefined()
  expect(textOf(texts, /^Idle$/)).toBeUndefined()
  const lines = stageLines(texts)
  expect(lines.findIndex((t) => /running the handoff command/.test(t.text))).toBeGreaterThanOrEqual(0)
  expect(lines.findIndex((t) => /running the handoff command/.test(t.text))).toBeLessThan(lines.length - 1)
})

test('the pane keeps the last 8 chain stage lines', { timeoutMs: 3000 }, async ($, on) => {
  const seen = engine(on, host(312_000))
  await $.session.start(START)
  await $.tool.call({ tool: 'Bash', command: 'ls' })

  for (let n = 1; n <= 6; n += 1) {
    await press($, seen, 'context-chain')
    await handoffTurn($, seen, `h${n}`)
    // The person's next turn clears the notice.
    await personsTurn($, seen, `p${n}`)
  }
  expect(seen.ran.filter((c) => c === 'compact')).toHaveLength(6)
  expect(stageLines(await paneTexts($))).toHaveLength(8)
})
