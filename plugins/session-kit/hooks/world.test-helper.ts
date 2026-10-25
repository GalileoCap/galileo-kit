// The engine beneath the step 3 modules, for their tests: a session with a
// working directory and an id, an environment, and a file system in memory.

import { mock } from 'claude-code/testing'

import type { On } from 'claude-code'

export type World = {
  files: Record<string, string>
}

export function world(on: On, options: { tmpdir?: string; cwd?: string; files?: Record<string, string> } = {}): World {
  const files = options.files ?? {}
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.usage', () => ({ value: { startedAt: 0, context: { tokens: 400_000, window: 1_000_000, percent: 40 }, rateLimits: [] } }))
  on('session.cwd', () => ({ value: options.cwd ?? '/proj' }))
  on('session.id', () => ({ value: 'sess-1' }))
  mock.clock(on, { now: 1_700_000_000_000 })
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

  return { files }
}
