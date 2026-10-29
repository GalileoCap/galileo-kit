import { expect, test } from 'claude-code/testing'

import type { EngineInterface, On, TurnCompleteInput } from 'claude-code'

import { world } from './world.test-helper'

const BAND = {
  plugin: 'session-kit',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 4 }, view: {} },
} as const

// What the engine beneath saw: the context each prompt reached it with, and the prompts the kit sent.
function engine(on: On) {
  const reached: { text: string; context: readonly string[] }[] = []
  const sent: string[] = []
  on('prompt.submit', (_, e) => {
    if (e.origin?.kind === 'plugin') {
      sent.push(e.text)
    }
    reached.push({ text: e.text, context: e.context ?? [] })

    return { text: e.text, context: e.context }
  })
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })

  return { reached, sent }
}

function typed(text: string) {
  return { text, wait: false, origin: { kind: 'composer' as const } }
}

function reply(answer: string, turnId = 't'): TurnCompleteInput {
  return { answer, durationMs: 10, isAborted: false, turnId, reason: 'answer' }
}

/** The kit's context on the last prompt that reached the engine, joined. */
function lastContext(reached: { context: readonly string[] }[]): string {
  return (reached.at(-1)?.context ?? []).join('\n')
}

/** The items the kit listed on the last prompt, without the closing-line forms after them. */
function lastItems(reached: { context: readonly string[] }[]): string {
  return /by id: (.*?)\. End the reply/.exec(lastContext(reached))?.[1] ?? ''
}

async function bandText($: EngineInterface): Promise<string> {
  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  const texts = await ui.findAll({ type: 'Text' })
  await ui.unmount()

  return texts.map((t) => t.text).join(' | ')
}

const START = { cwd: '/proj', surface: 'desktop', isInteractive: true } as const

test('a tagged message gets an id per item in hidden context, and FYI, pasted, fenced and untagged lines open none', async ($, on) => {
  world(on)
  const { reached } = engine(on)
  await $.session.start(START)

  await $.prompt.submit(typed('just a question about the layout'))
  expect(lastItems(reached)).toBe('')

  await $.prompt.submit(
    typed(
      [
        'Do: rename it to Verdict',
        '- Ask: why is this in the styleguide?',
        'FYI: the stats row is tight',
        'Decide: Q4, refuse to delete',
        '```',
        'Do: an example inside a fence',
        '```',
        '<pasted_content id="x">',
        'Later: a line from a pasted document',
        '</pasted_content id="x">',
      ].join('\n'),
    ),
  )
  // The message itself reaches the model with each tag written as its id; FYI, fenced and pasted lines keep theirs.
  const shown = reached.at(-1)?.text ?? ''
  expect(shown).toMatch(/^Do-1: rename it to Verdict$/m)
  expect(shown).toMatch(/^- Ask-1: why is this in the styleguide\?$/m)
  expect(shown).toMatch(/^Decide-1: Q4, refuse to delete$/m)
  expect(shown).toMatch(/^FYI: the stats row is tight$/m)
  expect(shown).toMatch(/^Do: an example inside a fence$/m)
  expect(shown).toMatch(/^Later: a line from a pasted document$/m)
  const context = lastContext(reached)
  expect(context).toMatch(/Do-1 "rename it to Verdict"/)
  expect(context).toMatch(/Ask-1 "why is this in the styleguide\?"/)
  expect(context).toMatch(/Decide-1 "Q4, refuse to delete"/)
  expect(context).not.toMatch(/FYI-/)
  expect(lastItems(reached)).not.toMatch(/Do-2|Later-1|example inside|pasted document/)
})

test('an item the reply leaves without a line is on the band and prompted once; a line that names it closes it', async ($, on) => {
  const w = world(on)
  const { reached, sent } = engine(on)
  await $.session.start(START)

  await $.prompt.submit(typed('Do: rename it to Verdict\nAsk: why is this here?'))
  await $.turn.complete(reply('It is here for the grid.\n\nAsk-1 Answered: why is this here'))
  await w.clock.settle()
  expect(sent.length).toBe(1)
  expect(sent[0]).toMatch(/Do-1/)
  expect(sent[0]).not.toMatch(/Ask-1/)
  expect(await bandText($)).toMatch(/Do-1/)

  // The kit's own prompt's turn misses it again: no second prompt.
  await $.turn.complete(reply('Working on it.'))
  await w.clock.settle()
  expect(sent.length).toBe(1)

  // In progress keeps it open, and the next tagged message lists it again beside its new items.
  await $.prompt.submit(typed('Do: add the stats row'))
  expect(lastContext(reached)).toMatch(/Do-1 "rename it to Verdict"/)
  expect(lastContext(reached)).toMatch(/Do-2 "add the stats row"/)
  await $.turn.complete(reply('**Do-1** In progress: the grid is renamed, the styleguide is left\n- Do-2 Done: the row is in (commit abc1234)'))
  await w.clock.settle()
  expect(sent.length).toBe(1)
  expect(await bandText($)).not.toMatch(/Do-2/)

  // Done closes it: the next tagged message no longer lists it.
  await $.prompt.submit(typed('Do: ship it'))
  expect(lastContext(reached)).toMatch(/Do-1 "rename it to Verdict"/)
  await $.turn.complete(reply('Do-1 Done: renamed\nDo-3 Done: shipped'))
  await $.prompt.submit(typed('Ask: anything left?'))
  expect(lastItems(reached)).not.toMatch(/Do-1|Do-3/)
  expect(lastItems(reached)).toMatch(/Ask-2/)
})

test('an id in prose, or a turn that is not the main loop\'s, closes nothing and prompts nothing', async ($, on) => {
  const w = world(on)
  const { sent } = engine(on)
  await $.session.start(START)

  await $.prompt.submit(typed('Do: rename it'))
  await $.turn.complete({ ...reply('Do-1 Done: a subagent says so'), agentId: 'sub-1' })
  await w.clock.settle()
  expect(sent.length).toBe(0)
  await $.turn.complete(reply('I renamed it, which settles Do-1 Done: as asked.'))
  await w.clock.settle()
  expect(sent.length).toBe(1)
})

test('nothing is checked while the chain is under way', { options: { chain: true } }, async ($, on) => {
  const w = world(on)
  const { sent } = engine(on)
  on('tool.register', (_, e) => ({ value: { tool: `mcp__session-kit__${e.name}` } }))
  on('command.run', () => ({ text: '' }))
  on('tool.call', () => ({ result: {} }))
  await $.session.start(START)

  await $.prompt.submit(typed('Do: rename it'))
  await $.tool.call({ tool: 'mcp__session-kit__clear_point', next_step: 'session', note: 'go on' })
  await $.turn.complete(reply('Clear point.'))
  await w.clock.settle()
  expect(sent.filter((s) => /Do-1/.test(s))).toEqual([])
})
