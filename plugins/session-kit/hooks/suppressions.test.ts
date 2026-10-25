import { expect, test } from 'claude-code/testing'

import { world } from './world.test-helper'

// The markers are spelled in pieces so this file holds none of them whole.
const NOQA = '# ' + 'noqa: E501'
const TS_IGNORE = '// @ts-' + 'ignore'
const AS_ANY = 'x as ' + 'any'

test('an Edit or a Write that adds a suppression to a source file is told to justify it in place and index it', async ($, on) => {
  world(on, { files: {} })
  on('tool.call', () => ({ result: {} }))

  const edited = await $.tool.call({ tool: 'Edit', file_path: '/proj/a.py', old_string: 'x = f()', new_string: `x = f()  ${NOQA}` })
  expect(edited.context?.length).toBe(1)
  expect(edited.context?.[0]).toMatch(/writes a suppression \(noqa\)/)
  expect(edited.context?.[0]).toMatch(/on its line or the line above/)
  expect(edited.context?.[0]).toMatch(/docs\/suppressions\.md/)

  const written = await $.tool.call({ tool: 'Write', file_path: '/proj/b.ts', content: `${TS_IGNORE}\nconst y = ${AS_ANY}\n` })
  expect(written.context?.[0]).toMatch(new RegExp(String.raw`\(@ts-` + 'ignore, as ' + String.raw`any\)`))
})

test('a marker only moved by the edit, a marker in prose, a clean edit and a denied edit say nothing', async ($, on) => {
  world(on, { files: {} })
  let deny = false
  on('tool.call', () => (deny ? { deny: 'no' } : { result: {} }))

  const moved = await $.tool.call({ tool: 'Edit', file_path: '/proj/a.py', old_string: `x = f()  ${NOQA}`, new_string: `y = g()\nx = f()  ${NOQA}` })
  expect(moved.context).toBeUndefined()
  const prose = await $.tool.call({ tool: 'Write', file_path: '/proj/CLAUDE.md', content: `Never ${NOQA}.` })
  expect(prose.context).toBeUndefined()
  const clean = await $.tool.call({ tool: 'Edit', file_path: '/proj/a.py', old_string: 'a', new_string: 'b' })
  expect(clean.context).toBeUndefined()
  deny = true
  const denied = await $.tool.call({ tool: 'Write', file_path: '/proj/c.py', content: NOQA })
  expect(denied.context).toBeUndefined()
})

test('the index named in .claude/claude-kit.json is the one the warning names', async ($, on) => {
  world(on, { files: { '/proj/.claude/claude-kit.json': '{"suppressions": {"index": "docs/escapes.md"}}' } })
  on('tool.call', () => ({ result: {} }))

  const ran = await $.tool.call({ tool: 'Write', file_path: '/proj/a.py', content: NOQA })
  expect(ran.context?.[0]).toMatch(/docs\/escapes\.md/)
})
