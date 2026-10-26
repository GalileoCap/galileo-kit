import { expect, test } from 'claude-code/testing'

import type { On, TurnCompleteInput } from 'claude-code'

import { world } from './world.test-helper'

const HANDOFF = '/proj/CLAUDE.local.md'

function turn(turnId: string, agentId?: string): TurnCompleteInput {
  const ended = { answer: 'done', durationMs: 10, isAborted: false, turnId, reason: 'answer' as const }

  return agentId === undefined ? ended : { ...ended, agentId }
}

// The engine beneath, outside a repository: a Write puts its content in the file, an Edit replaces its string.
function session(on: On, files: Record<string, string>) {
  const made = world(on, { files })
  on('tool.call', (_, e) => {
    if (e.tool === 'Write') {
      made.files[e.file_path] = e.content
    }
    if (e.tool === 'Edit') {
      made.files[e.file_path] = (made.files[e.file_path] ?? '').replace(e.old_string, e.new_string)
    }

    return { result: {} }
  })
  on('process.run', () => ({ value: { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }))
  on('prompt.submit', (_, e) => ({ text: e.text }))
  on('turn.complete', (_, e) => ({ text: e.answer }))

  return made
}

const MODEL_TEXT = '# Live state\n\n## Task\n\nThe owner: "keep building".\n'

// The kit rewrites the owner's handoff file, so a slip here loses the model's account with nothing said.
test('the facts go after the model\'s text at the end of the turn that wrote the file, a later handoff replaces them in place, and the model\'s text before and after them is never changed', async ($, on) => {
  const { files } = session(on, { [HANDOFF]: 'the old handoff\n' })

  await $.prompt.submit({ text: 'Keep building', wait: false, origin: { kind: 'composer' } })
  await $.tool.call({ tool: 'Write', file_path: HANDOFF, content: MODEL_TEXT })
  // Nothing is added while the turn runs.
  expect(files[HANDOFF]).toBe(MODEL_TEXT)
  await $.turn.complete(turn('t1'))

  const first = files[HANDOFF] ?? ''
  expect(first.startsWith(MODEL_TEXT)).toBe(true)
  const block = first.slice(MODEL_TEXT.length)
  expect(block).toMatch(/session-kit/)
  expect(block).toMatch(/Keep building/)

  // The model rewrites the file keeping the old facts in the middle, with its own text after them.
  const before = '# Live state\n\n## Task\n\nThe owner: "keep building, then stop".\n'
  const after = '\n## Next step\n\nStop here.\n'
  await $.tool.call({ tool: 'Write', file_path: HANDOFF, content: `${before}${block}${after}` })
  await $.turn.complete(turn('t2'))
  const second = files[HANDOFF] ?? ''
  expect(second.startsWith(before)).toBe(true)
  expect(second.endsWith(after)).toBe(true)
  expect(second.split('Keep building').length).toBe(2)

  // A turn that did not write the file leaves it alone, and so does a subagent's turn end.
  await $.tool.call({ tool: 'Write', file_path: '/proj/other.md', content: 'x' })
  await $.turn.complete(turn('t3'))
  await $.turn.complete(turn('t4', 'agent-1'))
  expect(files[HANDOFF]).toBe(second)

  // An Edit is a write of the file too, and a section the model cut short keeps every line it holds.
  files[HANDOFF] = `${before}<!-- session-kit facts -->\nhalf a section\n${after}`
  await $.tool.call({ tool: 'Edit', file_path: HANDOFF, old_string: 'Stop here.', new_string: 'Stop there.' })
  await $.turn.complete(turn('t5'))
  const third = files[HANDOFF] ?? ''
  expect(third.startsWith(`${before}<!-- session-kit facts -->\nhalf a section\n\n## Next step\n\nStop there.\n`)).toBe(true)
  expect(third.split('Keep building').length).toBe(2)
})
