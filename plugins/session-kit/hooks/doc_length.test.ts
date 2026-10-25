import { expect, test } from 'claude-code/testing'

import { world } from './world.test-helper'

const lines = (n: number) => Array.from({ length: n }, (_, i) => `line ${i + 1}`).join('\n') + '\n'

test('a docs markdown file past 1500 lines is named with its count after an Edit or a Write', async ($, on) => {
  world(on, { files: { '/proj/docs/big.md': lines(1501), '/proj/docs/fine.md': lines(1500) } })
  on('tool.call', () => ({ result: {} }))

  const edited = await $.tool.call({ tool: 'Edit', file_path: '/proj/docs/big.md', old_string: 'a', new_string: 'b' })
  expect(edited.context?.length).toBe(1)
  expect(edited.context?.[0]).toMatch(/\/proj\/docs\/big\.md/)
  expect(edited.context?.[0]).toMatch(/1501 lines/)
  expect(edited.context?.[0]).toMatch(/split/)

  const written = await $.tool.call({ tool: 'Write', file_path: '/proj/docs/big.md', content: 'x' })
  expect(written.context?.[0]).toMatch(/1501 lines/)

  const fine = await $.tool.call({ tool: 'Edit', file_path: '/proj/docs/fine.md', old_string: 'a', new_string: 'b' })
  expect(fine.context).toBeUndefined()
})

test('a file outside docs, a file that is not markdown, and a denied edit say nothing', async ($, on) => {
  world(on, { files: { '/proj/src/big.md': lines(2000), '/proj/docs/big.py': lines(2000), '/proj/docs/big.md': lines(2000) } })
  let deny = false
  on('tool.call', () => (deny ? { deny: 'no' } : { result: {} }))

  expect((await $.tool.call({ tool: 'Edit', file_path: '/proj/src/big.md', old_string: 'a', new_string: 'b' })).context).toBeUndefined()
  expect((await $.tool.call({ tool: 'Edit', file_path: '/proj/docs/big.py', old_string: 'a', new_string: 'b' })).context).toBeUndefined()
  deny = true
  expect((await $.tool.call({ tool: 'Edit', file_path: '/proj/docs/big.md', old_string: 'a', new_string: 'b' })).context).toBeUndefined()
})

test('the cap comes from the docLines option', { options: { docLines: 10 } }, async ($, on) => {
  world(on, { files: { '/proj/docs/a.md': lines(11) } })
  on('tool.call', () => ({ result: {} }))

  const ran = await $.tool.call({ tool: 'Edit', file_path: '/proj/docs/a.md', old_string: 'a', new_string: 'b' })
  expect(ran.context?.[0]).toMatch(/11 lines/)
})
