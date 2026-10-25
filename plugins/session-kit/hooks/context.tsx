// Context pressure, in-process: the engine's own figure after every tool
// call, a warning to the model every `step` tokens past `threshold` percent
// of the window, and a band above the prompt with the figure for the person.
//
// The model is the one that knows where a clear point is, so the warning
// goes to it, on the tool result, while it can still choose where to stop.
// The end of a turn is left alone: a held stop costs every long turn a
// closing paragraph. Nothing here blocks a tool call. A hook that fails is
// replaced by what ran beneath it, so the kit is never the reason a call
// fails.

import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { ContextFigure } from '../types'

const warnedAt = atom({ plugin: 'session-kit', key: 'contextWarnedAt' } as const, 0)
const figure = atom({ plugin: 'session-kit', key: 'contextFigure' } as const, null)

const THRESHOLD_PERCENT = 50
const STEP_TOKENS = 25000

export function advice(percent: number): string {
  if (percent >= 80) {
    return (
      'Stop starting anything new. Commit or discard what is in the tree, ' +
      'write CLAUDE.local.md now, and end this turn saying you are ready to compact.'
    )
  }
  if (percent >= 65) {
    return (
      'End this turn at the next green commit, even with the task unfinished: ' +
      'write CLAUDE.local.md, reach a clean tree, and tell the user whether it ' +
      'is safe to compact. Start nothing new before that.'
    )
  }
  return (
    'Aim for a safe point: finish the step under the cursor, commit if it is ' +
    'green, write CLAUDE.local.md, then tell the user it is safe to compact.'
  )
}

export function warning(f: ContextFigure): string {
  return `Context at ${f.tokens.toLocaleString('en-US')} tokens (${f.percent}% of ${f.window.toLocaleString('en-US')}). ${advice(f.percent)}`
}

function asNumber(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) && value > 0 ? value : fallback
}

export const register: Register = (on, options) => {
  const threshold = asNumber(options.threshold, THRESHOLD_PERCENT)
  const step = asNumber(options.step, STEP_TOKENS)

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined) {
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

    return { ...ran, context: [...(ran.context ?? []), warning(now)] }
  }).catch(($, e, next) => next(e))

  on('session.measure', async ($, e, next) => {
    const { tokens, window, percent } = e.context
    if (tokens !== undefined && percent !== undefined) {
      await update($, figure, () => ({ tokens, window, percent }))
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const now = await read($, figure)
    if (e.props.hasSurvey || now === null || now.percent < threshold) {
      return next(e)
    }
    const { Box, Text } = $.ui.resolve(e)

    return (
      <Box>
        <Text dimColor>
          Context {now.percent}% of {now.window.toLocaleString('en-US')}: find a clear point, commit, write the handoff, ask to compact.
        </Text>
      </Box>
    )
  }).catch(($, e, next) => next(e))
}
