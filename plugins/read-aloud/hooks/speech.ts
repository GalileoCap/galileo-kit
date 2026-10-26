// An answer's markdown turned into what the voice says: one utterance per
// paragraph, heading or list item, code blocks and tables named instead of
// read, links read as their label, and no utterance longer than the engine
// speaks.

/** The engine speaks a text up to its first 4,096 characters. */
export const UTTERANCE_LIMIT = 4096

const FENCE = /^\s*(```|~~~)/
const TABLE_ROW = /^\s*\|/
const HEADING = /^\s*#{1,6}\s+(.*?)\s*#*\s*$/
const LIST_ITEM = /^\s*(?:[-*+]|\d+[.)])\s+(.*)$/
const RULE = /^\s*([-*_])(?:\s*\1){2,}\s*$/
const QUOTE = /^\s*>\s?/

/** The utterances an answer's markdown is read as, in order. */
export function utterances(markdown: string): string[] {
  return paragraphs(markdown).flatMap(text => pieces(text, UTTERANCE_LIMIT))
}

function paragraphs(markdown: string): string[] {
  const out: string[] = []
  let current: string[] = []
  const flush = () => {
    const text = spoken(current.join(' '))
    if (text !== '') {
      out.push(text)
    }
    current = []
  }
  const lines = markdown.split(/\r?\n/).map(line => line.replace(QUOTE, ''))
  const at = (i: number) => lines[i] ?? ''
  for (let i = 0; i < lines.length; i += 1) {
    const line = at(i)
    const fence = FENCE.exec(line)?.[1]
    if (fence !== undefined) {
      flush()
      while (i + 1 < lines.length && !at(i + 1).trimStart().startsWith(fence)) {
        i += 1
      }
      i += 1
      out.push('Code block skipped.')
      continue
    }
    if (TABLE_ROW.test(line)) {
      flush()
      while (i + 1 < lines.length && TABLE_ROW.test(at(i + 1))) {
        i += 1
      }
      out.push('Table skipped.')
      continue
    }
    if (line.trim() === '' || RULE.test(line)) {
      flush()
      continue
    }
    const heading = HEADING.exec(line)?.[1]
    if (heading !== undefined) {
      flush()
      current = [heading]
      flush()
      continue
    }
    const item = LIST_ITEM.exec(line)?.[1]
    if (item !== undefined) {
      flush()
      current = [item]
      continue
    }
    current.push(line.trim())
  }
  flush()

  return out
}

// One paragraph's inline markdown as plain words, ended so the voice pauses after it.
function spoken(text: string): string {
  const linked = text
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/<https?:\/\/[^>]+>/g, 'a link')
    .replace(/https?:\/\/[^\s)]*[^\s).,;:!?]/g, 'a link')
    .replace(/<\/?[a-zA-Z][^>]*>/g, '')
  const plain = linked
    .split(/(`[^`]*`)/)
    .map(part => (part.startsWith('`') ? part.slice(1, -1) : unemphasized(part)))
    .join('')
    .replace(/\s+/g, ' ')
    .trim()
  if (plain === '' || /[.!?:;]$/.test(plain)) {
    return plain
  }

  return `${plain}.`
}

function unemphasized(text: string): string {
  return text
    .replace(/(\*\*|__)(.+?)\1/g, '$2')
    .replace(/~~(.+?)~~/g, '$1')
    .replace(/\*(\S(?:.*?\S)?)\*/g, '$1')
    .replace(/(^|[^\w])_(\S(?:.*?\S)?)_(?=[^\w]|$)/g, '$1$2')
}

// A paragraph cut at sentence ends into pieces of at most `limit` characters, a sentence longer than that at its last space.
function pieces(text: string, limit: number): string[] {
  if (text.length <= limit) {
    return [text]
  }
  const out: string[] = []
  let current = ''
  for (const sentence of text.split(/(?<=[.!?])\s+/).flatMap(one => hardCut(one, limit))) {
    if (current === '') {
      current = sentence
    } else if (current.length + 1 + sentence.length <= limit) {
      current = `${current} ${sentence}`
    } else {
      out.push(current)
      current = sentence
    }
  }
  if (current !== '') {
    out.push(current)
  }

  return out
}

function hardCut(sentence: string, limit: number): string[] {
  const out: string[] = []
  let rest = sentence
  while (rest.length > limit) {
    const space = rest.lastIndexOf(' ', limit)
    const at = space > 0 ? space : limit
    out.push(rest.slice(0, at))
    rest = rest.slice(at).trimStart()
  }
  out.push(rest)

  return out
}
