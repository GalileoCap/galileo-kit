// The project's local-scratch/ (A109), where the kit writes the files no one
// commits: the test log and the chain file. The directory holds a .gitignore
// of `*`, so it ignores itself in a project whose own .gitignore lacks the
// line, and its files are neither uncommitted changes nor part of the tree a
// test run is stamped with.

import type { EngineInterface } from 'claude-code'

export function scratchDir(root: string): string {
  return `${root.replace(/\/+$/, '')}/local-scratch`
}

/** The path of a session's file in local-scratch/, its name the prefix and the session id. */
export function scratchPath(root: string, prefix: string, sessionId: string): string {
  const safe = sessionId.replace(/[^\w-]/g, '_') || 'session'

  return `${scratchDir(root)}/${prefix}-${safe}.log`
}

/** The session's file in local-scratch/ at the session's root, with the directory's .gitignore written first when it has none. */
export async function scratchFile($: EngineInterface, prefix: string): Promise<string> {
  const root = await $.session.root()
  const ignore = `${scratchDir(root)}/.gitignore`
  if (!(await $.fs.exists(ignore))) {
    await $.fs.write(ignore, '*\n')
  }

  return scratchPath(root, prefix, await $.session.id())
}
