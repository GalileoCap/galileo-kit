// The engine beneath the in-process modules, for their tests: a session with
// a working directory, an id and a context window, a clock, an environment,
// and a file system in memory. A test changes `context` to stand for a fresh
// window, and moves the clock through `clock`.

import { mock } from 'claude-code/testing'

import type { On, SessionContextUsage } from 'claude-code'

export type World = {
  files: Record<string, string>
  context: SessionContextUsage
  clock: ReturnType<typeof mock.clock>
}

export function world(on: On, options: { tmpdir?: string; cwd?: string; files?: Record<string, string> } = {}): World {
  const files = options.files ?? {}
  const clock = mock.clock(on, { now: 1_700_000_000_000 })
  const made: World = { files, context: { tokens: 100_000, window: 1_000_000, percent: 10 }, clock }
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.usage', () => ({ value: { startedAt: 0, context: made.context, rateLimits: [] } }))
  on('session.cwd', () => ({ value: options.cwd ?? '/proj' }))
  on('session.id', () => ({ value: 'sess-1' }))
  mock.env(on, options.tmpdir === undefined ? {} : { TMPDIR: options.tmpdir })
  on('fs.read', (_, e) => {
    const text = files[e.path]
    if (text === undefined) {
      throw new Error(`ENOENT: ${e.path}`)
    }

    return { value: text }
  })
  on('fs.write', (_, e) => {
    files[e.path] = e.text

    return { value: undefined }
  })
  on('fs.exists', (_, e) => ({ value: e.path in files }))

  return made
}
