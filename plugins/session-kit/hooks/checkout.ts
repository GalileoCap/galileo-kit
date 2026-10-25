// The checkout checks, in-process: at the start of a conversation and after
// a compaction, the model is told when `CLAUDE.local.md` is missing or older
// than the last commit, through a context block beside the instruction files.
// At the end of a turn of the main loop, the person sees one dim line when
// the tree holds uncommitted changes or the handoff predates the last commit.
// Outside a git repository both stay silent. A hook that fails leaves the
// conversation and the turn as they were.

import type { EngineInterface, Register } from 'claude-code'

export const HANDOFF = 'CLAUDE.local.md'
export const HANDOFF_COMMAND = '/session-kit:handoff'
const BLOCK = 'session-kit:handoff'

export type HandoffState = 'missing' | 'stale' | 'current'

async function lastCommitMs($: EngineInterface, cwd: string): Promise<number | null> {
  const ran = await $.process.run(['git', 'log', '-1', '--format=%ct'], { cwd })
  const seconds = Number(ran.stdout.trim())

  return ran.exitCode === 0 && Number.isFinite(seconds) && seconds > 0 ? seconds * 1000 : null
}

export async function handoffState($: EngineInterface, cwd: string): Promise<HandoffState> {
  const path = `${cwd}/${HANDOFF}`
  if (!(await $.fs.exists(path))) {
    return 'missing'
  }
  const committed = await lastCommitMs($, cwd)
  if (committed === null) {
    return 'current'
  }
  const written = (await $.fs.stat(path)).mtimeMs

  return written < committed ? 'stale' : 'current'
}

/** The paths `git status` lists, uncommitted; empty outside a repository. */
export async function uncommitted($: EngineInterface, cwd: string): Promise<string[]> {
  const ran = await $.process.run(['git', 'status', '--porcelain'], { cwd })
  if (ran.exitCode !== 0) {
    return []
  }

  return ran.stdout.split('\n').filter((line) => line.trim() !== '')
}

export function handoffAdvice(state: HandoffState): string | null {
  switch (state) {
    case 'missing':
      return `${HANDOFF} is missing: run ${HANDOFF_COMMAND} init before working, so the next context starts from the files.`
    case 'stale':
      return `${HANDOFF} predates the last commit: read it knowing that, and run ${HANDOFF_COMMAND} at the next clear point.`
    case 'current':
      return null
  }
}

export function turnEndLine(changes: number, state: HandoffState): string | null {
  const parts: string[] = []
  if (changes > 0) {
    parts.push(`${changes} uncommitted ${changes === 1 ? 'change' : 'changes'} at the end of the turn`)
  }
  if (state === 'stale') {
    parts.push(`${HANDOFF} predates the last commit (${HANDOFF_COMMAND})`)
  } else if (state === 'missing') {
    parts.push(`${HANDOFF} is missing (${HANDOFF_COMMAND} init)`)
  }

  return parts.length === 0 ? null : `session-kit: ${parts.join('. ')}.`
}

export const register: Register = (on) => {
  on('prompt.context', async ($, e, next) => {
    const composed = await next(e)
    const advice = handoffAdvice(await handoffState($, await $.session.cwd()))
    if (advice === null) {
      return composed
    }

    return { ...composed, blocks: [...composed.blocks, { name: BLOCK, text: advice }] }
  }).catch(($, e, next) => next(e))

  on('turn.complete', { reason: 'answer' }, async ($, e, next) => {
    const done = await next(e)
    if (e.agentId !== undefined) {
      return done
    }
    const cwd = await $.session.cwd()
    const line = turnEndLine((await uncommitted($, cwd)).length, await handoffState($, cwd))
    if (line !== null) {
      $.ui.log(line)
    }

    return done
  }).catch(($, e, next) => next(e))
}
