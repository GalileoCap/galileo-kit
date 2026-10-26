import { expect, mock, test } from 'claude-code/testing'

import type { On, SessionUsage, TurnCompleteInput } from 'claude-code'

import { backstop, journalPath } from './context'

const WINDOW = 1_000_000
const TOOL = 'mcp__session-kit__clear_point'

function usage(percent: number): SessionUsage {
  const tokens = Math.round((WINDOW * percent) / 100)

  return { startedAt: 0, context: { tokens, window: WINDOW, percent }, rateLimits: [] }
}

function turn(turnId: string, reason: TurnCompleteInput['reason'] = 'answer'): TurnCompleteInput {
  const ended = { answer: 'done', durationMs: 10, isAborted: reason === 'aborted', turnId }

  return reason === 'refusal'
    ? { ...ended, reason, refusal: { category: null, explanation: null } }
    : { ...ended, reason }
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

type Compaction = {
  percent?: number
  // A /compact still running until this settles.
  held?: Promise<void>
}

// The engine beneath the plugin, recording what the chain asked of it.
function engine(on: On, { percent = 55, held }: Compaction = {}) {
  const asked: string[] = []
  on('session.usage', () => ({ value: usage(percent) }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/' }))
  on('tool.register', (_, e) => {
    // new_task is registered beside it, proven in new_task.test.tsx.
    if (e.name === 'clear_point') {
      asked.push(`register ${e.name}`)
    }

    return { value: { tool: `mcp__session-kit__${e.name}` } }
  })
  on('command.run', async (_, e) => {
    asked.push(e.args === '' ? `command ${e.command}` : `command ${e.command} ${e.args}`)
    if (e.command === 'compact' && held !== undefined) {
      await held
    }

    return { text: 'handoff written' }
  })
  // The engine's own compaction call, which the chain never makes.
  on('session.compact', (_, e) => {
    asked.push(`compact ${e.instructions ?? ''}`)

    return { messages: [{ role: 'user' as const, text: 'the summary', toolUses: [] }] }
  })
  on('prompt.submit', (_, e) => {
    asked.push(`prompt ${e.text}`)

    return { text: e.text }
  })
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('tool.call', () => ({ result: {} }))

  return asked
}

test('off: no tool is registered and the warning names none', { options: { chain: false } }, async ($, on) => {
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(asked).toEqual([])

  const ran = await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(ran.context?.[0]).toMatch(/safe to compact/)
  expect(ran.context?.[0]).not.toMatch(/clear_point/)
})

test('on: the model signals, the mod writes the handoff, compacts and continues', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  expect(asked).toEqual(['register clear_point'])

  const warned = await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(warned.context?.[0]).toMatch(/clear_point/)

  const signalled = await $.tool.call({ tool: TOOL, next_step: 'session', note: 'run the checks' })
  expect(signalled.deny).toBeUndefined()
  // The engine's output schema for a registered tool takes a string: an object is refused at the call.
  expect(typeof signalled.result).toBe('string')
  expect(signalled.result).toMatch(/End this turn/)
  // The warning does not ride on the signal itself.
  expect(signalled.context).toBeUndefined()

  // Nothing runs while the turn goes on.
  expect(asked.length).toBe(1)

  await $.turn.complete(turn('t1'))
  await clock.settle()
  expect(asked[1]).toBe('command session-kit:handoff')
  expect(asked.length).toBe(2)

  await $.turn.complete(turn('t2'))
  await clock.settle()
  // A person is at the prompt, and the chain still compacts through /compact.
  expect(asked[2]).toMatch(/^command compact .*CLAUDE\.local\.md/)
  expect(asked[3]).toMatch(/^prompt .*CLAUDE\.local\.md.*run the checks/)
  expect(asked.length).toBe(4)

  // The continue turn ends: the chain is over, nothing more runs.
  await $.turn.complete(turn('t3'))
  await clock.settle()
  expect(asked.length).toBe(4)
})

test('when the next step is the owner\'s, the chain stops after the compaction and the band says so', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await $.tool.call({ tool: TOOL, next_step: 'owner', note: 'approve O14 to O16' })
  await $.turn.complete(turn('t1'))
  await clock.settle()
  await $.turn.complete(turn('t2'))
  await clock.settle()
  expect(asked[2]).toMatch(/^command compact /)
  expect(asked.length).toBe(3)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    const row = await ui.find({ type: 'Text', text: /next step/ })
    expect(row?.text).toMatch(/yours.*approve O14 to O16/)
    // The chain's line draws above the band beneath it, never in its place.
    expect((await ui.find({ type: 'Text', text: /engine/ }))?.text).toBe('engine')
    await ui.unmount()
  }

  // The owner's next turn clears the notice.
  await $.turn.complete(turn('t3'))
  await clock.settle()
  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /next step/ })).toBeUndefined()
  await ui.unmount()
})

test('an interrupted turn cancels the chain', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'next' })
  await $.turn.complete(turn('t1', 'aborted'))
  await clock.settle()
  await $.turn.complete(turn('t2'))
  await clock.settle()
  expect(asked).toEqual(['register clear_point'])
})

test('a signal without a next step is refused and starts nothing', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const answered = await $.tool.call({ tool: TOOL, note: 'next' })
  expect(answered.deny).toMatch(/next_step/)
  expect(answered.result).toBeUndefined()
  await $.turn.complete(turn('t1'))
  await clock.settle()
  expect(asked).toEqual(['register clear_point'])
})

test('the band shows each stage of the chain', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const bandSays = async (pattern: RegExp) => {
    const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
    const row = await ui.find({ type: 'Text', text: pattern })
    await ui.unmount()

    return row?.text
  }

  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'next' })
  expect(await bandSays(/clear point/i)).toMatch(/when this turn ends/)
  await $.turn.complete(turn('t1'))
  await clock.settle()
  expect(await bandSays(/handoff/i)).toMatch(/writing the handoff/)
})

const NO_COST = { input_tokens: 0, output_tokens: 0, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 }

type Reply = { isAnswered: true; text: string; usage: typeof NO_COST } | { isAnswered: false; reason: 'empty-reply'; usage: typeof NO_COST }

// The judge beneath: what it was asked, how many continues had gone before, and the reply each time.
function judge(on: On, asked: string[], reply: () => Reply) {
  const judged: { before: number; model: string; prompt: string }[] = []
  on('model.complete', (_, e) => {
    judged.push({ before: asked.filter((a) => a.startsWith('prompt Continue')).length, model: e.model, prompt: e.prompt })

    return { value: reply() }
  })

  return judged
}

// A repository whose HEAD is `c<n>`, its log one subject per commit.
function repo(on: On, head: () => number) {
  on('process.run', (_, e) => {
    const args = e.argv.slice(3)
    const done = (stdout: string) => ({ value: { exitCode: 0, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } })
    if (args.join(' ') === 'rev-parse --short HEAD') {
      return done(`c${head()}\n`)
    }
    const range = args[0] === 'log' ? /^c(\d+)\.\.HEAD$/.exec(args[args.length - 1] ?? '') : null
    if (range !== null) {
      const lines: string[] = []
      for (let n = head(); n > Number(range[1]); n -= 1) {
        lines.push(`c${n} commit number ${n}`)
      }

      return done(lines.map((line) => `${line}\n`).join(''))
    }

    return { value: { exitCode: 128, stdout: '', stderr: 'fatal', isStdoutTruncated: false, isStderrTruncated: false } }
  })
}

function handoffFile(on: On) {
  on('fs.read', (_, e) => {
    if (e.path === '/CLAUDE.local.md') {
      return { value: '# Live state\n\n## Task\n\nThe owner: "build the transcript reader".\n\n## Next step\n\nstep 9\n' }
    }
    throw new Error(`ENOENT: ${e.path}`)
  })
}

function answered(text: string): Reply {
  return { isAnswered: true, text, usage: NO_COST }
}

test('the chain goes on by itself, and a judge reads the evidence at the third, the fifth and every signal from the seventh since the person\'s last prompt', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  const judged = judge(on, asked, () => answered('CONTINUE: each step moves the task on.'))
  let commit = 0
  repo(on, () => commit)
  handoffFile(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: 'build it', wait: false, origin: { kind: 'composer' } })
  const continues = () => asked.filter((a) => a.startsWith('prompt Continue')).length
  const chain = async (note: string) => {
    commit += 1
    const signalled = await $.tool.call({ tool: TOOL, next_step: 'session', note })
    await $.turn.complete(turn(`${note}-1`))
    await clock.settle()
    await $.turn.complete(turn(`${note}-2`))
    await clock.settle()

    return signalled
  }

  for (let n = 1; n <= 8; n += 1) {
    expect((await chain(`step ${n}`)).deny).toBeUndefined()
  }
  expect(continues()).toBe(8)
  expect(judged.map((j) => j.before + 1)).toEqual([3, 5, 7, 8])
  const third = judged[0]
  expect(third?.model).toBe('haiku')
  expect(third?.prompt).toMatch(/build the transcript reader/)
  expect(third?.prompt).toMatch(/build it/)
  expect(third?.prompt).toMatch(/1\. \(at commit c1\) step 1\n2\. \(at commit c2\) step 2/)
  expect(third?.prompt).toMatch(/c3 commit number 3\n- c2 commit number 2/)
  expect(third?.prompt).toMatch(/\(at commit c3\) it proposes to go on with:\nstep 3/)

  // A prompt that is not the person's changes nothing: the ninth is judged.
  await $.prompt.submit({ text: 'a task finished', wait: false, origin: { kind: 'task-notification' } })
  await chain('step 9')
  expect(judged.length).toBe(5)

  // The person's next prompt starts the count over, and a step that is the owner's asks no judge.
  await $.prompt.submit({ text: 'carry on', wait: false, origin: { kind: 'composer' } })
  await chain('step a')
  await chain('step b')
  expect(judged.length).toBe(5)
  await $.tool.call({ tool: TOOL, next_step: 'owner', note: 'approve it' })
  expect(judged.length).toBe(5)
  await $.turn.complete(turn('owner-1'))
  await clock.settle()
  await $.turn.complete(turn('owner-2'))
  await clock.settle()
  await chain('step c')
  expect(judged.length).toBe(6)
  expect(continues()).toBe(12)
})

test('a judge that finds a loop, a step beyond the task, or gives no verdict stops the chain after the compaction, with its reason to the model and on the band', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  const replies = [
    answered('LOOP: the same fix is tried a third time with nothing committed.'),
    answered('**BEYOND**: publishing the plugin is the owner\'s to decide'),
    { isAnswered: false as const, reason: 'empty-reply' as const, usage: NO_COST },
    answered('It looks fine to me.'),
  ]
  judge(on, asked, () => replies.shift() ?? answered('CONTINUE: fine.'))
  repo(on, () => 1)
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const continues = () => asked.filter((a) => a.startsWith('prompt Continue')).length
  const chain = async (note: string) => {
    const signalled = await $.tool.call({ tool: TOOL, next_step: 'session', note })
    await $.turn.complete(turn(`${note}-1`))
    await clock.settle()
    await $.turn.complete(turn(`${note}-2`))
    await clock.settle()

    return signalled
  }
  const stopsAt = async (pattern: RegExp) => {
    await $.prompt.submit({ text: 'carry on', wait: false, origin: { kind: 'composer' } })
    await chain('first')
    await chain('second')
    const before = continues()
    const third = await chain('third')
    expect(third.deny).toBeUndefined()
    expect(third.result).toMatch(/^Clear point noted\. session-kit's judge stops the chain after the compaction: /)
    expect(third.result).toMatch(pattern)
    expect(third.result).toMatch(/End this turn now, with nothing more started/)
    // The handoff and the compaction ran, and no continue was sent.
    expect(asked.slice(-2)).toEqual(['command session-kit:handoff', expect.stringMatching(/^command compact /)])
    expect(continues()).toBe(before)
    const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
    const row = await ui.find({ type: 'Text', text: /next step/ })
    expect(row?.text).toMatch(/^Compacted\. The next step is yours: third\. The chain stopped since /)
    expect(row?.text).toMatch(pattern)
    await ui.unmount()
  }

  await stopsAt(/the session is going round: the same fix is tried a third time with nothing committed\./)
  await stopsAt(/the next step goes beyond the owner's task: publishing the plugin is the owner's to decide\./)
  await stopsAt(/the judge gave no verdict \(empty-reply\), and an unjudged chain waits for the owner\./)
  await stopsAt(/the judge gave no verdict \(its reply named none\), and an unjudged chain waits for the owner\./)
})

test('where no person is at the prompt, the chain compacts through /compact and then continues', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  const asked = engine(on)
  await $.session.start({ cwd: '/', surface: null, isInteractive: false })

  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'run the checks' })
  await $.turn.complete(turn('t1'))
  await clock.settle()
  await $.turn.complete(turn('t2'))
  await clock.settle()

  // The engine's own compaction is refused in an SDK session, so it is never asked.
  expect(asked.filter((a) => a.startsWith('compact '))).toEqual([])
  expect(asked.slice(1, 3)).toEqual(['command session-kit:handoff', expect.stringMatching(/^command compact CLAUDE\.local\.md holds the handoff/)])
  expect(asked[3]).toMatch(/^prompt .*run the checks/)
})

test('every stage of a chain leaves a line in the session\'s chain file, which a host that draws no log line still has', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  engine(on)
  const files: Record<string, string> = {}
  mock.env(on, { TMPDIR: '/var/tmp/t' })
  on('session.id', () => ({ value: 'sess-1' }))
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
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'next' })
  await $.turn.complete(turn('t1'))
  await clock.settle()
  await $.turn.complete(turn('t2'))
  await clock.settle()
  await clock.advance(1000)

  const journal = files[journalPath('/var/tmp/t', 'sess-1')] ?? ''
  const stages = [/writing the handoff/, /handoff command returned/, /compacting/, /sending the continue prompt/]
  let from = 0
  for (const stage of stages) {
    const at = journal.slice(from).search(stage)
    expect(at).toBeGreaterThanOrEqual(0)
    from += at + 1
  }
})

test('the backstop tells the engine\'s own compaction what a handoff keeps', async () => {
  const added = backstop(undefined)
  expect(added).toMatch(/CLAUDE\.local\.md/)
  expect(added).toMatch(/next step/)
  expect(added).toMatch(/decision/)
  expect(backstop('keep the plan')).toMatch(/^keep the plan\n/)
  expect(backstop('keep the plan')).toMatch(/next step/)
})

test('dismissing the band stops the chain where it stands, before the handoff or during the compaction', { options: { chain: true } }, async ($, on) => {
  const clock = mock.clock(on)
  let finish = () => {}
  const held = new Promise<void>((resolve) => {
    finish = resolve
  })
  const asked = engine(on, { held })
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const dismiss = async () => {
    const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
    await ui.press({ key: 'chain-dismiss' })
    // The chain's own lines; the figure's line stays, since the turn end past the threshold draws it.
    expect(await ui.find({ type: 'Text', text: /^(Clear point|session-kit is|Compacted)/ })).toBeUndefined()
    await ui.unmount()
  }

  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'next' })
  await dismiss()
  await $.turn.complete(turn('t1'))
  await clock.settle()
  expect(asked).toEqual(['register clear_point'])

  // The band is dismissed while /compact still runs: the compaction lands, and nothing continues after it.
  await $.tool.call({ tool: TOOL, next_step: 'session', note: 'next' })
  await $.turn.complete(turn('t2'))
  await clock.settle()
  await $.turn.complete(turn('t3'))
  await clock.settle()
  await dismiss()
  finish()
  await clock.advance(2000)
  expect(asked).toEqual(['register clear_point', 'command session-kit:handoff', expect.stringMatching(/^command compact /)])
})
