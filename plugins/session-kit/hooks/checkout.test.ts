import { expect, test } from 'claude-code/testing'

import type { On } from 'claude-code'

import { world } from './world.test-helper'

type Repo = { commitSeconds: number | null; status: string }

function git(on: On, repo: Repo): string[] {
  const logged: string[] = []
  on('process.run', (_, e) => {
    if (repo.commitSeconds === null) {
      return { value: { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }
    }
    const stdout = e.argv[1] === 'log' ? `${repo.commitSeconds}\n` : repo.status

    return { value: { exitCode: 0, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('ui.log', (_, e) => {
    logged.push(e.text)

    return { value: undefined }
  })
  on('prompt.context', (_, e) => ({ blocks: e.blocks }))
  on('turn.complete', () => ({ text: '' }))

  return logged
}

function handoffWrittenAt(on: On, mtimeMs: number) {
  on('fs.stat', () => ({ value: { kind: 'file' as const, size: 1, mtimeMs, isLink: false } }))
}

const turn = { answer: '', durationMs: 0, isAborted: false, turnId: 't1', reason: 'answer' as const }

test('a missing handoff is named in the context at the start, with the init command', async ($, on) => {
  world(on, { files: {} })
  git(on, { commitSeconds: 1_700_000_000, status: '' })
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })

  const context = await $.prompt.context({ blocks: [{ name: 'claudeMd', text: 'rules' }] })
  expect(context.blocks.length).toBe(2)
  expect(context.blocks[1]?.name).toBe('session-kit:handoff')
  expect(context.blocks[1]?.text).toMatch(/CLAUDE\.local\.md is missing/)
  expect(context.blocks[1]?.text).toMatch(/\/session-kit:handoff init/)
})

test('a handoff older than the last commit is named as stale, and a current one adds nothing', async ($, on) => {
  world(on, { files: { '/proj/CLAUDE.local.md': 'state' } })
  git(on, { commitSeconds: 1_700_000_000, status: '' })
  handoffWrittenAt(on, 1_699_999_000_000)
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })

  const stale = await $.prompt.context({ blocks: [] })
  expect(stale.blocks[0]?.text).toMatch(/predates the last commit/)
})

test('a current handoff adds no block', async ($, on) => {
  world(on, { files: { '/proj/CLAUDE.local.md': 'state' } })
  git(on, { commitSeconds: 1_700_000_000, status: '' })
  handoffWrittenAt(on, 1_700_000_500_000)
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })

  expect((await $.prompt.context({ blocks: [] })).blocks).toEqual([])
})

test('the end of a turn names the uncommitted changes and the stale handoff in one dim line, and says nothing when clean', async ($, on) => {
  world(on, { files: { '/proj/CLAUDE.local.md': 'state' } })
  const repo: Repo = { commitSeconds: 1_700_000_000, status: ' M a.py\n?? b.py\n' }
  const logged = git(on, repo)
  handoffWrittenAt(on, 1_699_999_000_000)
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })

  await $.turn.complete(turn)
  expect(logged.length).toBe(1)
  expect(logged[0]).toMatch(/2 uncommitted changes/)
  expect(logged[0]).toMatch(/CLAUDE\.local\.md predates the last commit/)

  repo.status = ''
  await $.turn.complete({ ...turn, agentId: 'agent-1' })
  expect(logged.length).toBe(1)
})

test('a clean tree with a current handoff, and a directory that is no repository, log nothing', async ($, on) => {
  world(on, { files: { '/proj/CLAUDE.local.md': 'state' } })
  const repo: Repo = { commitSeconds: 1_700_000_000, status: '' }
  const logged = git(on, repo)
  handoffWrittenAt(on, 1_700_000_500_000)
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })

  await $.turn.complete(turn)
  expect(logged).toEqual([])

  repo.commitSeconds = null
  repo.status = ' M a.py\n'
  await $.turn.complete(turn)
  expect(logged).toEqual([])
  expect((await $.prompt.context({ blocks: [] })).blocks).toEqual([])
})
