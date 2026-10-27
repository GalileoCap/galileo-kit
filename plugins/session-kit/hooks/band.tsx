// The band above the prompt and the line that closes a turn. The band keeps
// only what needs the person: a failure, the offer or the chain or the context
// figure past its threshold, the cold-cache timer that will act on its own, and
// a usage window at 95% (at 80% when the kit keeps no status line). Each row is
// a bold label, the figures, and the buttons that do the thing. The kit's rows
// draw above whatever the plugins beneath drew, so no band of theirs is hidden.
// The turn line gets the context percent the turn ended at, found by the turn's
// duration, so an old line never shows a later figure.

import { atom, read } from 'claude-code'
import type { ElementTable, EngineInterface, Register, SessionRateLimit } from 'claude-code'

import type { TurnFigure, ChainState, ContextFigure, Failure, NewTaskState } from '../types'
import {
  adviceTier,
  chainByPerson,
  dismissChain,
  dismissCold,
  dismissFailure,
  dismissFigure,
  dismissLimit,
  dismissOffer,
  handoffByPerson,
  handoffThenClear,
  keepGoing,
  retryFailure,
  runColdNow,
} from './context'
import { LIMIT_FIRM, LIMIT_WARN, coldText, compact, limitLine, newTaskLine, showsLimit, stageLine } from './lines'
import { readOptions, triggerTokens, withinStep } from './options'

const NO_WINDOWS: SessionRateLimit[] = []
const NO_MARKS: Record<string, number> = {}
const NO_TURNS: TurnFigure[] = []

const chain = atom({ plugin: 'session-kit', key: 'chain' } as const, null)
const coldTimerAt = atom({ plugin: 'session-kit', key: 'coldTimerAt' } as const, 0)
const failure = atom({ plugin: 'session-kit', key: 'failure' } as const, null)
const figure = atom({ plugin: 'session-kit', key: 'contextFigure' } as const, null)
const figureDismissedAt = atom({ plugin: 'session-kit', key: 'contextDismissedAt' } as const, 0)
const limitsDismissed = atom({ plugin: 'session-kit', key: 'limitsDismissed' } as const, NO_MARKS)
const newTask = atom({ plugin: 'session-kit', key: 'newTask' } as const, null)
const rateLimits = atom({ plugin: 'session-kit', key: 'rateLimits' } as const, NO_WINDOWS)
const turnFigures = atom({ plugin: 'session-kit', key: 'turnFigures' } as const, NO_TURNS)
const turnGrowth = atom({ plugin: 'session-kit', key: 'turnGrowth' } as const, 0)

type Parts = Pick<ElementTable<'desktop'>, 'Box' | 'Button' | 'Text'>

/** What a row needs to draw: the elements, whether a turn runs, and whether the chain is on. */
type Draw = { p: Parts; isWorking: boolean; chainOn: boolean }

/** A small ✕ at the row's right edge: the spacer takes the free width, and the glyph stands alone as a plain control. */
function dismissButton(d: Draw, key: string, onPress: () => void) {
  const { Box, Button } = d.p

  return (
    <Box key={`${key}-end`} flexGrow={1} justifyContent="flex-end">
      <Button key={key} label="✕" plain dimColor onPress={onPress} />
    </Box>
  )
}

function failureRow($: EngineInterface, d: Draw, held: Failure) {
  const { Box, Button, Text } = d.p

  return (
    <Box key="failure" gap={1} alignItems="center">
      <Text bold color="error">Failed</Text>
      <Text>{`${held.text}.`}</Text>
      {held.retry === undefined ? null : <Button key="failure-retry" label="Try again" onPress={() => retryFailure($)} />}
      {dismissButton(d, 'failure-dismiss', () => dismissFailure($))}
    </Box>
  )
}

function offerRow($: EngineInterface, d: Draw, offered: NewTaskState) {
  const { Box, Button, Text } = d.p
  const isOffered = offered.stage === 'offered'

  return (
    <Box key="offer" gap={1} alignItems="center">
      <Text>{newTaskLine(offered)}</Text>
      {isOffered && offered.effort !== undefined ? (
        <Button key="new-task-clear-effort" label={`Handoff, clear, effort ${offered.effort.level}`} variant="primary" onPress={() => handoffThenClear($, offered, true)} />
      ) : null}
      {isOffered ? (
        <Button key="new-task-clear" label="Handoff and clear" variant={offered.effort === undefined ? 'primary' : undefined} onPress={() => handoffThenClear($, offered, false)} />
      ) : null}
      {isOffered ? <Button key="new-task-here" label="Keep going here" onPress={() => keepGoing($)} /> : null}
      {dismissButton(d, 'new-task-dismiss', () => dismissOffer($))}
    </Box>
  )
}

function chainRow($: EngineInterface, d: Draw, running: ChainState) {
  const { Box, Button, Text } = d.p

  return (
    <Box key="chain" gap={1} alignItems="center">
      <Text bold color={running.stage === 'waiting' && running.stopped !== undefined ? 'warning' : 'subtle'}>Chain</Text>
      <Text>{stageLine(running)}</Text>
      {dismissButton(d, 'chain-dismiss', () => dismissChain($))}
    </Box>
  )
}

function figureRow($: EngineInterface, d: Draw, now: ContextFigure, grewBy: number, tier: number) {
  const { Box, Button, Text } = d.p

  return (
    <Box key="figure" gap={1} alignItems="center">
      <Text bold color={tier === 0 ? 'warning' : 'error'}>Context</Text>
      <Text tabular>{`${compact(now.tokens)} / ${compact(now.window)}  ${now.percent}%`}</Text>
      {grewBy > 0 ? <Text dimColor>{`+${compact(grewBy)} last turn`}</Text> : null}
      {d.isWorking ? null : <Button key="context-handoff" label="Handoff" variant={d.chainOn ? undefined : 'primary'} onPress={() => handoffByPerson($)} />}
      {d.isWorking || !d.chainOn ? null : <Button key="context-chain" label="Handoff and compact" variant="primary" onPress={() => chainByPerson($)} />}
      {dismissButton(d, 'context-dismiss', () => dismissFigure($))}
    </Box>
  )
}

function coldRow($: EngineInterface, d: Draw, at: number) {
  const { Box, Button, Text } = d.p

  return (
    <Box key="cold" gap={1} alignItems="center">
      <Text bold color="subtle">Cache</Text>
      <Text>{coldText(at)}</Text>
      {d.isWorking ? null : <Button key="cold-run" label="Run chain now" variant="primary" onPress={() => runColdNow($)} />}
      {dismissButton(d, 'cold-dismiss', () => dismissCold($))}
    </Box>
  )
}

function limitRow($: EngineInterface, d: Draw, w: SessionRateLimit) {
  const { Box, Button, Text } = d.p

  return (
    <Box key={`limit-${w.kind}`} gap={1} alignItems="center">
      <Text color={w.percentUsed >= LIMIT_FIRM ? 'error' : 'warning'}>{limitLine(w)}</Text>
      {dismissButton(d, `limit-dismiss-${w.kind}`, () => dismissLimit($, w))}
    </Box>
  )
}

export const register: Register = (on, options) => {
  const { thresholdTokens, thresholdPercent, step, chainOn, statusLine } = readOptions(options)
  const limitFloor = statusLine ? LIMIT_FIRM : LIMIT_WARN

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const below = await next(e)
    const held = await read($, failure)
    const offered = await read($, newTask)
    const running = await read($, chain)
    const now = await read($, figure)
    const dismissedAt = await read($, figureDismissedAt)
    const coldAt = await read($, coldTimerAt)
    const grewBy = await read($, turnGrowth)
    const marks = await read($, limitsDismissed)
    const limits = (await read($, rateLimits)).filter((w) => showsLimit(w, marks[w.kind], limitFloor))
    const trigger = now === null ? 0 : triggerTokens(thresholdTokens, thresholdPercent, now.window)
    const past = now !== null && now.tokens >= trigger && !withinStep(dismissedAt, now.tokens, step)
    if (e.props.hasSurvey || (held === null && offered === null && running === null && !past && coldAt === 0 && limits.length === 0)) {
      return below
    }
    const { Box, Button, Text } = $.ui.resolve(e)
    const d: Draw = { p: { Box, Button, Text }, isWorking: e.props.isWorking, chainOn }
    const rows = []
    if (held !== null) {
      rows.push(failureRow($, d, held))
    }
    if (offered !== null) {
      rows.push(offerRow($, d, offered))
    } else if (running !== null) {
      rows.push(chainRow($, d, running))
    } else if (past && now !== null) {
      rows.push(figureRow($, d, now, grewBy, adviceTier(now.tokens, trigger)))
    }
    if (coldAt !== 0) {
      rows.push(coldRow($, d, coldAt))
    }
    for (const w of limits) {
      rows.push(limitRow($, d, w))
    }

    return (
      <Box flexDirection="column" rowGap="xs">
        {rows}
        {below}
      </Box>
    )
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'TurnDuration' }, async ($, e, next) => {
    const below = await next(e)
    const ended = [...(await read($, turnFigures))].reverse().find((t) => t.durationMs === e.props.durationMs)
    if (ended === undefined) {
      return below
    }
    const { Box, Text } = $.ui.resolve(e)

    return (
      <Box>
        {below}
        <Text dimColor>{` · ctx ${ended.percent}%`}</Text>
      </Box>
    )
  }).catch(($, e, next) => next(e))
}
