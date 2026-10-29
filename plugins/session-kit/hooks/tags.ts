// The owner's tagged lines (`A83`): a line of the person's that starts with
// `Do:`, `Decide:`, `Ask:` or `Later:` opens an item, which the kit names with
// the tag word, a hyphen and a number (`Do-1`), counted per tag across the
// session, and lists as context beside the prompt with the closing-line forms.
// `FYI:` opens none, and neither does a line in a fenced block or in pasted
// content. The person's message reaches the model with each tag written as
// its id (`Do-1:`), so the ids stand in what they sent. At the end of the
// main loop's turn, the reply's lines that start with an id close their
// items, an `In progress` line keeping its item open.
// An item left without a line is drawn on the band and, once per item, sent
// back to the session as a prompt. While the chain or a new-task offer is
// under way the check stands aside, since a prompt of the kit's would land in
// the middle of their turns. A hook that fails leaves the prompt and the turn
// as they were.

import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { TaggedItem } from '../types'
import { isThePersons } from './context'

const NO_COUNTS: Record<string, number> = {}
const NO_ITEMS: TaggedItem[] = []
const NO_IDS: string[] = []
const TEXT_SHOWN = 60

const tagCounts = atom({ plugin: 'session-kit', key: 'tagCounts' } as const, NO_COUNTS)
const openItems = atom({ plugin: 'session-kit', key: 'openItems' } as const, NO_ITEMS)
const itemsMissed = atom({ plugin: 'session-kit', key: 'itemsMissed' } as const, NO_ITEMS)
const pendingQuestion = atom({ plugin: 'session-kit', key: 'pendingQuestion' } as const, null)
const itemsPrompted = atom({ plugin: 'session-kit', key: 'itemsPrompted' } as const, NO_IDS)
const checkDue = atom({ plugin: 'session-kit', key: 'tagCheckDue' } as const, false)
const chain = atom({ plugin: 'session-kit', key: 'chain' } as const, null)
const newTask = atom({ plugin: 'session-kit', key: 'newTask' } as const, null)

// A tag starts a line, after at most three spaces and a bullet or a number; deeper lines belong to the tag above.
const TAG_LINE = /^ {0,3}(?:[-*+]\s+|\d+[.)]\s+)?(Do|Decide|Ask|Later|FYI):\s*(\S.*)$/i
const TAG_WORD = /^( {0,3}(?:[-*+]\s+|\d+[.)]\s+)?)[A-Za-z]+:/
// The matcher only narrows the prompts the hook sees, and `taggedLines` decides; kept short for the validator's report.
const ANY_TAG = /(?:Do|Decide|Ask|Later):/i
// An id at a line's start, bare, bold or in backticks, then whether the line says the item is still in progress.
const CLOSING_LINE = /^\s*(?:[-*+]\s+)?[*`]*(Do|Decide|Ask|Later)-(\d+)[*`]*\s*:?\s*(in progress)?/i
const FENCE = /^ {0,3}(```|~~~)/
const PASTED_OPEN = /<pasted_content\b/
const PASTED_CLOSE = /<\/pasted_content\b/

function canonical(tag: string): TaggedItem['tag'] | null {
  const word = tag.toLowerCase()

  return word === 'do' ? 'Do' : word === 'decide' ? 'Decide' : word === 'ask' ? 'Ask' : word === 'later' ? 'Later' : null
}

function clip(text: string): string {
  const flat = text.trim().replace(/\s+/g, ' ')

  return flat.length > TEXT_SHOWN ? `${flat.slice(0, TEXT_SHOWN - 1)}…` : flat
}

/** The indexes of a message's own lines: those outside a fenced block and outside pasted content. */
export function ownLines(lines: readonly string[]): number[] {
  const own: number[] = []
  let fence: string | null = null
  let pasted = false
  lines.forEach((line, i) => {
    const marker = FENCE.exec(line)?.[1]
    if (pasted) {
      pasted = !PASTED_CLOSE.test(line)
    } else if (fence !== null) {
      fence = marker === fence ? null : fence
    } else if (marker !== undefined) {
      fence = marker
    } else if (PASTED_OPEN.test(line)) {
      pasted = !PASTED_CLOSE.test(line.slice(line.search(PASTED_OPEN)))
    } else {
      own.push(i)
    }
  })

  return own
}

/** The tagged lines of a message that open items, in order, each with its line's index. */
export function taggedLines(text: string): { tag: TaggedItem['tag']; text: string; line: number }[] {
  const lines = text.split('\n')
  const found: { tag: TaggedItem['tag']; text: string; line: number }[] = []
  for (const i of ownLines(lines)) {
    const m = TAG_LINE.exec(lines[i] ?? '')
    const tag = m === null ? null : canonical(m[1] ?? '')
    if (m !== null && tag !== null) {
      found.push({ tag, text: clip(m[2] ?? ''), line: i })
    }
  }

  return found
}

/** The message with each item's tag written as its id (`Do:` becomes `Do-1:`), so the person sees the ids in what they sent. */
export function withIds(text: string, items: readonly { line: number; id: string }[]): string {
  const lines = text.split('\n')
  for (const { line, id } of items) {
    lines[line] = (lines[line] ?? '').replace(TAG_WORD, `$1${id}:`)
  }

  return lines.join('\n')
}

/** The ids a reply names at the start of a line, each with whether its line keeps it in progress. */
export function closingLines(answer: string): Map<string, boolean> {
  const named = new Map<string, boolean>()
  for (const line of answer.split('\n')) {
    const m = CLOSING_LINE.exec(line)
    const tag = m === null ? null : canonical(m[1] ?? '')
    if (m !== null && tag !== null) {
      named.set(`${tag}-${m[2] ?? ''}`, m[3] !== undefined)
    }
  }

  return named
}

function listed(items: readonly TaggedItem[]): string {
  return items.map((i) => `${i.id} "${i.text}"`).join(' · ')
}

function itemsContext(items: readonly TaggedItem[]): string {
  return (
    `session-kit: the owner's tagged items, by id: ${listed(items)}. ` +
    'End the reply with one line per item, starting with its id: "Do-1 Done: …", "Do-1 Not done: <why>", ' +
    '"Do-1 In progress: <what remains>", "Decide-1 Decided: <where it is recorded>", "Later-1 Parked: <where>", ' +
    '"Ask-1 Answered: <first words>". Then "Read as Do: …" or "Read as FYI: …" for each untagged line you acted on, ' +
    'and last, under "Asks you:", each question the owner must answer, one per line.'
  )
}

function missedPrompt(items: readonly TaggedItem[]): string {
  return (
    `session-kit: your reply leaves these tagged items without a closing line: ${listed(items)}. ` +
    'Report each on a line that starts with its id, or say why not.'
  )
}

export async function dismissMissed($: EngineInterface): Promise<void> {
  await update($, itemsMissed, () => NO_ITEMS)
}

/** Ids for the new items, counted on from the session's last number per tag. */
async function numbered($: EngineInterface, lines: { tag: TaggedItem['tag']; text: string }[]): Promise<TaggedItem[]> {
  const counts = { ...(await read($, tagCounts)) }
  const items = lines.map((l) => {
    const n = (counts[l.tag] ?? 0) + 1
    counts[l.tag] = n

    return { id: `${l.tag}-${n}`, tag: l.tag, text: l.text }
  })
  await update($, tagCounts, () => counts)

  return items
}

/** The reply's closing lines read against the open items: closed ones go, and the missed ones are kept for the band and returned. */
async function settle($: EngineInterface, answer: string): Promise<TaggedItem[]> {
  const named = closingLines(answer)
  const open = await read($, openItems)
  const stillOpen = open.filter((i) => named.get(i.id) !== false)
  const missed = open.filter((i) => !named.has(i.id))
  await update($, openItems, () => stillOpen)
  await update($, itemsMissed, () => missed)
  const kept = new Set(stillOpen.map((i) => i.id))
  await update($, itemsPrompted, (ids) => ids.filter((id) => kept.has(id)))

  return missed
}

export const register: Register = (on) => {
  // A prompt with a tagged line, a matcher since the engine takes one unmatched `prompt.submit` hook per module (context.tsx's).
  on('prompt.submit', { text: ANY_TAG }, async ($, e, next) => {
    if (e.command !== undefined || !isThePersons(e.origin)) {
      return next(e)
    }
    const lines = taggedLines(e.text)
    if (lines.length === 0) {
      return next(e)
    }
    const fresh = await numbered($, lines)
    const open = [...(await read($, openItems)), ...fresh]
    await update($, openItems, () => open)
    await update($, checkDue, () => true)

    const shown = withIds(e.text, fresh.map((item, i) => ({ id: item.id, line: lines[i]?.line ?? -1 })))

    return next({ ...e, text: shown, context: [...(e.context ?? []), itemsContext(open)] })
  }).catch(($, e, next) => next(e))

  // The check runs before the turn is passed on, so a concern beneath that fails cannot skip it.
  on('turn.complete', { reason: 'answer' }, async ($, e, next) => {
    if (e.agentId !== undefined || !(await read($, checkDue))) {
      return next(e)
    }
    await update($, checkDue, () => false)
    if ((await read($, chain)) !== null || (await read($, newTask)) !== null) {
      return next(e)
    }
    const missed = await settle($, e.answer)
    // A prompt of the kit's would start a turn over the session's question: the band shows the missed items alone.
    if ((await read($, pendingQuestion)) !== null) {
      return next(e)
    }
    const asked = new Set(await read($, itemsPrompted))
    const unasked = missed.filter((i) => !asked.has(i.id))
    if (unasked.length > 0) {
      await update($, itemsPrompted, (ids) => [...ids, ...unasked.map((i) => i.id)])
      await update($, checkDue, () => true)
      // Outside this dispatch: a prompt sent inside a hook the turn waits on would start before it ends.
      $.clock.after(0, () => {
        void $.prompt.submit({ text: missedPrompt(unasked) })
      })
    }

    return next(e)
  }).catch(($, e, next) => next(e))
}
