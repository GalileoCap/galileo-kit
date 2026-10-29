// The pre-send check (`A85`): a message of the person's that starts with `??`,
// or holds four bullets or more of its own, is read by Haiku against the
// owner's rules before it is sent. When Haiku finds something, the message is
// held, put back in the box, and the band shows up to three findings with
// Send as is, Use the rewrite and a dismissal. Nothing is rewritten without a
// press. A message Haiku finds nothing in, a check that fails or times out,
// and a surface that draws no band let the message through as written, the
// `??` taken off. A press of Send as is or Use the rewrite lets the next
// message of the person's through unchecked.

import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { PresendHeld } from '../types'
import { drawsBand, isThePersons } from './context'
import { ownLines } from './tags'

const MODEL = 'haiku'
const MAX_TOKENS = 2000
const TIMEOUT_MS = 15000
const BULLETS = 4
const FINDINGS_SHOWN = 3
const ASKS_SHOWN = 1500
const NAMES_SHOWN = 3000

const held = atom({ plugin: 'session-kit', key: 'presendHeld' } as const, null)
const pass = atom({ plugin: 'session-kit', key: 'presendPass' } as const, false)

const ASKED = /^\s*\?\?\s*/
const BULLET = /^[ \t]*(?:[-*+]|\d+[.)])\s/
// A `??` or a line that may be a bullet, a matcher since the engine takes one unmatched `prompt.submit` hook per module; the hook decides.
const MAYBE = /\?\?|^\s*[-*+\d]/m

const SYSTEM =
  'You check a message the owner is about to send to a coding agent, against the owner\'s own rules. ' +
  'Answer with JSON alone: {"findings": ["…"], "rewrite": "…"}. Each finding is one short line that quotes ' +
  'the first words of the line it is about. Give three at most, the most useful first. When nothing breaks a ' +
  'rule, answer {"findings": []}. The rewrite is the whole message with each finding fixed and nothing else ' +
  'changed, in the owner\'s own voice and language, and is left out when there is no finding.'

const RULES = [
  'A line may start with a tag: "Do:" an order, "Decide:" a binding answer, "Ask:" a question that changes nothing, "Later:" deferred work, "FYI:" context with no action. A message that mixes an order, a decision and a question should tag its lines, and in a tagged message an untagged line should get a tag: offer the one it reads as.',
  'An "Ask:" line phrased as an order, or a "Do:" line phrased as a question, contradicts its tag.',
  'An id (an entry like A12 or O3, an item like M27 or Q4) is written with its name.',
  'A short go-ahead ("yes to both", "proceed", "ok") after a reply that asked several questions should say which it answers: name the ones it leaves open, from the reply\'s questions below.',
  'A long run asked for (a benchmark, a sweep, an overnight job) states a time estimate, how often to check in, or when to stop.',
  'A reversal ("remove it", "take them back", "undo that") gives its reason.',
]

/** How many of the message's own lines are bullets, outside fenced and pasted blocks. */
export function bulletCount(text: string): number {
  const lines = text.split('\n')

  return ownLines(lines).filter((i) => BULLET.test(lines[i] ?? '')).length
}

/** The findings and the rewrite in Haiku's answer; null when it names no finding or cannot be read. */
export function readReview(answer: string): { findings: string[]; rewrite: string | null } | null {
  const json = /\{[\s\S]*\}/.exec(answer)?.[0]
  if (json === undefined) {
    return null
  }
  let parsed: unknown
  try {
    parsed = JSON.parse(json)
  } catch {
    return null
  }
  if (typeof parsed !== 'object' || parsed === null || !('findings' in parsed) || !Array.isArray(parsed.findings)) {
    return null
  }
  const findings = parsed.findings.filter((f): f is string => typeof f === 'string' && f.trim() !== '').map((f) => f.trim()).slice(0, FINDINGS_SHOWN)
  if (findings.length === 0) {
    return null
  }
  const rewrite = 'rewrite' in parsed && typeof parsed.rewrite === 'string' && parsed.rewrite.trim() !== '' ? parsed.rewrite : null

  return { findings, rewrite }
}

/** The questions the last reply put to the owner, from its `Asks you:` block, or its last paragraph when it has none. */
async function lastAsks($: EngineInterface): Promise<string> {
  try {
    const last = [...(await $.session.messages())].reverse().find((m) => m.role === 'assistant')
    const text = last?.text ?? ''
    const at = text.lastIndexOf('Asks you:')
    const asks = at >= 0 ? text.slice(at) : text.split('\n\n').at(-1) ?? ''

    return asks.slice(0, ASKS_SHOWN)
  } catch {
    return ''
  }
}

/** The project's intent ids with their names, so Haiku can tell a named id from a bare one; empty where there is none. */
async function intentNames($: EngineInterface): Promise<string> {
  try {
    const r = await $.process.run(['session-intent', 'names'], { cwd: await $.session.cwd() })

    return r.exitCode === 0 ? r.stdout.slice(0, NAMES_SHOWN) : ''
  } catch {
    return ''
  }
}

async function review($: EngineInterface, draft: string): Promise<{ findings: string[]; rewrite: string | null } | null> {
  const asks = await lastAsks($)
  const names = await intentNames($)
  const prompt = [
    'The owner\'s rules for a message:',
    ...RULES.map((r) => `- ${r}`),
    '',
    asks === '' ? 'The last reply asked nothing.' : `The last reply ended with:\n${asks}`,
    '',
    names === '' ? '' : `The project's ids and their names:\n${names}\n`,
    'The message:',
    '<<<',
    draft,
    '>>>',
  ].join('\n')
  try {
    const r = await $.model.complete({ model: MODEL, system: SYSTEM, prompt, maxTokens: MAX_TOKENS, timeoutMs: TIMEOUT_MS })

    return r.isAnswered ? readReview(r.text) : null
  } catch {
    return null
  }
}

async function bandHere($: EngineInterface): Promise<boolean> {
  try {
    return (await $.session.surfaces()).every(drawsBand)
  } catch {
    return false
  }
}

/** Outside the press's dispatch: a prompt sent inside a hook the engine waits on would be refused. */
function later($: EngineInterface, run: () => Promise<void>): void {
  $.clock.after(0, () => {
    void run()
  })
}

/** Sends what the box holds, the held message when it is empty, and lets it through unchecked. */
export async function sendAsIs($: EngineInterface): Promise<void> {
  const kept = await read($, held)
  await update($, held, () => null)
  if (kept === null) {
    return
  }
  later($, async () => {
    const box = (await $.prompt.read()).text
    const text = box.trim() === '' ? kept.text : box
    await update($, pass, () => true)
    await $.prompt.fill({ text: '', mode: 'replace' })
    await $.prompt.submit({ text, asUser: true })
  })
}

/** Puts Haiku's rewrite in the box for the person to edit and send, unchecked. */
export async function useRewrite($: EngineInterface): Promise<void> {
  const kept = await read($, held)
  await update($, held, () => null)
  if (kept?.rewrite === undefined || kept.rewrite === null) {
    return
  }
  const { rewrite } = kept
  await update($, pass, () => true)
  later($, async () => {
    await $.prompt.fill({ text: rewrite, mode: 'replace' })
  })
}

export async function dismissHeld($: EngineInterface): Promise<void> {
  await update($, held, () => null)
}

export const register: Register = (on) => {
  on('prompt.submit', { text: MAYBE }, async ($, e, next) => {
    if (e.command !== undefined || !isThePersons(e.origin)) {
      return next(e)
    }
    const asked = ASKED.test(e.text)
    const text = asked ? e.text.replace(ASKED, '') : e.text
    if (await read($, pass)) {
      await update($, pass, () => false)

      return next({ ...e, text })
    }
    if ((!asked && bulletCount(text) < BULLETS) || !(await bandHere($))) {
      return next({ ...e, text })
    }
    const found = await review($, text)
    if (found === null) {
      if (asked) {
        $.ui.log('session-kit: the pre-send check found nothing, so the message went on.')
      }

      return next({ ...e, text })
    }
    const kept: PresendHeld = { text, findings: found.findings, rewrite: found.rewrite }
    await update($, held, () => kept)
    later($, async () => {
      await $.prompt.fill({ text, mode: 'replace' })
    })

    return { drop: `Held by the pre-send check: ${found.findings.length === 1 ? 'one finding' : `${found.findings.length} findings`} on the band, and the message is back in the box.` }
  }).catch(($, e, next) => next(e))
}
