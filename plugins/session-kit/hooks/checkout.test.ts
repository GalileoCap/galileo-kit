import { expect, test } from 'claude-code/testing'

import type { On } from 'claude-code'

import { world } from './world.test-helper'

type Repo = { commitSeconds: number | null; status: string }

// The engine beneath: git, the dim lines it draws, and the context each prompt reached it with.
function git(on: On, repo: Repo): { logged: string[]; sent: (readonly string[] | undefined)[]; ran: string[][] } {
  const logged: string[] = []
  const sent: (readonly string[] | undefined)[] = []
  const ran: string[][] = []
  on('process.run', (_, e) => {
    ran.push([...e.argv])
    if (repo.commitSeconds === null) {
      return { value: { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }
    }
    // The subcommand follows `git` and any `-c key=value` pair.
    const subcommand = e.argv[1] === '-c' ? e.argv[3] : e.argv[1]
    const stdout = subcommand === 'log' ? `${repo.commitSeconds}\n` : repo.status

    return { value: { exitCode: 0, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('ui.log', (_, e) => {
    logged.push(e.text)

    return { value: undefined }
  })
  on('prompt.submit', (_, e) => {
    sent.push(e.context)

    return { text: e.text, context: e.context }
  })
  on('prompt.context', (_, e) => ({ blocks: e.blocks }))
  on('turn.complete', () => ({ text: '' }))

  return { logged, sent, ran }
}

function handoffWrittenAt(on: On, mtimeMs: number) {
  on('fs.stat', () => ({ value: { kind: 'file' as const, size: 1, mtimeMs, isLink: false } }))
}

const turn = { answer: '', durationMs: 0, isAborted: false, turnId: 't1', reason: 'answer' as const }
const FRESH = { window: 1_000_000 }

function typed(text: string) {
  return { text, wait: false, origin: { kind: 'composer' as const } }
}

test('the first prompt of a fresh window carries the missing handoff\'s advice, with no prompt.context hook to reach', async ($, on) => {
  const w = world(on, { files: {} })
  w.context = FRESH
  const { sent } = git(on, { commitSeconds: 1_700_000_000, status: '' })
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })

  await $.prompt.submit(typed('hello'))
  expect(sent.length).toBe(1)
  expect(sent[0]?.length).toBe(1)
  expect(sent[0]?.[0]).toMatch(/CLAUDE\.local\.md is missing/)
  expect(sent[0]?.[0]).toMatch(/\/session-kit:handoff init/)
  // A mod seated ahead answers prompt.context without passing it on: the kit adds nothing there.
  expect((await $.prompt.context({ blocks: [] })).blocks).toEqual([])
})

test('a stale handoff is named on the first prompt of a window, and a prompt after its first response carries nothing', async ($, on) => {
  const w = world(on, { files: { '/proj/CLAUDE.local.md': 'state' } })
  w.context = FRESH
  const { sent } = git(on, { commitSeconds: 1_700_000_000, status: '' })
  handoffWrittenAt(on, 1_699_999_000_000)
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })

  await $.prompt.submit(typed('first'))
  expect(sent[0]?.[0]).toMatch(/predates the last commit/)

  w.context = { tokens: 30_000, window: 1_000_000, percent: 3 }
  await $.prompt.submit(typed('second'))
  expect(sent[1]).toBeUndefined()
})

test('a current handoff, and a slash command in a fresh window, carry nothing', async ($, on) => {
  const w = world(on, { files: { '/proj/CLAUDE.local.md': 'state' } })
  w.context = FRESH
  const { sent } = git(on, { commitSeconds: 1_700_000_000, status: '' })
  const writtenAt = { mtimeMs: 1_700_000_500_000 }
  on('fs.stat', () => ({ value: { kind: 'file' as const, size: 1, mtimeMs: writtenAt.mtimeMs, isLink: false } }))
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })

  await $.prompt.submit(typed('hello'))
  writtenAt.mtimeMs = 1_699_999_000_000
  await $.prompt.submit({ ...typed('/session-kit:handoff'), command: { name: 'session-kit:handoff', args: '' } })
  expect(sent).toEqual([undefined, undefined])
})

test('the end of a turn names the uncommitted changes and the stale handoff in one dim line, says nothing when clean, and runs git with the repository\'s own config unable to run code', async ($, on) => {
  world(on, { files: { '/proj/CLAUDE.local.md': 'state' } })
  const repo: Repo = { commitSeconds: 1_700_000_000, status: ' M a.py\n?? b.py\n' }
  const { logged, ran } = git(on, repo)
  handoffWrittenAt(on, 1_699_999_000_000)
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })

  await $.turn.complete(turn)
  expect(logged.length).toBe(1)
  expect(logged[0]).toMatch(/2 uncommitted changes/)
  expect(logged[0]).toMatch(/CLAUDE\.local\.md predates the last commit/)
  // A repository whose config names a fsmonitor command would run it at every turn end.
  expect(ran.map((argv) => argv.slice(0, 3).join(' '))).toEqual(['git -c core.fsmonitor=false', 'git -c core.fsmonitor=false'])

  repo.status = ''
  await $.turn.complete({ ...turn, agentId: 'agent-1' })
  expect(logged.length).toBe(1)
})

test('a clean tree with a current handoff, and a directory that is no repository, log nothing', async ($, on) => {
  const w = world(on, { files: { '/proj/CLAUDE.local.md': 'state' } })
  const repo: Repo = { commitSeconds: 1_700_000_000, status: '' }
  const { logged, sent } = git(on, repo)
  handoffWrittenAt(on, 1_700_000_500_000)
  await $.session.start({ cwd: '/proj', surface: 'terminal', isInteractive: true })

  await $.turn.complete(turn)
  expect(logged).toEqual([])

  repo.commitSeconds = null
  repo.status = ' M a.py\n'
  await $.turn.complete(turn)
  expect(logged).toEqual([])
  w.context = FRESH
  await $.prompt.submit(typed('hello'))
  expect(sent).toEqual([undefined])
})
