import { expect, test } from 'claude-code/testing'

import { world } from './world.test-helper'

const LOG = '/var/tmp/t/claude-kit-last-test-sess-1.log'

test('a passing test run writes the command, cwd, stdout and stderr to the log and says nothing', async ($, on) => {
  const { files } = world(on, { tmpdir: '/var/tmp/t' })
  on('tool.call', () => ({ result: { stdout: '12 passed in 0.4s', stderr: 'a warning on stderr', interrupted: false } }))

  const ran = await $.tool.call({ tool: 'Bash', command: 'uv run pytest -q' })
  expect(ran.context).toBeUndefined()
  const log = files[LOG] ?? ''
  expect(log).toMatch(/Command: uv run pytest -q/)
  expect(log).toMatch(/Directory: \/proj/)
  expect(log).toMatch(/Result: passed/)
  expect(log).toMatch(/12 passed in 0\.4s/)
  expect(log).toMatch(/a warning on stderr/)
})

test('a failing test run writes its error output and says where, in one line', async ($, on) => {
  const { files } = world(on, { tmpdir: '/var/tmp/t' })
  const output = 'Exit code 1\nFAILED tests/test_a.py::test_b - assert 1 == 2\n1 failed'
  on('tool.call', () => ({ isError: true, result: output, text: output }))

  const ran = await $.tool.call({ tool: 'Bash', command: 'uv run pytest' })
  expect(ran.context?.length).toBe(1)
  expect(ran.context?.[0]).toBe(`The test run failed; its whole output is in ${LOG}.`)
  expect(files[LOG]).toMatch(/Result: failed/)
  expect(files[LOG]).toMatch(/FAILED tests\/test_a\.py::test_b/)
})

test('a project runner from .claude/claude-kit.json is a test run, and an ordinary command is not', async ($, on) => {
  const { files } = world(on, { tmpdir: '/var/tmp/t', files: { '/proj/.claude/claude-kit.json': '{"test_commands": ["scripts/test"]}' } })
  on('tool.call', () => ({ isError: true, result: '3 failed', text: '3 failed' }))

  const plain = await $.tool.call({ tool: 'Bash', command: 'ls -la && git status' })
  expect(plain.context).toBeUndefined()
  expect(files[LOG]).toBeUndefined()

  const run = await $.tool.call({ tool: 'Bash', command: 'scripts/test unit' })
  expect(run.context?.[0]).toMatch(/whole output is in/)
  expect(files[LOG]).toMatch(/3 failed/)
})

test('each run replaces the log whole, and the log goes to /tmp without TMPDIR', async ($, on) => {
  const { files } = world(on)
  let stdout = 'FAILED the-old-failure'
  on('tool.call', () => ({ result: { stdout, stderr: '', interrupted: false } }))

  await $.tool.call({ tool: 'Bash', command: 'pnpm test' })
  stdout = '5 passed'
  await $.tool.call({ tool: 'Bash', command: 'pnpm test' })
  const log = files['/tmp/claude-kit-last-test-sess-1.log'] ?? ''
  expect(log).toMatch(/5 passed/)
  expect(log).not.toMatch(/the-old-failure/)
})

test('a denied call writes no log', async ($, on) => {
  const { files } = world(on, { tmpdir: '/var/tmp/t' })
  on('tool.call', () => ({ deny: 'no' }))

  await $.tool.call({ tool: 'Bash', command: 'pytest -x' })
  expect(Object.keys(files)).toEqual([])
})
