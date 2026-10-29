// The kit's pane, drawn on every surface: the context with a bar, each usage
// window, the cache timer, the chain or the offer with the last lines of its
// journal, the handoff, the uncommitted files and the last test run. It shows
// what the band and the status line only name, and the facts the handoff
// carries, without a model turn. A `kit` chip in the footer's mode labels shows
// and hides it with one click, as `/kit` does, and the next session starts with
// the pane as the last press left it; the pane's own close mark hides it for
// this session alone. The validator cuts a line of its report at about a
// thousand characters (`A60`), so the pane and the chip share one drawing hook,
// and the context concern's `session.start` hook registers the command and
// opens the pane again with direct calls.

import { atom, read } from 'claude-code'
import type { EngineInterface, Register, SessionRateLimit } from 'claude-code'

import type { StageLine } from '../types'
import { handoffState, uncommitted } from './checkout'
import { bar, clip, clockTime, newTaskLine, stageLine, windowRow } from './lines'
import { verdictOf } from './test_log'

const NO_WINDOWS: SessionRateLimit[] = []
const NO_STAGES: StageLine[] = []

const chain = atom({ plugin: 'session-kit', key: 'chain' } as const, null)
const coldTimerAt = atom({ plugin: 'session-kit', key: 'coldTimerAt' } as const, 0)
const failure = atom({ plugin: 'session-kit', key: 'failure' } as const, null)
const figure = atom({ plugin: 'session-kit', key: 'contextFigure' } as const, null)
const newTask = atom({ plugin: 'session-kit', key: 'newTask' } as const, null)
const rateLimits = atom({ plugin: 'session-kit', key: 'rateLimits' } as const, NO_WINDOWS)
const stages = atom({ plugin: 'session-kit', key: 'stages' } as const, NO_STAGES)
const turnGrowth = atom({ plugin: 'session-kit', key: 'turnGrowth' } as const, 0)

const lastTest = atom({ plugin: 'session-kit', key: 'lastTest' } as const, null)

export const PANE = 'kit'
export const PANE_TITLE = 'session-kit'
export const COMMAND = 'kit'
export const COMMAND_DESCRIPTION = 'Show or hide the session-kit pane: context, usage windows, chain and checks'
const COMMAND_SHOWN = 60
// The `$.store` key that keeps, across sessions, whether the person left the pane open.
export const KEPT_OPEN = 'paneOpen'

/** The checkout's two facts, or `unknown` where git or the file system cannot say. */
async function checkout($: EngineInterface): Promise<{ handoff: string; changes: string }> {
  try {
    const cwd = await $.session.cwd()
    const files = await uncommitted($, cwd)

    return { handoff: await handoffState($, cwd), changes: `${files.length} ${files.length === 1 ? 'file' : 'files'}` }
  } catch {
    return { handoff: 'unknown', changes: 'unknown' }
  }
}

async function testLine($: EngineInterface): Promise<string> {
  const last = await read($, lastTest)
  if (last === null) {
    return 'Last test: none'
  }
  let verdict = 'UNKNOWN'
  try {
    verdict = await verdictOf($, await $.session.cwd(), last)
  } catch {
    // The verdict stays unknown where the tree cannot be read.
  }

  return `Last test: ${verdict} ${clip(last.command, COMMAND_SHOWN)}, ${clockTime(new Date(last.at))}`
}

async function chainLine($: EngineInterface): Promise<string> {
  const held = await read($, failure)
  if (held !== null) {
    return `Failed: ${held.text}.`
  }
  const offered = await read($, newTask)
  if (offered !== null) {
    return newTaskLine(offered)
  }
  const running = await read($, chain)

  return running === null ? 'Idle' : stageLine(running)
}

/** Opens the pane where it is closed and closes it where it is open, and keeps the choice for the next session. */
async function toggle($: EngineInterface): Promise<string> {
  const isUp = (await $.ui.panes()).some((pane) => pane.id === PANE)
  await $.store.set(KEPT_OPEN, !isUp)
  if (isUp) {
    await $.ui.close({ id: PANE })

    return 'The session-kit pane is hidden.'
  }
  const opened = await $.ui.open({ id: PANE, title: PANE_TITLE })

  return opened.isPlaced ? 'The session-kit pane is open.' : `The session-kit pane waits for room: ${opened.reason}`
}

export const register: Register = (on) => {
  on('command.run', { command: COMMAND }, async ($) => ({ text: await toggle($) })).catch(() => ({ text: 'The session-kit pane could not be opened.' }))

  on('ui.render', { component: /^(Pane|SessionMode)$/ }, async ($, e, next) => {
    if (e.component === 'SessionMode') {
      const { Box, Button } = $.ui.resolve(e)

      return (
        <Box gap={1}>
          {await next(e)}
          <Button key="kit-pane" plain label="kit" onPress={async () => { await toggle($) }} />
        </Box>
      )
    }
    if (e.requestId !== PANE) {
      return next(e)
    }
    const { Box, Text } = $.ui.resolve(e)
    const now = await read($, figure)
    const grewBy = await read($, turnGrowth)
    const windows = await read($, rateLimits)
    const coldAt = await read($, coldTimerAt)
    const journal = await read($, stages)
    const checks = await checkout($)

    return (
      <Box flexDirection="column">
        <Text bold>Context</Text>
        {now === null ? (
          <Text dimColor>Not measured yet</Text>
        ) : (
          <Box flexDirection="column">
            <Text tabular>{`${now.tokens.toLocaleString('en-US')} / ${now.window.toLocaleString('en-US')} tokens (${now.percent}%)`}</Text>
            <Text>{bar(now.percent)}</Text>
            {grewBy > 0 ? <Text dimColor>{`+${grewBy.toLocaleString('en-US')} tokens in the last turn`}</Text> : null}
          </Box>
        )}
        <Text bold>Usage</Text>
        {windows.length === 0 ? <Text dimColor>No usage windows</Text> : windows.map((w) => <Text tabular>{windowRow(w)}</Text>)}
        <Text bold>Cache</Text>
        <Text>{coldAt === 0 ? 'No timer' : `Compacts at ${clockTime(new Date(coldAt))}`}</Text>
        <Text bold>Chain</Text>
        <Text>{await chainLine($)}</Text>
        {journal.map((s) => (
          <Text dimColor>{`${clockTime(new Date(s.at))}  ${s.text}`}</Text>
        ))}
        <Text bold>Checks</Text>
        <Text>{`Handoff: ${checks.handoff}`}</Text>
        <Text>{`Uncommitted: ${checks.changes}`}</Text>
        <Text>{await testLine($)}</Text>
      </Box>
    )
  }).catch(($, e, next) => next(e))
}
