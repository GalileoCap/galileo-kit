import { type Engine, expect, test } from 'claude-code/testing'

import type { On } from 'claude-code'

import { world } from './world.test-helper'

const INDEX = [
  '# Intent index',
  '',
  '- [A20 One module per concern](A20-one-module-per-concern.md): decided 2026-10-25 (an action to validate)',
  '- [A24 The reference mod](A24-the-reference-mod.md): decided 2026-10-25 (behaviour)',
  '- [O18 Communication with the owner is clear](O18-communication.md): approved 2026-10-25',
  '',
].join('\n')

// The engine beneath draws the text it is handed.
function project(on: On) {
  world(on, { files: { '/proj/docs/intent/INDEX.md': INDEX } })
  on('fs.stat', () => ({ value: { kind: 'file' as const, size: 1, mtimeMs: 1, isLink: false } }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>{e.component === 'AssistantMessage' ? e.props.text : 'engine'}</Text>
  })
}

async function drawn($: Engine, text: string): Promise<string> {
  const ui = await $.ui.mount({ plugin: 'session-kit', component: 'AssistantMessage', surface: 'desktop', props: { text, isFirstOfReply: true } })
  const texts = await ui.findAll({ type: 'Text' })
  await ui.unmount()

  return texts.map((t) => t.text).join('')
}

// Kept past the build: a wrong or doubled name on screen reads as the model's own words, and nothing else would show it.
test('an id already named, in code, in a path, or unknown to the index is drawn as written', async ($, on) => {
  project(on)
  await $.session.start({ cwd: '/proj', surface: 'desktop', isInteractive: true })

  const text = [
    '`A20` (one module per concern) holds, and so does (`O18`, clear talk).',
    'See docs/intent/A24-the-reference-mod.md and A99.',
    '```',
    'O18 inside a fence',
    '```',
  ].join('\n')
  expect(await drawn($, text)).toBe(text)
})

test('a parenthesis after an id that does not hold its name still gets the name', async ($, on) => {
  project(on)
  await $.session.start({ cwd: '/proj', surface: 'desktop', isInteractive: true })

  expect(await drawn($, '`A24` (built today) works.')).toBe('`A24` (the reference mod) (built today) works.')
})
