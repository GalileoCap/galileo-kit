// The session registry (A91): each session keeps a record of itself in
// ~/.claude/session-kit/sessions/<id>.json, outside every project, for what
// counts the owner's load across sessions. The record says whether the
// session is working or waiting on the owner, since when, whether a question
// of its waits, and a beat written each minute while it lives, so a reader
// tells a closed session by its age. A clear ends the old session's record as
// the new one starts. It rides on context.tsx's hooks, since a hook of its own
// would put the kit's hooks line past the validator's cut. A write that fails
// is skipped: the registry is never the reason a turn goes wrong.

import type { EngineInterface, Timer } from 'claude-code'

type State = 'working' | 'waiting' | 'ended'

type SessionRecord = { id: string; cwd: string; state: State; since: number; beat: number; question: boolean }

const BEAT_MS = 60_000

let current: SessionRecord | null = null
let beating: Timer | null = null

async function write($: EngineInterface, record: SessionRecord): Promise<void> {
  try {
    const home = await $.env.get('HOME')
    if (home !== undefined) {
      await $.fs.write(`${home}/.claude/session-kit/sessions/${record.id}.json`, JSON.stringify(record))
    }
  } catch {
    // The next turn or beat writes it again.
  }
}

async function mark($: EngineInterface, state: State, question: boolean): Promise<void> {
  if (current === null) {
    return
  }
  const at = await $.clock.now()
  current = { ...current, state, question, since: state === current.state && question === current.question ? current.since : at, beat: at }
  await write($, current)
}

/** At session start: a cleared session's record ends, and this one's starts, waiting, beating each minute. */
export async function startRecord($: EngineInterface): Promise<void> {
  try {
    const id = await $.session.id()
    const at = await $.clock.now()
    if (current !== null && current.id !== id) {
      await write($, { ...current, state: 'ended', beat: at })
    }
    current = { id, cwd: await $.session.cwd(), state: 'waiting', since: at, beat: at, question: false }
    await write($, current)
    beating?.cancel()
    beating = $.clock.every(BEAT_MS, async () => {
      if (current !== null) {
        current = { ...current, beat: await $.clock.now() }
        await write($, current)
      }
    })
  } catch {
    // No record this session: nothing reads it inside the session.
  }
}

/** A main-loop turn started. */
export async function markWorking($: EngineInterface): Promise<void> {
  await mark($, 'working', false)
}

/** A main-loop turn ended, with or without a question waiting on the owner. */
export async function markWaiting($: EngineInterface, question: boolean): Promise<void> {
  await mark($, 'waiting', question)
}
