// The session registry (A91): each session keeps a record of itself in
// ~/.claude/session-kit/sessions/<id>.json, outside every project, for what
// counts the owner's load across sessions. The record says whether the
// session is working or waiting on the owner, since when, whether a question
// of its waits, when its last main-loop turn ended, and a beat written each
// minute while it lives, so a reader tells a closed session by its age. A clear ends the old session's record as
// the new one starts. It rides on context.tsx's hooks, since a hook of its own
// would put the kit's hooks line past the validator's cut. A write that fails
// is skipped: the registry is never the reason a turn goes wrong. A sidechat,
// the desktop's btw opened beside a session, says so in its record, read from
// the desktop's own record of the session, so the owner's load leaves it out.

import type { EngineInterface, Timer } from 'claude-code'

type State = 'working' | 'waiting' | 'ended'

/** A session's record; `turnEnded` is 0 before its first main-loop turn ends, and `side` is true for a sidechat. */
export type SessionRecord = { id: string; cwd: string; state: State; since: number; beat: number; question: boolean; turnEnded: number; side?: boolean }

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
  const since = state === current.state && question === current.question ? current.since : at
  current = { ...current, state, question, since, beat: at, turnEnded: state === 'waiting' ? at : current.turnEnded }
  await write($, current)
}

/**
 * Where the desktop keeps its record of this session, from the variables it
 * sets: its host session id, under the account and organization the session
 * runs as. Null outside the desktop.
 */
export async function desktopRecordPath($: EngineInterface): Promise<string | null> {
  const home = await $.env.get('HOME')
  const host = await $.env.get('CLAUDE_CODE_HOST_SESSION_ID')
  const account = await $.env.get('CLAUDE_CODE_ACCOUNT_UUID')
  const org = await $.env.get('CLAUDE_CODE_ORGANIZATION_UUID')

  return home === undefined || host === undefined || account === undefined || org === undefined ? null : `${home}/Library/Application Support/Claude/claude-code-sessions/${account}/${org}/${host}.json`
}

/**
 * Whether the desktop's record of the session, its text, says it opened the
 * session as a sidechat (`spawnedFrom.btw`). False for no text, or for a
 * record whose shape changed, so a sidechat then counts like every session.
 */
function isSidechat(desktop: string): boolean {
  try {
    const record = JSON.parse(desktop) as { spawnedFrom?: { btw?: unknown } } | null // The desktop's file, read for this one field.

    return record?.spawnedFrom?.btw === true
  } catch {
    return false
  }
}

/** At session start: a cleared session's record ends, and this one's starts, waiting, beating each minute; `desktop` is the desktop's record of it, empty when there is none. */
export async function startRecord($: EngineInterface, desktop: string): Promise<void> {
  try {
    const id = await $.session.id()
    const at = await $.clock.now()
    if (current !== null && current.id !== id) {
      await write($, { ...current, state: 'ended', beat: at })
    }
    current = { id, cwd: await $.session.cwd(), state: 'waiting', since: at, beat: at, question: false, turnEnded: 0, side: isSidechat(desktop) }
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
