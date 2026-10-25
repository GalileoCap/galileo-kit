// The checkout checks, in-process: on the first prompt of a context (a new
// conversation, or one just compacted or cleared), the model is told when
// `CLAUDE.local.md` is missing or older than the last commit, as context
// beside that prompt. At the end of a turn of the main loop, the person sees
// one dim line when the tree holds uncommitted changes or the handoff
// predates the last commit. Outside a git repository both stay silent. A hook
// that fails leaves the prompt and the turn as they were.
//
// The advice rides on `prompt.submit` and not on `prompt.context`, since a
// mod seated ahead of the kit by an organisation's policy answers
// `prompt.context` without passing it on, and lets `prompt.submit` through.

import type { EngineInterface, Register } from 'claude-code'

export const HANDOFF = 'CLAUDE.local.md'
export const HANDOFF_COMMAND = '/session-kit:handoff'

export type HandoffState = 'missing' | 'stale' | 'current'

// A repository's own config names no command git would run here: a `core.fsmonitor` set in `.git/config` is code.
const GIT = ['git', '-c', 'core.fsmonitor=false']

async function lastCommitMs($: EngineInterface, cwd: string): Promise<number | null> {
  const ran = await $.process.run([...GIT, 'log', '-1', '--format=%ct'], { cwd })
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
  const ran = await $.process.run([...GIT, 'status', '--porcelain'], { cwd })
  if (ran.exitCode !== 0) {
    return []
  }

  return ran.stdout.split('\n').filter((line) => line.trim() !== '')
}

export function handoffAdvice(state: HandoffState): string | null {
  switch (state) {
    case 'missing':
      return `session-kit: ${HANDOFF} is missing: run ${HANDOFF_COMMAND} init before working, so the next context starts from the files.`
    case 'stale':
      return `session-kit: ${HANDOFF} predates the last commit: read it knowing that, and run ${HANDOFF_COMMAND} at the next clear point.`
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
  // A prompt with words, a matcher since the engine takes one unmatched `prompt.submit` hook per module (context.tsx's).
  on('prompt.submit', { text: /\S/ }, async ($, e, next) => {
    // The engine has no figure for the window until its first response in it.
    if (e.command !== undefined || (await $.session.usage()).context.tokens !== undefined) {
      return next(e)
    }
    const advice = handoffAdvice(await handoffState($, await $.session.cwd()))
    if (advice === null) {
      return next(e)
    }

    return next({ ...e, context: [...(e.context ?? []), advice] })
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
