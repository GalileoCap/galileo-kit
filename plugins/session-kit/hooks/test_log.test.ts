import { expect, test } from 'claude-code/testing'

import type { On } from 'claude-code'

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

test('a runner named only in quoted text, a heredoc or an argument is no test run, and one a launcher starts is', async ($, on) => {
  const { files } = world(on, { tmpdir: '/var/tmp/t', files: { '/proj/.claude/claude-kit.json': '{"test_commands": ["scripts/test", "scripts/check"]}' } })
  on('tool.call', () => ({ result: { stdout: '', stderr: '', interrupted: false } }))

  // Three of lane1's reads, each once logged as a passing run.
  for (const command of [
    'cd /proj/tagents-platform; grep -n "^def test\\|^async def test\\|^FORMS\\|^    pytest.param\\|id=" tests/test_knowledge_wording.py | head -40',
    "cd /proj && python3 -I - <<'EOF'\nfrom pathlib import Path\nprint('scripts/test all' in Path('docs/timing.md').read_text())\nEOF",
    "cd /proj/tagents-platform && wc -l scripts/test && grep -n -E '^\\s*(all|unit|landing)' scripts/test",
    "cd /proj; cat > docs/a.md <<'EOF'\nProven by `scripts/test` and `uv run pytest`.\nEOF",
  ]) {
    await $.tool.call({ tool: 'Bash', command })
  }
  expect(files[LOG]).toBeUndefined()

  await $.tool.call({ tool: 'Bash', command: 'cd /proj/tagents-platform && session-watched -- scripts/test stack > "$TMPDIR/stack.log" 2>&1' })
  expect(files[LOG]).toMatch(/Command: cd \/proj\/tagents-platform && session-watched -- scripts\/test stack/)

  await $.tool.call({ tool: 'Bash', command: 'command scripts/check .' })
  expect(files[LOG]).toMatch(/Command: command scripts\/check \.\n/)
})

test('a call a command hook refused is no test run, and the run before it stays the last', async ($, on) => {
  const { files } = world(on, { tmpdir: '/var/tmp/t' })
  const refusal = 'PreToolUse:Bash hook error: Write test output to a file (`&> log`) and search the file. Piping it inline throws the rest away and forces a rerun.'
  let answer: { result: { stdout: string; stderr: string; interrupted: boolean } } | { isError: true; result: string; text: string } = { result: { stdout: '4 passed', stderr: '', interrupted: false } }
  on('tool.call', () => answer)

  await $.tool.call({ tool: 'Bash', command: 'uv run pytest -q' })
  answer = { isError: true, result: refusal, text: refusal }
  const refused = await $.tool.call({ tool: 'Bash', command: 'uv run pytest -q | tail -5' })
  expect(refused.context).toBeUndefined()
  expect(files[LOG]).toMatch(/Command: uv run pytest -q\n/)
  expect(files[LOG]).toMatch(/Result: passed/)
})

test('a denied call writes no log', async ($, on) => {
  const { files } = world(on, { tmpdir: '/var/tmp/t' })
  on('tool.call', () => ({ deny: 'no' }))

  await $.tool.call({ tool: 'Bash', command: 'pytest -x' })
  expect(Object.keys(files)).toEqual([])
})

// The git beneath the stamp: an index of blob hashes and a working tree of the
// same, a path missing from the working tree deleted, one missing from the
// index untracked. A commit copies the working tree into the index.
type Tree = { inRepo: boolean; index: Record<string, string>; worktree: Record<string, string> }

function ok(stdout: string) {
  return { value: { exitCode: 0, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
}

function fatal(stderr: string) {
  return { value: { exitCode: 128, stdout: '', stderr, isStdoutTruncated: false, isStderrTruncated: false } }
}

function git(on: On, tree: Tree): { logged: string[] } {
  const logged: string[] = []
  on('process.run', (_, e) => {
    if (e.argv.slice(0, 3).join(' ') !== 'git -c core.fsmonitor=false') {
      return fatal(`unexpected argv ${e.argv.join(' ')}`)
    }
    if (!tree.inRepo) {
      return fatal('fatal: not a git repository')
    }
    const args = e.argv.slice(3).join(' ')
    if (args === 'ls-files -s -z') {
      return ok(Object.entries(tree.index).map(([p, h]) => `100644 ${h} 0\t${p}\0`).join(''))
    }
    if (args === 'diff-files -z') {
      const none = '0'.repeat(40)
      const records = Object.entries(tree.index).flatMap(([p, h]) => {
        const now = tree.worktree[p]
        if (now === undefined) {
          return [`:100644 000000 ${h} ${none} D\0${p}\0`]
        }

        return now === h ? [] : [`:100644 100644 ${h} ${none} M\0${p}\0`]
      })

      return ok(records.join(''))
    }
    if (args === 'ls-files --others --exclude-standard -z') {
      return ok(Object.keys(tree.worktree).filter((p) => !(p in tree.index)).map((p) => `${p}\0`).join(''))
    }
    if (args === 'hash-object --no-filters --stdin-paths') {
      const paths = (e.init?.stdin ?? '').split('\n').filter((p) => p !== '')
      const missing = paths.find((p) => tree.worktree[p] === undefined)
      if (missing !== undefined) {
        return fatal(`fatal: could not open '${missing}' for reading`)
      }

      return ok(paths.map((p) => `${tree.worktree[p]}\n`).join(''))
    }

    return fatal(`unexpected git ${args}`)
  })
  on('ui.log', (_, e) => {
    logged.push(e.text)

    return { value: undefined }
  })
  on('turn.complete', () => ({ text: '' }))

  return { logged }
}

const TURN = { answer: '', durationMs: 0, isAborted: false, turnId: 't1', reason: 'answer' as const }
const PASSED = { result: { stdout: '2 passed in 0.3s', stderr: '', interrupted: false } }
const COMMITTED = { result: { stdout: '[main 1a2b3c4] x', stderr: '', interrupted: false } }

test('a test run is stamped with the tree it ran on, and a commit or a turn\'s end is told when the last run failed or passed on a different tree', async ($, on) => {
  // The handoff is present, so the checkout's own turn-end line stays out of the way.
  const { files } = world(on, { tmpdir: '/var/tmp/t', files: { '/proj/CLAUDE.local.md': 'state' } })
  const tree: Tree = { inRepo: true, index: { 'a.py': 'h1', 'b.py': 'h2' }, worktree: { 'a.py': 'h1x', 'b.py': 'h2', 'c.py': 'h3' } }
  const { logged } = git(on, tree)
  let run: { result: { stdout: string; stderr: string; interrupted: boolean } } | { isError: true; result: string; text: string } = PASSED
  on('tool.call', (_, e) => (e.tool === 'Bash' && e.command.startsWith('git commit') ? COMMITTED : run))
  const pytest = async () => (await $.tool.call({ tool: 'Bash', command: 'uv run pytest -q' })).context
  const commit = async () => (await $.tool.call({ tool: 'Bash', command: 'git commit -m "x"' })).context
  const turnEnd = async () => {
    const before = logged.length
    await $.turn.complete(TURN)

    return logged.slice(before)
  }

  // A passing run on a dirty tree: the stamp is in the log, and a commit of that content is green.
  expect(await pytest()).toBeUndefined()
  expect(files[LOG]).toMatch(/^Tree: [0-9a-f]+$/m)
  expect(await commit()).toBeUndefined()
  tree.index = { ...tree.worktree }
  expect(await turnEnd()).toEqual([])

  // A tracked file changed since: the person and the model are told, and the edit undone restores the run.
  tree.worktree['a.py'] = 'h1y'
  const stale = await turnEnd()
  expect(stale.length).toBe(1)
  expect(stale[0]).toMatch(/^session-kit: the last test run \(uv run pytest -q, \d\d:\d\d\) passed on a different tree: files have changed since it ran\.$/)
  const told = await commit()
  expect(told?.length).toBe(1)
  expect(told?.[0]).toMatch(/^The last test run \(uv run pytest -q, at \d\d:\d\d\) passed on a different tree, and files have changed since it ran\. Run the tests again before this is delivered as green, or say they did not run on this tree\.$/)
  tree.worktree['a.py'] = 'h1x'
  expect(await turnEnd()).toEqual([])

  // An untracked file, its content and a deletion count as changes too.
  tree.worktree['d.py'] = 'h4'
  expect((await turnEnd()).length).toBe(1)
  expect(await pytest()).toBeUndefined()
  tree.worktree['d.py'] = 'h4b'
  expect((await turnEnd()).length).toBe(1)
  tree.worktree['d.py'] = 'h4'
  expect(await turnEnd()).toEqual([])
  delete tree.worktree['b.py']
  expect((await turnEnd()).length).toBe(1)
  tree.worktree['b.py'] = 'h2'
  expect(await turnEnd()).toEqual([])

  // A failed run is the last word until one passes, whatever the tree.
  const failure = 'Exit code 1\nFAILED tests/test_a.py::test_b - assert 1 == 2\n1 failed in 0.4s'
  run = { isError: true, result: failure, text: failure }
  expect((await pytest())?.length).toBe(1)
  const red = await turnEnd()
  expect(red.length).toBe(1)
  expect(red[0]).toMatch(/^session-kit: the last test run \(uv run pytest -q, \d\d:\d\d\) failed, and none has passed since\.$/)
  const redTold = await commit()
  expect(redTold?.[0]).toMatch(/^The last test run \(uv run pytest -q, at \d\d:\d\d\) failed, and none has passed since\. Run the tests again before this is delivered as green, or deliver it red with the evidence\.$/)
  run = PASSED
  expect(await pytest()).toBeUndefined()
  expect(await turnEnd()).toEqual([])

  // Outside a repository the run is not stamped, and nothing is said of it.
  tree.inRepo = false
  expect(await pytest()).toBeUndefined()
  expect(files[LOG]).toMatch(/^Tree: unknown$/m)
  expect(await commit()).toBeUndefined()
  expect(await turnEnd()).toEqual([])
  tree.inRepo = true
  tree.worktree['a.py'] = 'h1z'
  expect(await turnEnd()).toEqual([])
  await $.turn.complete({ ...TURN, agentId: 'agent-1' })
  expect(logged.length).toBe(stale.length + 3 + red.length)
})

test('the same test command failing with the same error after two edits names the rule, a rerun counts nothing, and a pass or a different error starts over', async ($, on) => {
  world(on, { tmpdir: '/var/tmp/t' })
  git(on, { inRepo: false, index: {}, worktree: {} })
  const S1 = 'Exit code 1\n    def test_b():\n>       assert 1 == 2\nE       assert 1 == 2\n\ntests/test_a.py:12: AssertionError\nFAILED tests/test_a.py::test_b - assert 1 == 2\n1 failed in 0.42s'
  const S2 = 'Exit code 1\n    def test_b():\n>       assert 1 == 2\nE       assert 1 == 2\n\ntests/test_a.py:14: AssertionError\n\x1b[31mFAILED\x1b[0m tests/test_a.py::test_b - assert 1 == 2\n1 failed in 0.51s'
  const T = 'Exit code 1\nFAILED tests/test_a.py::test_b - KeyError: \'x\'\n1 failed in 0.40s'
  let output = S1
  let editAnswer: { result: Record<string, unknown> } | { deny: string } = { result: { filePath: '/proj/a.py', oldString: 'a', newString: 'b', originalFile: null, structuredPatch: [], userModified: false, replaceAll: false } }
  on('tool.call', (_, e) => (e.tool === 'Bash' ? (output === '' ? PASSED : { isError: true, result: output, text: output }) : editAnswer))
  const pytest = async () => (await $.tool.call({ tool: 'Bash', command: 'uv run pytest' })).context ?? []
  const edit = () => $.tool.call({ tool: 'Edit', file_path: '/proj/a.py', old_string: 'a', new_string: 'b' })
  const RULE = /^session-kit: uv run pytest has failed with the same error after two edits\. A fix that has not worked after two tries stops and shows evidence: state what was tried and what happened, and let the owner or the next reader decide\.$/

  expect((await pytest()).length).toBe(1)
  await edit()
  expect((await pytest()).length).toBe(1)
  await edit()
  output = S2
  const named = await pytest()
  expect(named.length).toBe(2)
  expect(named[1]).toMatch(RULE)
  // A rerun with no edit between is no try, and the next edit's is named again.
  expect((await pytest()).length).toBe(1)
  await edit()
  expect((await pytest()).map((line) => RULE.test(line))).toEqual([false, true])

  // A different error starts the count over.
  await edit()
  output = T
  expect((await pytest()).length).toBe(1)
  await edit()
  expect((await pytest()).length).toBe(1)
  await edit()
  expect((await pytest()).length).toBe(2)

  // A pass starts it over, and a refused edit is no edit.
  output = ''
  expect(await pytest()).toEqual([])
  output = T
  expect((await pytest()).length).toBe(1)
  editAnswer = { deny: 'no' }
  await edit()
  expect((await pytest()).length).toBe(1)
  editAnswer = { result: { filePath: '/proj/a.py', oldString: 'a', newString: 'b', originalFile: null, structuredPatch: [], userModified: false, replaceAll: false } }
  await edit()
  expect((await pytest()).length).toBe(1)
  await edit()
  expect((await pytest()).length).toBe(2)
})

test('the stale line is said once while the run stays stale, and again once the tree has come back and left', async ($, on) => {
  world(on, { tmpdir: '/var/tmp/t', files: { '/proj/CLAUDE.local.md': 'state', '/proj/.claude/claude-kit.json': '{"test_commands": ["scripts/test"]}' } })
  const tree: Tree = { inRepo: true, index: { 'a.py': 'h1', 'b.py': 'h2' }, worktree: { 'a.py': 'h1', 'b.py': 'h2' } }
  const { logged } = git(on, tree)
  on('tool.call', () => PASSED)
  const turnEnd = async () => {
    const before = logged.length
    await $.turn.complete(TURN)

    return logged.slice(before)
  }

  // lane1's run, then edit after edit with a turn's end between: one line, where it said one at every turn.
  await $.tool.call({ tool: 'Bash', command: 'cd /proj && scripts/test unit tests/test_surface.py > /var/tmp/t/surface.log 2>&1' })
  tree.worktree['a.py'] = 'h1y'
  expect((await turnEnd()).length).toBe(1)
  expect(await turnEnd()).toEqual([])
  tree.worktree['b.py'] = 'h2y'
  expect(await turnEnd()).toEqual([])

  // Back to the tree the run passed on, and away again: said again.
  tree.worktree = { 'a.py': 'h1', 'b.py': 'h2' }
  expect(await turnEnd()).toEqual([])
  tree.worktree['a.py'] = 'h1z'
  expect((await turnEnd()).length).toBe(1)
  expect(await turnEnd()).toEqual([])
})
