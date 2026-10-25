// The test log, in-process: after a Bash call that ran tests, the run's whole
// output is written to `<tempdir>/claude-kit-last-test-<session id>.log`,
// replaced each run, and a failed run tells the model in one line where it
// is. A command is a test run when it holds one of the builtin runners or a
// `test_commands` entry of the project's `.claude/claude-kit.json`. A hook
// that fails leaves the call as it ran.

import type { EngineInterface, Register } from 'claude-code'

export const BUILTIN_TEST_COMMANDS = [
  'pytest', 'vitest', 'jest', 'playwright test', 'cargo test', 'go test',
  'npm test', 'pnpm test', 'yarn test',
]

function escape(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function isTestRun(command: string, runners: readonly string[]): boolean {
  return runners.some((name) => new RegExp(`(?<![\\w/.-])${escape(name)}(?![\\w-])`).test(command))
}

export function logPath(tempdir: string, sessionId: string): string {
  const safe = sessionId.replace(/[^\w-]/g, '_') || 'session'

  return `${tempdir.replace(/\/+$/, '')}/claude-kit-last-test-${safe}.log`
}

async function projectRunners($: EngineInterface, cwd: string): Promise<string[]> {
  try {
    const parsed: unknown = JSON.parse(await $.fs.read(`${cwd}/.claude/claude-kit.json`))
    if (typeof parsed !== 'object' || parsed === null || !('test_commands' in parsed)) {
      return []
    }
    const listed = parsed.test_commands

    return Array.isArray(listed) ? listed.filter((c): c is string => typeof c === 'string' && c !== '') : []
  } catch {
    return []
  }
}

export const register: Register = (on) => {
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined) {
      return ran
    }
    const cwd = await $.session.cwd()
    const runners = [...BUILTIN_TEST_COMMANDS, ...(await projectRunners($, cwd))]
    if (!isTestRun(e.command, runners)) {
      return ran
    }
    const failed = ran.isError === true
    const output = failed
      ? ran.text ?? (typeof ran.result === 'string' ? ran.result : '')
      : `${ran.result.stdout}\n--- stderr ---\n${ran.result.stderr}`
    const path = logPath((await $.env.get('TMPDIR')) ?? '/tmp', await $.session.id())
    const when = new Date(await $.clock.now()).toISOString()
    await $.fs.write(
      path,
      `--- ${when} ---\nDirectory: ${cwd}\nCommand: ${e.command}\n` +
        `Result: ${failed ? 'failed' : 'passed'}\n--- output ---\n${output}\n`,
    )
    if (!failed) {
      return ran
    }

    return { ...ran, context: [...(ran.context ?? []), `The test run failed; its whole output is in ${path}.`] }
  }).catch(($, e, next) => next(e))
}
