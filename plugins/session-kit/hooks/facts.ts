// The handoff's facts, in-process: when a main-loop turn that wrote
// `CLAUDE.local.md` ends (through the handoff command, the Skill tool, the
// chain or a plain edit), the kit adds a section it read itself after the
// model's text: the branch against its upstream, what is uncommitted, the
// last test run's verdict on this tree, the person's last prompt verbatim
// with the commits since it, and the commit ids the model's text names that
// the repository does not hold. The section sits between its own markers,
// and the next write of the file replaces it there. Every line outside the
// markers is the model's and is never changed, so the next context reads the
// model's account and the program's beside it.
//
// The kit registers this concern ahead of the context concern, so the facts
// are in the file before the chain asks for the compaction. A failure leaves
// the file as the model wrote it, with a dim line saying why.

import { atom, read } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import { gitOutput } from './checkout'
import { clip, clockTime } from './lines'
import { verdictOf } from './test_log'
import type { Verdict } from './test_log'

const lastPrompt = atom({ plugin: 'session-kit', key: 'lastPrompt' } as const, '')
const lastPromptAt = atom({ plugin: 'session-kit', key: 'lastPromptAt' } as const, 0)
const lastTest = atom({ plugin: 'session-kit', key: 'lastTest' } as const, null)

export const HANDOFF_NAME = 'CLAUDE.local.md'
export const FACTS_START = '<!-- session-kit facts -->'
export const FACTS_END = '<!-- end of session-kit facts -->'

// The section is loaded on every turn with the rest of the file, so each list is kept short.
const PROMPT_SHOWN = 600
const COMMITS_SHOWN = 6
const SUBJECT_SHOWN = 100
const PATHS_SHOWN = 10
const IDS_CHECKED = 20
const COMMAND_SHOWN = 80

type Branch = { name: string | null; head: string | null; upstream: string | null; ahead: number; behind: number }

type Status = { branch: Branch; paths: string[] }

type Facts = {
  at: number
  status: Status | null
  test: { verdict: Verdict; command: string; at: number } | null
  prompt: { text: string; at: number } | null
  commits: string[] | null
  missing: string[]
}

/** The branch header and the changed paths of `git status --porcelain=v2 --branch`, untracked ones marked. */
export function readStatus(out: string): Status {
  const branch: Branch = { name: null, head: null, upstream: null, ahead: 0, behind: 0 }
  const paths: string[] = []
  for (const line of out.split('\n')) {
    const fields = line.split(' ')
    switch (fields[0]) {
      case '#': {
        const value = fields.slice(2).join(' ')
        if (fields[1] === 'branch.oid') {
          branch.head = value === '(initial)' ? null : value.slice(0, 7)
        } else if (fields[1] === 'branch.head') {
          branch.name = value === '(detached)' ? null : value
        } else if (fields[1] === 'branch.upstream') {
          branch.upstream = value
        } else if (fields[1] === 'branch.ab') {
          branch.ahead = Math.abs(Number(fields[2] ?? 0)) || 0
          branch.behind = Math.abs(Number(fields[3] ?? 0)) || 0
        }
        break
      }
      case '1':
        paths.push(`\`${fields.slice(8).join(' ')}\``)
        break
      case '2':
        paths.push(`\`${(fields.slice(9).join(' ').split('\t')[0] ?? '')}\``)
        break
      case 'u':
        paths.push(`\`${fields.slice(10).join(' ')}\` (unmerged)`)
        break
      case '?':
        paths.push(`\`${fields.slice(1).join(' ')}\` (untracked)`)
        break
      default:
    }
  }

  return { branch, paths }
}

/** Where the kit's section starts and ends in the file: the last start marker and the first end after it; null when none is whole. */
function section(text: string): { start: number; end: number } | null {
  const start = text.lastIndexOf(FACTS_START)
  const end = start < 0 ? -1 : text.indexOf(FACTS_END, start)

  return end < 0 ? null : { start, end: end + FACTS_END.length }
}

/** The model's text: the file with the kit's section taken out. */
export function withoutFacts(text: string): string {
  const at = section(text)

  return at === null ? text : `${text.slice(0, at.start)}${text.slice(at.end)}`
}

/** The file with the section replaced where it stands, or added after the model's text; nothing else changes. */
export function withFacts(text: string, block: string): string {
  const at = section(text)
  if (at !== null) {
    return `${text.slice(0, at.start)}${block}${text.slice(at.end)}`
  }

  return `${text}${text.endsWith('\n') ? '\n' : '\n\n'}${block}\n`
}

/** The commit ids a text names: seven to forty hex characters with a digit and a letter, standing alone and not inside a path. */
export function namedIds(text: string): string[] {
  const found = new Set<string>()
  for (const m of text.matchAll(/(?<![\w/.-])[0-9a-f]{7,40}(?![\w/-]|\.\w)/g)) {
    if (/\d/.test(m[0]) && /[a-f]/.test(m[0])) {
      found.add(m[0])
    }
  }

  return [...found].slice(0, IDS_CHECKED)
}

function when(ms: number): string {
  const d = new Date(ms)
  const day = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

  return `${clockTime(d)} on ${day}`
}

function plural(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`
}

function branchLine(status: Status | null): string {
  if (status === null) {
    return 'git gave no status here: no repository, or git failed.'
  }
  const { name, head, upstream, ahead, behind } = status.branch
  const at = `${name === null ? 'Detached' : `On \`${name}\``} at ${head === null ? 'no commit yet' : `\`${head}\``}`
  if (upstream === null) {
    return `${at}, with no upstream.`
  }

  return `${at}, ${plural(ahead, 'commit', 'commits')} ahead of \`${upstream}\` and ${behind === 0 ? 'none' : behind} behind.`
}

function uncommittedLine(paths: string[]): string {
  if (paths.length === 0) {
    return 'Nothing uncommitted.'
  }
  const more = paths.length > PATHS_SHOWN ? `, and ${paths.length - PATHS_SHOWN} more` : ''

  return `${plural(paths.length, 'path', 'paths')} uncommitted: ${paths.slice(0, PATHS_SHOWN).join(', ')}${more}.`
}

function testLine(test: Facts['test']): string {
  if (test === null) {
    return 'No test run is recorded in this session.'
  }
  const run = `\`${clip(test.command.replace(/\s+/g, ' '), COMMAND_SHOWN)}\`, at ${when(test.at)}`
  switch (test.verdict) {
    case 'PASS':
      return `The last test run passed on this tree: ${run}.`
    case 'FAIL':
      return `The last test run failed, and none has passed since: ${run}.`
    case 'STALE':
      return `The last test run passed on a different tree, and files have changed since: ${run}.`
    case 'UNKNOWN':
      return `The last test run passed, on a tree git could not print: ${run}.`
  }
}

function promptLines(prompt: NonNullable<Facts['prompt']>): string[] {
  const shown = prompt.text.length > PROMPT_SHOWN ? prompt.text.slice(0, PROMPT_SHOWN) : prompt.text
  const quoted = shown.split('\n').map((line) => (line.trim() === '' ? '  >' : `  > ${line}`))
  if (shown.length < prompt.text.length) {
    quoted.push(`  > … (the first ${PROMPT_SHOWN} of ${prompt.text.length} characters)`)
  }

  return [`- The person's last prompt${prompt.at > 0 ? `, at ${when(prompt.at)}` : ''}, verbatim:`, ...quoted]
}

function commitLines(commits: string[] | null): string[] {
  if (commits === null) {
    return ['- git listed no commits since that prompt: it failed.']
  }
  if (commits.length === 0) {
    return ['- No commit since that prompt.']
  }
  const shown = commits.slice(0, COMMITS_SHOWN).map((line) => {
    const space = line.indexOf(' ')
    const id = space < 0 ? line : line.slice(0, space)

    return `  - \`${id}\` ${clip(space < 0 ? '' : line.slice(space + 1), SUBJECT_SHOWN)}`
  })
  const earlier = commits.length > COMMITS_SHOWN ? [`  - and ${commits.length - COMMITS_SHOWN} earlier.`] : []

  return [`- ${plural(commits.length, 'commit', 'commits')} since that prompt, newest first:`, ...shown, ...earlier]
}

export function factsBlock(f: Facts): string {
  const lines = [
    FACTS_START,
    '## Facts from git and the session',
    '',
    `Written by session-kit from git and its own records at ${when(f.at)}, when the turn that wrote this file ended. The model did not write this section, and the next write of the file replaces it.`,
    '',
    `- ${branchLine(f.status)}`,
  ]
  if (f.status !== null) {
    lines.push(`- ${uncommittedLine(f.status.paths)}`)
  }
  lines.push(`- ${testLine(f.test)}`)
  if (f.prompt === null) {
    lines.push('- No prompt of the person\'s is recorded in this session.')
  } else {
    lines.push(...promptLines(f.prompt))
    if (f.status !== null && f.prompt.at > 0) {
      lines.push(...commitLines(f.commits))
    }
  }
  if (f.missing.length > 0) {
    lines.push(`- Commit ids the text above names that this repository does not hold: ${f.missing.map((id) => `\`${id}\``).join(', ')}.`)
  }
  lines.push(FACTS_END)

  return lines.join('\n')
}

/** The ids git answers `missing` for; an id it holds, or one it finds ambiguous, is not listed. */
async function missingIds($: EngineInterface, dir: string, ids: string[]): Promise<string[]> {
  if (ids.length === 0) {
    return []
  }
  const out = await gitOutput($, dir, ['cat-file', '--batch-check'], `${ids.join('\n')}\n`)

  return (out ?? '')
    .split('\n')
    .filter((line) => line.endsWith(' missing'))
    .map((line) => line.slice(0, -' missing'.length))
}

async function gather($: EngineInterface, dir: string, own: string): Promise<Facts> {
  const at = await $.clock.now()
  const out = await gitOutput($, dir, ['status', '--porcelain=v2', '--branch'])
  const status = out === null ? null : readStatus(out)
  const last = await read($, lastTest)
  const test = last === null ? null : { verdict: await verdictOf($, dir, last), command: last.command, at: last.at }
  const said = await read($, lastPrompt)
  const saidAt = await read($, lastPromptAt)
  const prompt = said === '' ? null : { text: said, at: saidAt }
  const listed = status === null || prompt === null || prompt.at === 0 ? null : await gitOutput($, dir, ['log', `--since=@${Math.floor(prompt.at / 1000)}`, '--format=%h %s'])
  const commits = listed === null ? null : listed.split('\n').filter((line) => line.trim() !== '')
  const missing = status === null ? [] : await missingIds($, dir, namedIds(own))

  return { at, status, test, prompt, commits, missing }
}

async function writeFacts($: EngineInterface, path: string): Promise<void> {
  try {
    const text = await $.fs.read(path)
    const block = factsBlock(await gather($, path.slice(0, path.lastIndexOf('/')) || '/', withoutFacts(text)))
    await $.fs.write(path, withFacts(text, block))
  } catch (error) {
    $.ui.log(`session-kit: the facts were not added to ${HANDOFF_NAME} (${error instanceof Error ? error.message : String(error)}).`)
  }
}

function isHandoff(path: unknown): path is string {
  return typeof path === 'string' && path.endsWith(`/${HANDOFF_NAME}`)
}

// The handoff file a tool wrote during the turn under way; the turn's end adds the facts to it.
let written: string | null = null

export const register: Register = (on) => {
  // One registration per tool, so the validator's footprint names each.
  on('tool.call', { tool: 'Write' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny === undefined && ran.isError !== true && isHandoff(e.file_path)) {
      written = e.file_path
    }

    return ran
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: 'Edit' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny === undefined && ran.isError !== true && isHandoff(e.file_path)) {
      written = e.file_path
    }

    return ran
  }).catch(($, e, next) => next(e))

  on('turn.complete', { turnId: /./ }, async ($, e, next) => {
    if (e.agentId === undefined && written !== null) {
      const path = written
      written = null
      await writeFacts($, path)
    }

    return next(e)
  }).catch(($, e, next) => next(e))
}
