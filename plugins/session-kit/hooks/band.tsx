// The band above the prompt and the line that closes a turn. The band keeps
// only what needs the person: a failure, a message the pre-send check held, the
// owner's tagged items a reply left without a line, the offer or the chain or
// the context figure from its firmer tier, the cold-cache timer that will act
// on its own (a line under the context row when that row offers the same
// chain), and a usage window at 95% (at 80% when the kit keeps no status line).
// The band is a ledger (`A86`): each row is a label in a column as wide as the
// longest label shown, its text, then its buttons and its ✕ at the right, and
// only the row that leads has a coloured label and a filled button. The kit's
// rows draw above whatever the plugins beneath drew, so no band of theirs is
// hidden. The turn line gets the context percent the turn ended at, found by
// the turn's duration, so an old line never shows a later figure.

import { atom, read } from 'claude-code'
import type { ElementTable, EngineInterface, Register, SessionRateLimit } from 'claude-code'

import type { TurnFigure, ChainState, ContextFigure, Failure, NewTaskState, PresendHeld, TaggedItem } from '../types'
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
import { LIMIT_FIRM, LIMIT_WARN, coldClause, coldText, compact, limitFigures, newTaskBody, showsLimit, stageLine } from './lines'
import { readOptions, triggerTokens, withinStep } from './options'
import { dismissHeld, sendAsIs, useRewrite } from './presend'
import { dismissMissed } from './tags'

const NO_WINDOWS: SessionRateLimit[] = []
const NO_MARKS: Record<string, number> = {}
const NO_TURNS: TurnFigure[] = []
const NO_ITEMS: TaggedItem[] = []

const chain = atom({ plugin: 'session-kit', key: 'chain' } as const, null)
const coldTimerAt = atom({ plugin: 'session-kit', key: 'coldTimerAt' } as const, 0)
const failure = atom({ plugin: 'session-kit', key: 'failure' } as const, null)
const figure = atom({ plugin: 'session-kit', key: 'contextFigure' } as const, null)
const presendHeld = atom({ plugin: 'session-kit', key: 'presendHeld' } as const, null)
const itemsMissed = atom({ plugin: 'session-kit', key: 'itemsMissed' } as const, NO_ITEMS)
const figureDismissedAt = atom({ plugin: 'session-kit', key: 'contextDismissedAt' } as const, 0)
const limitsDismissed = atom({ plugin: 'session-kit', key: 'limitsDismissed' } as const, NO_MARKS)
const newTask = atom({ plugin: 'session-kit', key: 'newTask' } as const, null)
const rateLimits = atom({ plugin: 'session-kit', key: 'rateLimits' } as const, NO_WINDOWS)
const turnFigures = atom({ plugin: 'session-kit', key: 'turnFigures' } as const, NO_TURNS)
const turnGrowth = atom({ plugin: 'session-kit', key: 'turnGrowth' } as const, 0)

type Parts = Pick<ElementTable<'desktop'>, 'Box' | 'Button' | 'Text'>

/** What a row needs to draw: the elements, whether a turn runs, whether the chain is on, and the label column's width. */
type Draw = { p: Parts; isWorking: boolean; chainOn: boolean; labelWidth: number }

type Tone = 'error' | 'warning' | 'subtle'

/** A button of a row; `main` marks the one that is filled when its row leads the band. */
type Action = { key: string; label: string; main?: boolean; onPress: () => void }

/** A piece of a row's text or of a line beneath it. */
type Piece = { text: string; dim?: boolean; tabular?: boolean }

/** A row of the ledger: its label and the colour it takes when it leads, its text, its buttons, the lines beneath it and its ✕. */
type Row = { key: string; label: string; tone: Tone; text: Piece[]; actions: Action[]; details: Piece[]; dismiss: Action }

/** The label column, empty on a line beneath a row, as wide as the band's longest label, so every row's text starts at the same place. */
function labelCell(d: Draw, row: Row, isLead: boolean, label: boolean) {
  const { Box, Text } = d.p

  return (
    <Box minWidth={d.labelWidth} flexShrink={0}>
      {label ? <Text bold color={isLead ? row.tone : 'subtle'}>{row.label}</Text> : null}
    </Box>
  )
}

/**
 * A row as the ledger draws it: on the left the label and the text, with the
 * lines beneath indented to the text, and on the right the buttons and the ✕,
 * centred against all of the left side.
 */
function ledgerRow(d: Draw, row: Row, isLead: boolean) {
  const { Box, Button, Text } = d.p

  return (
    <Box key={row.key} gap={1} alignItems="center">
      <Box flexDirection="column" flexGrow={1} flexShrink={1}>
        <Box gap={1}>
          {labelCell(d, row, isLead, true)}
          {row.text.map((t, i) => (
            <Text key={`${row.key}-text-${i}`} dimColor={t.dim} tabular={t.tabular}>
              {t.text}
            </Text>
          ))}
        </Box>
        {row.details.map((t, i) => (
          <Box key={`${row.key}-detail-${i}`} gap={1}>
            {labelCell(d, row, isLead, false)}
            <Text dimColor={t.dim}>{t.text}</Text>
          </Box>
        ))}
      </Box>
      {row.actions.map((a) => (
        <Button key={a.key} label={a.label} variant={isLead && a.main === true ? 'primary' : undefined} onPress={a.onPress} />
      ))}
      <Button key={row.dismiss.key} label="✕" plain dimColor onPress={row.dismiss.onPress} />
    </Box>
  )
}

function failureRow($: EngineInterface, held: Failure): Row {
  return {
    key: 'failure',
    label: 'Failed',
    tone: 'error',
    text: [{ text: `${held.text}.` }],
    actions: held.retry === undefined ? [] : [{ key: 'failure-retry', label: 'Try again', main: true, onPress: () => retryFailure($) }],
    details: [],
    dismiss: { key: 'failure-dismiss', label: '✕', onPress: () => dismissFailure($) },
  }
}

/** The message the pre-send check held, its findings one per line beneath, and what the person can do with it. */
function heldRow($: EngineInterface, kept: PresendHeld): Row {
  const send = { key: 'presend-send', label: 'Send as is', main: kept.rewrite === null, onPress: () => sendAsIs($) }

  return {
    key: 'presend',
    label: 'Held',
    tone: 'warning',
    text: [{ text: 'Your message is back in the box.' }],
    actions: kept.rewrite === null ? [send] : [send, { key: 'presend-rewrite', label: 'Use the rewrite', main: true, onPress: () => useRewrite($) }],
    details: kept.findings.map((f) => ({ text: `· ${f}` })),
    dismiss: { key: 'presend-dismiss', label: '✕', onPress: () => dismissHeld($) },
  }
}

/** The owner's tagged items the last reply left without a closing line. */
function missedRow($: EngineInterface, missed: readonly TaggedItem[]): Row {
  return {
    key: 'missed',
    label: 'No line',
    tone: 'warning',
    text: [{ text: missed.map((i) => `${i.id} "${i.text}"`).join(' · ') }],
    actions: [],
    details: [],
    dismiss: { key: 'missed-dismiss', label: '✕', onPress: () => dismissMissed($) },
  }
}

function offerRow($: EngineInterface, offered: NewTaskState): Row {
  const actions: Action[] = []
  if (offered.stage === 'offered') {
    if (offered.effort !== undefined) {
      actions.push({ key: 'new-task-clear-effort', label: `Handoff, clear, effort ${offered.effort.level}`, main: true, onPress: () => handoffThenClear($, offered, true) })
    }
    actions.push({ key: 'new-task-clear', label: 'Handoff and clear', main: offered.effort === undefined, onPress: () => handoffThenClear($, offered, false) })
    actions.push({ key: 'new-task-here', label: 'Keep going here', onPress: () => keepGoing($) })
  }

  return {
    key: 'offer',
    label: 'New task',
    tone: 'warning',
    text: [{ text: newTaskBody(offered) }],
    actions,
    details: [],
    dismiss: { key: 'new-task-dismiss', label: '✕', onPress: () => dismissOffer($) },
  }
}

function chainRow($: EngineInterface, running: ChainState): Row {
  return {
    key: 'chain',
    label: 'Chain',
    tone: running.stage === 'waiting' && running.stopped !== undefined ? 'warning' : 'subtle',
    text: [{ text: stageLine(running) }],
    actions: [],
    details: [],
    dismiss: { key: 'chain-dismiss', label: '✕', onPress: () => dismissChain($) },
  }
}

/** The context row; `coldAt` is the cold-cache deadline when the row carries it, since its chain button is the one that timer would run. */
function figureRow($: EngineInterface, d: Draw, now: ContextFigure, grewBy: number, tier: number, coldAt: number): Row {
  const actions: Action[] = []
  if (!d.isWorking) {
    actions.push({ key: 'context-handoff', label: 'Handoff', main: !d.chainOn, onPress: () => handoffByPerson($) })
    if (d.chainOn) {
      actions.push({ key: 'context-chain', label: 'Handoff and compact', main: true, onPress: () => chainByPerson($) })
    }
  }

  return {
    key: 'figure',
    label: 'Context',
    tone: tier >= 2 ? 'error' : 'warning',
    text: [{ text: `${compact(now.tokens)} / ${compact(now.window)}  ${now.percent}%`, tabular: true }, ...(grewBy > 0 ? [{ text: `+${compact(grewBy)} last turn`, dim: true }] : [])],
    actions,
    details: coldAt === 0 ? [] : [{ text: coldClause(coldAt), dim: true }],
    dismiss: {
      key: 'context-dismiss',
      label: '✕',
      onPress: () => {
        dismissFigure($)
        if (coldAt !== 0) {
          dismissCold($)
        }
      },
    },
  }
}

function coldRow($: EngineInterface, d: Draw, at: number): Row {
  return {
    key: 'cold',
    label: 'Cache',
    tone: 'subtle',
    text: [{ text: coldText(at) }],
    actions: d.isWorking ? [] : [{ key: 'cold-run', label: 'Run chain now', main: true, onPress: () => runColdNow($) }],
    details: [],
    dismiss: { key: 'cold-dismiss', label: '✕', onPress: () => dismissCold($) },
  }
}

function limitRow($: EngineInterface, w: SessionRateLimit): Row {
  return {
    key: `limit-${w.kind}`,
    label: 'Usage',
    tone: w.percentUsed >= LIMIT_FIRM ? 'error' : 'warning',
    text: [{ text: limitFigures(w), tabular: true }],
    actions: [],
    details: [],
    dismiss: { key: `limit-dismiss-${w.kind}`, label: '✕', onPress: () => dismissLimit($, w) },
  }
}

/** The row that leads: the first whose own colour is not `subtle`, or the first row when none has one. */
function leadOf(rows: readonly Row[]): number {
  const coloured = rows.findIndex((r) => r.tone !== 'subtle')

  return coloured === -1 ? 0 : coloured
}

export const register: Register = (on, options) => {
  const { thresholdTokens, thresholdPercent, step, chainOn, statusLine } = readOptions(options)
  const limitFloor = statusLine ? LIMIT_FIRM : LIMIT_WARN

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const below = await next(e)
    const held = await read($, failure)
    const missed = await read($, itemsMissed)
    const kept = await read($, presendHeld)
    const offered = await read($, newTask)
    const running = await read($, chain)
    const now = await read($, figure)
    const dismissedAt = await read($, figureDismissedAt)
    const coldAt = await read($, coldTimerAt)
    const grewBy = await read($, turnGrowth)
    const marks = await read($, limitsDismissed)
    const limits = (await read($, rateLimits)).filter((w) => showsLimit(w, marks[w.kind], limitFloor))
    const trigger = now === null ? 0 : triggerTokens(thresholdTokens, thresholdPercent, now.window)
    const tier = now === null ? 0 : adviceTier(now.tokens, trigger)
    // Below the firmer tier the figure is the status line's alone: the band keeps what needs a decision.
    const past = now !== null && now.tokens >= trigger && tier >= 1 && !withinStep(dismissedAt, now.tokens, step)
    if (e.props.hasSurvey || (held === null && kept === null && missed.length === 0 && offered === null && running === null && !past && coldAt === 0 && limits.length === 0)) {
      return below
    }
    const { Box, Button, Text } = $.ui.resolve(e)
    const d: Draw = { p: { Box, Button, Text }, isWorking: e.props.isWorking, chainOn, labelWidth: 0 }
    // The context row offers the same chain the cache row would, so it takes the timer in.
    const foldsCold = chainOn && offered === null && running === null && past
    const rows: Row[] = []
    if (held !== null) {
      rows.push(failureRow($, held))
    }
    if (kept !== null) {
      rows.push(heldRow($, kept))
    }
    if (missed.length > 0) {
      rows.push(missedRow($, missed))
    }
    if (offered !== null) {
      rows.push(offerRow($, offered))
    } else if (running !== null) {
      rows.push(chainRow($, running))
    } else if (past && now !== null) {
      rows.push(figureRow($, d, now, grewBy, tier, foldsCold ? coldAt : 0))
    }
    if (coldAt !== 0 && !foldsCold) {
      rows.push(coldRow($, d, coldAt))
    }
    for (const w of limits) {
      rows.push(limitRow($, w))
    }
    const lead = leadOf(rows)
    const drawn = { ...d, labelWidth: Math.max(...rows.map((r) => r.label.length)) }
    // The left inset matches the room the plain ✕ leaves at the right; a gap goes under the kit's rows only when a band beneath follows them.
    const kit = (
      <Box flexDirection="column" rowGap="xs" paddingLeft={1}>
        {rows.map((r, i) => ledgerRow(drawn, r, i === lead))}
      </Box>
    )

    return below === null || below === undefined ? (
      kit
    ) : (
      <Box flexDirection="column" rowGap="xs">
        {kit}
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
