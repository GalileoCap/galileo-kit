// A question the session put to the person in the app's next-step box (the
// `ask` of `wrap_up`): it waits from the turn that asked it until the person's
// next prompt, both seen by context.tsx's hooks, which keep the kit's hooks
// line under the validator's cut. While it waits, the chain does not start and the tagged-lines
// check sends no prompt, since a turn of the kit's would take the box's place.
// A handoff that runs anyway (the cold-cache timer, or the person's own press)
// writes the question word for word, and the band shows it with its buttons
// until the person answers.

import { atom, read, update } from 'claude-code'
import type { EngineInterface } from 'claude-code'

import type { PendingQuestion, QuestionAction } from '../types'

export const WRAP_UP_TOOL = 'mcp__ccd_turn__wrap_up'

const pendingQuestion = atom({ plugin: 'session-kit', key: 'pendingQuestion' } as const, null)

function text(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

/** The box's buttons: a reply sends its message, or its label when it has none; an app action is the app's to run, so it carries no message. */
export function questionActions(value: unknown): QuestionAction[] {
  if (!Array.isArray(value)) {
    return []
  }

  return value.flatMap((item: unknown): QuestionAction[] => {
    if (typeof item !== 'object' || item === null) {
      return []
    }
    const action = 'action' in item ? text(item.action) : ''
    const label = 'label' in item ? text(item.label) : ''
    const message = 'message' in item ? text(item.message) : ''
    if (action !== '') {
      return [{ label: label === '' ? action : label, message: null }]
    }

    return label === '' ? [] : [{ label, message: message === '' ? label : message }]
  })
}

/** The handoff's instruction for a waiting question: under Open questions, word for word, with its options. */
export function handoffArgs(q: PendingQuestion): string {
  const options = q.actions.map((a) => (a.message === null || a.message === a.label ? a.label : `${a.label} ("${a.message}")`))

  return (
    'A question of the session\'s waits on the owner, unanswered. Write it under Open questions ' +
    `word for word, with its options: ${q.ask}` +
    (options.length === 0 ? '' : ` Options: ${options.join('; ')}.`)
  )
}

/** The args of the handoff command: the waiting question, which is then carried to the band, or none. */
export async function carryQuestion($: EngineInterface): Promise<string | undefined> {
  const q = await read($, pendingQuestion)
  if (q === null) {
    return undefined
  }
  if (!q.carried) {
    await update($, pendingQuestion, () => ({ ...q, carried: true }))
  }

  return handoffArgs(q)
}

/** A press on one of the question's buttons: its message goes as the person's own prompt, and the question is answered. */
export async function answerQuestion($: EngineInterface, message: string): Promise<void> {
  await update($, pendingQuestion, () => null)
  // Outside the press's dispatch: a prompt sent inside a hook the engine waits on would be refused.
  $.clock.after(0, () => {
    void $.prompt.submit({ text: message, asUser: true })
  })
}

export async function dismissQuestion($: EngineInterface): Promise<void> {
  await update($, pendingQuestion, () => null)
}

/** A main-loop `wrap_up` that went through: its question waits, and one without a question clears any. */
export async function noteQuestion($: EngineInterface, args: { ask?: unknown; actions?: unknown }): Promise<void> {
  const ask = text(args.ask)
  await update($, pendingQuestion, () => (ask === '' ? null : { ask, actions: questionActions(args.actions), carried: false }))
}
