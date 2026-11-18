// The reference mod (A24): each intent id in a reply is drawn with its name
// beside it, `A20` as `A20` (one module per concern), on the screen alone.
// The stored message keeps what the model wrote. The names come from the
// project's generated INDEX.md, one read, again only when its mtime moves.
// An id is named at its first mention in a block, unless the model named it
// there, by its name, an aside after a comma, or a parenthesis. Ids in code,
// in a path or a file name, and ids the index does not hold are drawn as
// written. A hook that fails draws the reply as is.

import type { EngineInterface, Register } from 'claude-code'

const DEFAULT_DIRECTORY = 'docs/intent'
const INDEX_LINE = /^\s*- \[([A-Z]+\d+) ([^\]]+)\]\(/gm

type Names = ReadonlyMap<string, string>

/** Each id the index lists, with its name as a reply writes it: the title's first letter lowered unless the first word is all capitals or mixed. */
export function namesIn(index: string): Names {
  const names = new Map<string, string>()
  for (const [, id, title] of index.matchAll(INDEX_LINE)) {
    if (id !== undefined && title !== undefined && !names.has(id)) {
      const first = title.split(' ', 1)[0] ?? ''
      const keepsCase = /[A-Z]/.test(first.slice(1)) || first.startsWith('`')
      names.set(id, keepsCase ? title : title.charAt(0).toLowerCase() + title.slice(1))
    }
  }

  return names
}

/**
 * Whether the words after an id already carry its name: a parenthesis or a
 * comma and words right after it (`A24`, the mod), which a paraphrase passes
 * too, or the name's first three words before the sentence ends.
 */
function alreadyNamed(after: string, name: string): boolean {
  if (/^\s*\(|^,\s+(?![A-Z]+\d)[a-z`'"]/.test(after)) {
    return true
  }
  const sentence = after.split(/(?<=[.!?])\s|\n/, 1)[0] ?? ''
  const head = name.toLowerCase().split(/\s+/).slice(0, 3).join(' ')

  return sentence.toLowerCase().includes(head)
}

/** The text with the first mention of each named id followed by its name; code, paths and named mentions left alone. */
export function annotate(text: string, names: Names): string {
  if (names.size === 0) {
    return text
  }
  const seen = new Set<string>()
  // Fenced blocks are kept whole; the rest is cut at inline code spans.
  return text
    .split(/(^```[^\n]*\n[\s\S]*?^```[^\n]*$)/m)
    .map((part) => (part.startsWith('```') ? part : prose(part, names, seen)))
    .join('')
}

function prose(text: string, names: Names, seen: Set<string>): string {
  const out: string[] = []
  const pieces = text.split(/(`[^`\n]*`)/)
  pieces.forEach((piece, i) => {
    const rest = pieces.slice(i + 1).join('')
    if (piece.startsWith('`') && piece.endsWith('`') && piece.length > 1) {
      const id = piece.slice(1, -1)
      out.push(piece + suffix(id, rest, names, seen))

      return
    }
    out.push(
      piece.replace(/(?<![\w/.-])([A-Z]+\d+)(?![\w/-])/g, (match: string, id: string, offset: number) => {
        return match + suffix(id, piece.slice(offset + match.length) + rest, names, seen)
      }),
    )
  })

  return out.join('')
}

function suffix(id: string, after: string, names: Names, seen: Set<string>): string {
  const name = names.get(id)
  if (name === undefined || seen.has(id)) {
    return ''
  }
  seen.add(id)

  return alreadyNamed(after, name) ? '' : ` (${name})`
}

async function directory($: EngineInterface, cwd: string): Promise<string> {
  try {
    const parsed: unknown = JSON.parse(await $.fs.read(`${cwd}/.claude/claude-kit.json`))
    if (typeof parsed === 'object' && parsed !== null && 'intent' in parsed) {
      const intent = parsed.intent
      if (typeof intent === 'object' && intent !== null && 'directory' in intent && typeof intent.directory === 'string' && intent.directory !== '') {
        return intent.directory
      }
    }
  } catch {
    return DEFAULT_DIRECTORY
  }

  return DEFAULT_DIRECTORY
}

// One process's cache of the names, by the index's path and mtime; a reload starts it over.
let cached: { path: string; mtimeMs: number; names: Names } | null = null

async function names($: EngineInterface): Promise<Names> {
  const cwd = await $.session.cwd()
  const path = `${cwd}/${await directory($, cwd)}/INDEX.md`
  if (!(await $.fs.exists(path))) {
    return new Map()
  }
  const { mtimeMs } = await $.fs.stat(path)
  if (cached === null || cached.path !== path || cached.mtimeMs !== mtimeMs) {
    cached = { path, mtimeMs, names: namesIn(await $.fs.read(path)) }
  }

  return cached.names
}

export const register: Register = (on) => {
  on('ui.render', { component: 'AssistantMessage' }, async ($, e, next) => {
    const text = annotate(e.props.text, await names($))

    return text === e.props.text ? next(e) : next({ ...e, props: { ...e.props, text } })
  }).catch(($, e, next) => next(e))
}
