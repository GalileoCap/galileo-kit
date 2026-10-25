// Context, in-process: the engine's own figure after every tool call, a
// warning to the model every `step` tokens past `threshold` percent of the
// window, a band above the prompt with the figure for the person, and, with
// the `chain` option on, the chain: the model calls `clear_point`, and when
// that turn ends the kit writes the handoff, compacts and continues.
//
// The model is the one that knows where a clear point is, so the warning
// goes to it, on the tool result, while it can still choose where to stop,
// and the chain starts on its signal and never on the kit's own judgement.
// The end of a turn is left alone: a held stop costs every long turn a
// closing paragraph. Nothing here blocks a tool call. A hook that fails is
// replaced by what ran beneath it, so the kit is never the reason a call
// fails. The engine's own compaction gets the backstop whatever the option.

import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { ChainState, ContextFigure } from '../types'

const warnedAt = atom({ plugin: 'session-kit', key: 'contextWarnedAt' } as const, 0)
const figure = atom({ plugin: 'session-kit', key: 'contextFigure' } as const, null)
const chain = atom({ plugin: 'session-kit', key: 'chain' } as const, null)

const THRESHOLD_PERCENT = 50
const STEP_TOKENS = 25000

const TOOL_NAME = 'clear_point'
const TOOL = 'mcp__session-kit__clear_point'
const HANDOFF_COMMAND = 'session-kit:handoff'
const COMPACT_TRIES = 6
const COMPACT_RETRY_MS = 500

const TOOL_DESCRIPTION =
  'Call this at a clear point: the tree is committed and green, nothing is in ' +
  'flight, and the next step is known. When this turn ends, session-kit writes ' +
  'the handoff (CLAUDE.local.md), compacts the context, and continues with the ' +
  'next step, or stops when that step waits on the owner. Then end the turn ' +
  'with nothing more started.'

const HANDOFF_FIELDS =
  'Keep the task in the user\'s own words, every decision with who took it and ' +
  'why, where the work stands (done, in progress, not started), the last check ' +
  'that ran and its result, the open questions for the user, and the next step ' +
  'as one line. Name by path every document the work rests on, so the next ' +
  'turn reads each again in full.'

const COMPACT_INSTRUCTIONS =
  'CLAUDE.local.md holds the handoff written for this compaction: keep the ' +
  'task, the decisions, where the work stands, the last proof and the next ' +
  'step as it states them, and the paths of the documents it lists. ' +
  HANDOFF_FIELDS

export function backstop(instructions: string | undefined): string {
  const added =
    'This compaction comes without a handoff, so the summary stands in for ' +
    'CLAUDE.local.md. ' +
    HANDOFF_FIELDS

  return instructions === undefined || instructions === '' ? added : `${instructions}\n${added}`
}

export function continuePrompt(note: string): string {
  return (
    'Continue. Read again in full the documents CLAUDE.local.md lists, then ' +
    `take its next step: ${note}`
  )
}

export function advice(percent: number, chainOn = false): string {
  const close = chainOn
    ? `then call the ${TOOL_NAME} tool.`
    : 'then tell the user it is safe to compact.'
  if (percent >= 80) {
    return (
      'Stop starting anything new. Commit or discard what is in the tree, ' +
      (chainOn
        ? `and call the ${TOOL_NAME} tool now.`
        : 'write CLAUDE.local.md now, and end this turn saying you are ready to compact.')
    )
  }
  if (percent >= 65) {
    return (
      'End this turn at the next green commit, even with the task unfinished: ' +
      (chainOn
        ? `reach a clean tree, ${close} Start nothing new before that.`
        : 'write CLAUDE.local.md, reach a clean tree, and tell the user whether it ' +
          'is safe to compact. Start nothing new before that.')
    )
  }

  return (
    'Aim for a safe point: finish the step under the cursor, commit if it is ' +
    (chainOn ? `green, ${close}` : `green, write CLAUDE.local.md, ${close}`)
  )
}

export function warning(f: ContextFigure, chainOn = false): string {
  return `Context at ${f.tokens.toLocaleString('en-US')} tokens (${f.percent}% of ${f.window.toLocaleString('en-US')}). ${advice(f.percent, chainOn)}`
}

function asNumber(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) && value > 0 ? value : fallback
}

function reason(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

function textResult(text: string, isError = false) {
  return { result: { content: [{ type: 'text', text }], isError } }
}

function stageLine(state: ChainState): string {
  switch (state.stage) {
    case 'requested':
      return 'Clear point: the handoff, the compaction and the continue run when this turn ends.'
    case 'handoff':
      return 'session-kit is writing the handoff.'
    case 'compacting':
      return 'session-kit is compacting the context.'
    case 'waiting':
      return `Compacted. The next step is yours: ${state.note}`
  }
}

async function runHandoff($: EngineInterface): Promise<void> {
  try {
    await $.command.run({ command: HANDOFF_COMMAND })
  } catch (error) {
    await update($, chain, () => null)
    $.ui.toast(`session-kit: the handoff did not run (${reason(error)}), so the chain stops here.`)
  }
}

async function compactThenContinue($: EngineInterface, state: ChainState, tries = COMPACT_TRIES): Promise<void> {
  let compacted
  try {
    compacted = await $.session.compact({ instructions: COMPACT_INSTRUCTIONS })
  } catch (error) {
    // The turn that just ended may not have let go yet: try again shortly.
    if (tries > 1) {
      $.clock.after(COMPACT_RETRY_MS, () => {
        void compactThenContinue($, state, tries - 1)
      })

      return
    }
    await update($, chain, () => null)
    $.ui.toast(`session-kit: the compaction did not run (${reason(error)}), so the chain stops here.`)

    return
  }
  if (compacted.skip !== undefined) {
    await update($, chain, () => null)
    $.ui.toast(`session-kit: the compaction was skipped (${compacted.skip}), so the chain stops here.`)

    return
  }
  if (state.waitsOnOwner) {
    await update($, chain, () => ({ ...state, stage: 'waiting' }))

    return
  }
  await update($, chain, () => null)
  await $.prompt.submit({ text: continuePrompt(state.note) })
}

export const register: Register = (on, options) => {
  const threshold = asNumber(options.threshold, THRESHOLD_PERCENT)
  const step = asNumber(options.step, STEP_TOKENS)
  const chainOn = options.chain === true

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined || e.tool === TOOL) {
      return ran
    }
    const { context } = await $.session.usage()
    if (context.tokens === undefined || context.percent === undefined) {
      return ran
    }
    const now: ContextFigure = {
      tokens: context.tokens,
      window: context.window,
      percent: context.percent,
    }
    await update($, figure, () => now)

    const trigger = (context.window * threshold) / 100
    if (now.tokens < trigger) {
      return ran
    }
    const warned = await read($, warnedAt)
    // A context smaller than the last warning has been compacted: warn afresh.
    if (warned && warned <= now.tokens && now.tokens < warned + step) {
      return ran
    }
    await update($, warnedAt, () => now.tokens)

    return { ...ran, context: [...(ran.context ?? []), warning(now, chainOn)] }
  }).catch(($, e, next) => next(e))

  on('session.measure', async ($, e, next) => {
    const { tokens, window, percent } = e.context
    if (tokens !== undefined && percent !== undefined) {
      await update($, figure, () => ({ tokens, window, percent }))
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  on('session.compact', { trigger: 'auto' }, ($, e, next) => {
    if (e.agentId !== undefined) {
      return next(e)
    }

    return next({ ...e, instructions: backstop(e.instructions) })
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const running = await read($, chain)
    const now = await read($, figure)
    if (e.props.hasSurvey || (running === null && (now === null || now.percent < threshold))) {
      return next(e)
    }
    const { Box, Text } = $.ui.resolve(e)
    if (running !== null) {
      return (
        <Box>
          <Text dimColor>{stageLine(running)}</Text>
        </Box>
      )
    }

    return (
      <Box>
        <Text dimColor>
          Context {now?.percent}% of {now?.window.toLocaleString('en-US')}: find a clear point, commit, write the handoff, {chainOn ? `call ${TOOL_NAME}.` : 'ask to compact.'}
        </Text>
      </Box>
    )
  }).catch(($, e, next) => next(e))

  if (!chainOn) {
    return
  }

  on('session.start', async ($, e, next) => {
    await $.tool.register({
      name: TOOL_NAME,
      description: TOOL_DESCRIPTION,
      inputSchema: {
        type: 'object',
        properties: {
          next_step: {
            type: 'string',
            enum: ['session', 'owner'],
            description: 'Who takes the next step: the session, or the owner (a review, an answer, an approval).',
          },
          note: { type: 'string', description: 'The next step, in one line.' },
        },
        required: ['next_step', 'note'],
      },
      isDeferred: false,
    })

    return next(e)
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: TOOL }, async ($, e) => {
    const nextStep = e.next_step
    const note = typeof e.note === 'string' && e.note.trim() !== '' ? e.note.trim() : ''
    if ((nextStep !== 'session' && nextStep !== 'owner') || note === '') {
      return textResult('next_step must be "session" or "owner", and note the next step in one line.', true)
    }
    const waitsOnOwner = nextStep === 'owner'
    await update($, chain, () => ({ stage: 'requested', waitsOnOwner, note }))

    return textResult(
      'Clear point noted. End this turn now, with nothing more started. When it ' +
        'ends, session-kit writes the handoff and compacts the context, then ' +
        (waitsOnOwner ? 'stops, since the next step is the owner\'s.' : `continues with: ${note}`),
    )
  }).catch(() => textResult('session-kit could not record the clear point, so the chain did not start.', true))

  on('turn.complete', async ($, e, next) => {
    if (e.agentId !== undefined) {
      return next(e)
    }
    const state = await read($, chain)
    if (state === null) {
      return next(e)
    }
    if (e.reason !== 'answer') {
      await update($, chain, () => null)

      return next(e)
    }
    switch (state.stage) {
      case 'requested': {
        await update($, chain, () => ({ ...state, stage: 'handoff' }))
        // Outside this dispatch: a command run inside a hook the turn waits on is refused.
        $.clock.after(0, () => {
          void runHandoff($)
        })
        break
      }
      case 'handoff': {
        await update($, chain, () => ({ ...state, stage: 'compacting' }))
        $.clock.after(0, () => {
          void compactThenContinue($, state)
        })
        break
      }
      default:
        // A turn ended with the chain compacting or waiting: the person moved on.
        await update($, chain, () => null)
    }

    return next(e)
  }).catch(($, e, next) => next(e))
}
