// The test log, in-process: after a Bash call that ran tests, the run's whole
// output is written to `<tempdir>/claude-kit-last-test-<session id>.log`,
// replaced each run, and a failed run tells the model in one line where it
// is. A command is a test run when one of the builtin runners or a
// `test_commands` entry of the project's `.claude/claude-kit.json` starts a
// command segment, read as the guard reads it: quoted text and heredoc bodies
// do not count. A call a command hook refused never ran, and is no run.
//
// Each run is stamped with the working tree it ran on: a fingerprint of the
// content of every tracked and untracked file, read through git, which a
// commit of the same content leaves unchanged. The last run is read back as
// PASS, FAIL (it failed, and none has passed since), STALE (it passed, and
// files have changed since) or UNKNOWN (no run, or no fingerprint). At a
// `git commit` the model is told of a FAIL or a STALE, and at the end of a
// main-loop turn the person sees one dim line for either, a STALE once until
// the tree comes back to the run's, so "never deliver red" rests on a record
// a program wrote.
//
// The same test command failing with the same error after an edit is a try
// at a fix, and the second failed try names the two-tries rule to the model.
// The error's signature is its failure lines, or the whole output, with
// colour, timings and addresses taken out. A rerun with no edit between is
// no try, a different error or a pass starts the count over.
//
// A hook that fails leaves the call as it ran.

import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, ToolCallResult } from 'claude-code'

import type { TestRetry, TestRun } from '../types'
import { gitOutput } from './checkout'
import { clockTime } from './lines'

export const BUILTIN_TEST_COMMANDS = [
  'pytest', 'vitest', 'jest', 'playwright test', 'cargo test', 'go test',
  'npm test', 'pnpm test', 'yarn test',
]

const lastTest = atom({ plugin: 'session-kit', key: 'lastTest' } as const, null)
const testRetry = atom({ plugin: 'session-kit', key: 'testRetry' } as const, null)

// More changed or untracked files than this and the tree is not stamped: hashing them all would hold the call.
const STAMP_FILES_MAX = 1000
const COMMAND_SHOWN = 80
const TRIES_NAMED = 2

export type Verdict = 'PASS' | 'FAIL' | 'STALE' | 'UNKNOWN'

function escape(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// The guard's reading of a command (hooks/guard.py), so the two agree on what a test run is.
const START = '(?:^|[;&|(`])\\s*'
const LAUNCHER = '(?:uv\\s+run|poetry\\s+run|pipenv\\s+run|npx|pnpm\\s+exec|yarn\\s+run|python3?\\s+-m|env|time|nice|session-watched)'
const HEREDOC = /<<-?\s*(['"]?)(\w+)\1[^\n]*\n[\s\S]*?\n\s*\2\s*(?=\n|$)/g
const SINGLE_QUOTED = /'[^']*'/g
const DOUBLE_QUOTED = /"(?:[^"\\]|\\.)*"/g
const RUNS = /\$\(|`/

/** The command as the shell runs it: heredoc bodies and quoted text blanked, except one holding a substitution. */
export function bare(command: string): string {
  const unlessItRuns = (blank: string) => (text: string) => (RUNS.test(text) ? text : blank)

  return command
    .replace(HEREDOC, unlessItRuns(' '))
    .replace(SINGLE_QUOTED, "''")
    .replace(DOUBLE_QUOTED, unlessItRuns('""'))
}

/** A runner where a command segment starts, behind a launcher and its words, or a path, or neither. */
export function isTestRun(command: string, runners: readonly string[]): boolean {
  const names = runners.map(escape).join('|')
  const start = new RegExp(`${START}(?:${LAUNCHER}(?:\\s+\\S+)*?\\s+)?(?:\\S*/)?(?:${names})(?![\\w.-])`)

  return runners.length > 0 && start.test(bare(command))
}

/** The engine's words for a call a command hook refused before it ran. */
function refusedByHook(ran: ToolCallResult): boolean {
  const text = ran.text ?? (typeof ran.result === 'string' ? ran.result : '')

  return ran.isError === true && /^PreToolUse(?::\w+)? hook error: /.test(text)
}

/** A `git commit` where a command segment starts, behind git's own `-c` pairs and flags. */
export function isCommit(command: string): boolean {
  return /(?:^|[;&|(]\s*)git\s+(?:-[cC]\s+\S+\s+|-\S+\s+)*commit(?![\w-])/.test(command)
}

export function logPath(tempdir: string, sessionId: string): string {
  const safe = sessionId.replace(/[^\w-]/g, '_') || 'session'

  return `${tempdir.replace(/\/+$/, '')}/claude-kit-last-test-${safe}.log`
}

/** FNV-1a over the text under two seeds, sixteen hex characters: tells two texts apart, and is no secret. */
export function fingerprint(text: string): string {
  return [0, 0x9e3779b9]
    .map((seed) => {
      let h = (0x811c9dc5 ^ seed) >>> 0
      for (let i = 0; i < text.length; i += 1) {
        h = Math.imul(h ^ text.charCodeAt(i), 0x01000193) >>> 0
      }

      return h.toString(16).padStart(8, '0')
    })
    .join('')
}

const FAILURE_LINE = /^\s*(?:FAILED|ERROR|FAIL\b|--- FAIL|✕|×|✖|✗|not ok\b)|\.\.\. FAILED\s*$/

/** What a failure is, once colour, timings and addresses are out: its failure lines, or all of it when no line is one. */
export function errorSignature(output: string): string {
  const lines = output
    .replace(/\x1b\[[0-9;]*[A-Za-z]/g, '')
    .replace(/\r/g, '')
    .replace(/\b\d+(?:\.\d+)?\s?(?:ms|µs|us|s)\b/g, '<t>')
    .replace(/0x[0-9a-fA-F]+/g, '<addr>')
    .split('\n')
    .map((line) => line.trimEnd())
    .filter((line) => line !== '')
  const failures = lines.filter((line) => FAILURE_LINE.test(line))

  return fingerprint((failures.length > 0 ? failures : lines).join('\n'))
}

function shortCommand(command: string): string {
  const flat = command.replace(/\s+/g, ' ').trim()

  return flat.length > COMMAND_SHOWN ? `${flat.slice(0, COMMAND_SHOWN - 1)}…` : flat
}

export function verdict(last: TestRun | null, treeNow: string | null): Verdict {
  if (last === null) {
    return 'UNKNOWN'
  }
  if (!last.passed) {
    return 'FAIL'
  }
  if (last.tree === null || treeNow === null) {
    return 'UNKNOWN'
  }

  return last.tree === treeNow ? 'PASS' : 'STALE'
}

/** What the model reads at a commit: a run that failed or went stale is named with what to do. */
export function verdictContext(v: Verdict, last: TestRun): string | null {
  const run = `${shortCommand(last.command)}, at ${clockTime(new Date(last.at))}`
  switch (v) {
    case 'FAIL':
      return `The last test run (${run}) failed, and none has passed since. Run the tests again before this is delivered as green, or deliver it red with the evidence.`
    case 'STALE':
      return `The last test run (${run}) passed on a different tree, and files have changed since it ran. Run the tests again before this is delivered as green, or say they did not run on this tree.`
    default:
      return null
  }
}

/** The person's dim line at the end of a turn, for the same two verdicts. */
export function verdictLine(v: Verdict, last: TestRun): string | null {
  const run = `${shortCommand(last.command)}, ${clockTime(new Date(last.at))}`
  switch (v) {
    case 'FAIL':
      return `session-kit: the last test run (${run}) failed, and none has passed since.`
    case 'STALE':
      return `session-kit: the last test run (${run}) passed on a different tree: files have changed since it ran.`
    default:
      return null
  }
}

export function twoTriesContext(command: string): string {
  return (
    `session-kit: ${shortCommand(command)} has failed with the same error after two edits. ` +
    'A fix that has not worked after two tries stops and shows evidence: state what was ' +
    'tried and what happened, and let the owner or the next reader decide.'
  )
}

/**
 * A fingerprint of the working tree's content: the index's blob hashes, with
 * the files changed since hashed afresh, the deleted ones out and the
 * untracked ones in, so a commit of the same content gives the same print.
 * Null where git cannot say: no repository, a merge under way, an entry that
 * is no file, or too many files to hash.
 */
export async function treeFingerprint($: EngineInterface, cwd: string): Promise<string | null> {
  const index = await gitOutput($, cwd, ['ls-files', '-s', '-z'])
  const changed = await gitOutput($, cwd, ['diff-files', '-z'])
  const others = await gitOutput($, cwd, ['ls-files', '--others', '--exclude-standard', '-z'])
  if (index === null || changed === null || others === null) {
    return null
  }
  const entries = new Map<string, string>()
  for (const record of index.split('\0')) {
    if (record === '') {
      continue
    }
    const entry = /^(\d{6}) (\S+) (\d)\t(.+)$/s.exec(record)
    if (entry === null || entry[3] !== '0') {
      return null
    }
    entries.set(entry[4] ?? '', entry[2] ?? '')
  }
  const toHash: string[] = []
  const fields = changed.split('\0')
  for (let i = 0; i + 1 < fields.length; i += 2) {
    const head = /^:\d{6} (\d{6}) \S+ \S+ ([A-Z])\d*$/.exec(fields[i] ?? '')
    const path = fields[i + 1] ?? ''
    if (head === null) {
      return null
    }
    if (head[2] === 'D') {
      entries.delete(path)
    } else if (head[2] === 'M' || head[2] === 'T') {
      toHash.push(path)
    } else {
      return null
    }
  }
  toHash.push(...others.split('\0').filter((path) => path !== ''))
  if (toHash.length > STAMP_FILES_MAX || toHash.some((path) => path.includes('\n'))) {
    return null
  }
  if (toHash.length > 0) {
    const hashed = await gitOutput($, cwd, ['hash-object', '--no-filters', '--stdin-paths'], `${toHash.join('\n')}\n`)
    const hashes = hashed?.split('\n').filter((line) => line !== '') ?? []
    if (hashes.length !== toHash.length) {
      return null
    }
    toHash.forEach((path, i) => entries.set(path, hashes[i] ?? ''))
  }
  const lines = [...entries].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)).map(([path, hash]) => `${hash} ${path}`)

  return fingerprint(lines.join('\n'))
}

/** The last run's verdict now: a failure needs no git, and a run with no stamp stays unknown. */
export async function verdictOf($: EngineInterface, cwd: string, last: TestRun): Promise<Verdict> {
  if (!last.passed || last.tree === null) {
    return verdict(last, null)
  }

  return verdict(last, await treeFingerprint($, cwd))
}

async function withVerdict($: EngineInterface, cwd: string, ran: ToolCallResult): Promise<ToolCallResult> {
  const last = await read($, lastTest)
  if (last === null || ran.deny !== undefined) {
    return ran
  }
  const text = verdictContext(await verdictOf($, cwd, last), last)

  return text === null ? ran : { ...ran, context: [...(ran.context ?? []), text] }
}

/** Counts the run against the two-tries rule, and names the rule at the second failed try after an edit. */
async function noteRun($: EngineInterface, command: string, failed: boolean, output: string): Promise<string | null> {
  if (!failed) {
    await update($, testRetry, () => null)

    return null
  }
  const signature = errorSignature(output)
  const open = await read($, testRetry)
  if (open === null || open.command !== command || open.signature !== signature) {
    await update($, testRetry, () => ({ command, signature, tries: 0, edited: false }))

    return null
  }
  if (!open.edited) {
    return null
  }
  const tries = open.tries + 1
  await update($, testRetry, () => ({ ...open, tries, edited: false }))

  return tries >= TRIES_NAMED ? twoTriesContext(command) : null
}

async function markEdited($: EngineInterface): Promise<void> {
  const open = await read($, testRetry)
  if (open !== null && !open.edited) {
    await update($, testRetry, () => ({ ...open, edited: true }))
  }
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
    if (ran.deny !== undefined || refusedByHook(ran)) {
      return ran
    }
    const cwd = await $.session.cwd()
    const runners = [...BUILTIN_TEST_COMMANDS, ...(await projectRunners($, cwd))]
    if (!isTestRun(e.command, runners)) {
      return isCommit(e.command) ? withVerdict($, cwd, ran) : ran
    }
    const failed = ran.isError === true
    const output = failed
      ? ran.text ?? (typeof ran.result === 'string' ? ran.result : '')
      : `${ran.result.stdout}\n--- stderr ---\n${ran.result.stderr}`
    const path = logPath((await $.env.get('TMPDIR')) ?? '/tmp', await $.session.id())
    const at = await $.clock.now()
    const tree = await treeFingerprint($, cwd)
    await $.fs.write(
      path,
      `--- ${new Date(at).toISOString()} ---\nDirectory: ${cwd}\nCommand: ${e.command}\n` +
        `Result: ${failed ? 'failed' : 'passed'}\nTree: ${tree ?? 'unknown'}\n--- output ---\n${output}\n`,
    )
    await update($, lastTest, () => ({ command: e.command, at, passed: !failed, tree }))
    const named = await noteRun($, e.command, failed, output)
    if (!failed) {
      return ran
    }
    const added = [`The test run failed; its whole output is in ${path}.`, ...(named === null ? [] : [named])]

    return { ...ran, context: [...(ran.context ?? []), ...added] }
  }).catch(($, e, next) => next(e))

  // An edit that landed is a try at a fix, for the failure under way. One registration per tool, so the validator's footprint names each.
  on('tool.call', { tool: 'Edit' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny === undefined && ran.isError !== true) {
      await markEdited($)
    }

    return ran
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: 'Write' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny === undefined && ran.isError !== true) {
      await markEdited($)
    }

    return ran
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: 'NotebookEdit' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny === undefined && ran.isError !== true) {
      await markEdited($)
    }

    return ran
  }).catch(($, e, next) => next(e))

  on('turn.complete', { reason: 'answer' }, async ($, e, next) => {
    const done = await next(e)
    if (e.agentId !== undefined) {
      return done
    }
    const last = await read($, lastTest)
    if (last === null) {
      return done
    }
    // A stale run is said once, and again only after the tree has come back to the run's.
    const v = await verdictOf($, await $.session.cwd(), last)
    const line = verdictLine(v, last)
    if (line !== null && !(v === 'STALE' && last.staleShown === true)) {
      $.ui.log(line)
    }
    if ((v === 'STALE') !== (last.staleShown === true)) {
      await update($, lastTest, (run) => (run === null ? null : { ...run, staleShown: v === 'STALE' }))
    }

    return done
  }).catch(($, e, next) => next(e))
}
