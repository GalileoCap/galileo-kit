// The kit's pane, opened by `/kit` and drawn on every surface: the context
// with a bar, each usage window, the cache timer, the chain or the offer with
// the last lines of its journal, the handoff, the uncommitted files and the last
// test run. It shows what the band and the status line only name, and the
// facts the handoff carries, without a model turn.

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

const PANE = 'kit'
const COMMAND = 'kit'
const COMMAND_SHOWN = 60

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

/** Registers `/kit`; the context concern calls it from its one `session.start` hook, since a module may hook that event once. */
export async function registerKitCommand($: EngineInterface): Promise<void> {
  await $.command.register({ name: COMMAND, description: 'Show the context, usage windows, chain and checks of session-kit in a pane' })
}

export const register: Register = (on) => {
  on('command.run', { command: COMMAND }, async ($) => {
    const opened = await $.ui.open({ id: PANE, title: 'session-kit' })

    return { text: opened.isPlaced ? 'The session-kit pane is open.' : `The session-kit pane waits for room: ${opened.reason}` }
  }).catch(() => ({ text: 'The session-kit pane could not be opened.' }))

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
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
