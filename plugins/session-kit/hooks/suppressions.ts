// The suppression warning, in-process: after an Edit or a Write that puts a
// suppression or a type escape into a source file (the noqa and ignore
// comments, the ts directives, the lint disables, the any casts), the model is told
// to write its reason beside it, on its line or the line above, and to
// regenerate the index the owner reviews, which `session-suppressions check`
// holds together. A marker an Edit only moves
// (already in the text it replaces) is not warned about again. Prose files
// are left alone, since a rule names the markers it bans. The names below
// are spelled in pieces so this file holds none of them whole. A hook that
// fails leaves the call as it ran.

import type { EngineInterface, Register } from 'claude-code'

export const DEFAULT_INDEX = 'docs/suppressions.md'
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

export function warning(names: readonly string[], index: string): string {
  return (
    `This edit writes a suppression (${names.join(', ')}). Write its reason beside it, a comment of a ` +
    'few words on its line or the line above saying why the rule does not hold there, then run ' +
    `session-suppressions index, which writes ${index} for the owner's review. ` +
    'session-suppressions check fails on a marker without its reason and on a stale index.'
  )
}

async function indexOf($: EngineInterface, cwd: string): Promise<string> {
  try {
    const parsed: unknown = JSON.parse(await $.fs.read(`${cwd}/.claude/claude-kit.json`))
    if (typeof parsed === 'object' && parsed !== null && 'suppressions' in parsed) {
      const settings = parsed.suppressions
      if (typeof settings === 'object' && settings !== null && 'index' in settings && typeof settings.index === 'string' && settings.index !== '') {
        return settings.index
      }
    }
  } catch {
    return DEFAULT_INDEX
  }

  return DEFAULT_INDEX
}

async function note($: EngineInterface, path: string, added: string, before: string): Promise<string | null> {
  if (isProse(path)) {
    return null
  }
  const was = new Set(suppressionsIn(before))
  const names = suppressionsIn(added).filter((name) => !was.has(name))

  return names.length === 0 ? null : warning(names, await indexOf($, await $.session.cwd()))
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
