// The suppression warning, in-process: after an Edit or a Write that puts a
// suppression or a type escape into a source file (the noqa and ignore
// comments, the ts directives, the lint disables, the any casts), the model is told
// it needs the owner's approval and, once approved, a numbered row in the
// project's decisions file cited beside the marker, which
// `session-suppressions check` holds together. A marker an Edit only moves
// (already in the text it replaces) is not warned about again. Prose files
// are left alone, since a rule names the markers it bans. The names below
// are spelled in pieces so this file holds none of them whole. A hook that
// fails leaves the call as it ran.

import type { EngineInterface, Register } from 'claude-code'

export const DEFAULT_LEDGER = 'docs/decisions.md'
const PROSE = ['.md', '.mdx', '.txt', '.rst']

export const MARKERS: readonly { name: string; pattern: RegExp }[] = [
  { name: 'noqa', pattern: new RegExp('#' + String.raw`\s*(?:ruff:\s*)?` + 'noqa' + String.raw`\b`) },
  { name: 'type: ' + 'ignore', pattern: new RegExp('#' + String.raw`\s*type:\s*` + 'ignore' + String.raw`\b`) },
  { name: 'pyright: ' + 'ignore', pattern: new RegExp('#' + String.raw`\s*pyright:\s*` + 'ignore' + String.raw`\b`) },
  { name: '@ts-' + 'ignore', pattern: new RegExp('@ts-' + 'ignore' + String.raw`\b`) },
  { name: '@ts-' + 'expect-error', pattern: new RegExp('@ts-' + 'expect-error' + String.raw`\b`) },
  { name: 'eslint-' + 'disable', pattern: new RegExp('eslint-' + 'disable') },
  { name: 'oxlint-' + 'disable', pattern: new RegExp('oxlint-' + 'disable') },
  { name: 'biome-' + 'ignore', pattern: new RegExp('biome-' + 'ignore') },
  { name: 'as ' + 'any', pattern: new RegExp(String.raw`\bas\s+` + 'any' + String.raw`\b`) },
  { name: 'as unknown ' + 'as', pattern: new RegExp(String.raw`\bas\s+unknown\s+` + 'as' + String.raw`\b`) },
]

/** The markers `text` holds, by name, each once, in the order above. */
export function suppressionsIn(text: string): string[] {
  return MARKERS.filter(({ pattern }) => pattern.test(text)).map(({ name }) => name)
}

export function isProse(path: string): boolean {
  return PROSE.some((suffix) => path.toLowerCase().endsWith(suffix))
}

export function warning(names: readonly string[], ledger: string): string {
  return (
    `This edit writes a suppression (${names.join(', ')}). It needs the owner's approval: put the ` +
    'trade-off to them (refactor, suppress or re-scope) and, once approved, give it a numbered row in ' +
    `${ledger} and cite the row beside the marker. session-suppressions check holds the two together.`
  )
}

async function ledgerOf($: EngineInterface, cwd: string): Promise<string> {
  try {
    const parsed: unknown = JSON.parse(await $.fs.read(`${cwd}/.claude/claude-kit.json`))
    if (typeof parsed === 'object' && parsed !== null && 'suppressions' in parsed) {
      const settings = parsed.suppressions
      if (typeof settings === 'object' && settings !== null && 'ledger' in settings && typeof settings.ledger === 'string' && settings.ledger !== '') {
        return settings.ledger
      }
    }
  } catch {
    return DEFAULT_LEDGER
  }

  return DEFAULT_LEDGER
}

async function note($: EngineInterface, path: string, added: string, before: string): Promise<string | null> {
  if (isProse(path)) {
    return null
  }
  const was = new Set(suppressionsIn(before))
  const names = suppressionsIn(added).filter((name) => !was.has(name))

  return names.length === 0 ? null : warning(names, await ledgerOf($, await $.session.cwd()))
}

export const register: Register = (on) => {
  on('tool.call', { tool: 'Edit' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined) {
      return ran
    }
    const text = await note($, e.file_path, e.new_string, e.old_string)

    return text === null ? ran : { ...ran, context: [...(ran.context ?? []), text] }
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: 'Write' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined) {
      return ran
    }
    const text = await note($, e.file_path, e.content, '')

    return text === null ? ran : { ...ran, context: [...(ran.context ?? []), text] }
  }).catch(($, e, next) => next(e))
}
