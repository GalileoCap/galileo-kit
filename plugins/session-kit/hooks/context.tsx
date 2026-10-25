// Context, in-process: the engine's own figure after every tool call, a
// warning to the model every `step` tokens past `thresholdTokens` (or past
// `threshold` percent of the window, whichever comes first), a band above the prompt with the figure for the person, and, with
// the `chain` option on, two tools: `clear_point`, after which the kit writes
// the handoff, compacts and continues when the turn ends, and `new_task`,
// after which the band offers the handoff and a clear, or to keep going here,
// and sends the person's prompt again.
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

import type { ChainState, ContextFigure, NewTaskState } from '../types'

const warnedAt = atom({ plugin: 'session-kit', key: 'contextWarnedAt' } as const, 0)
const figure = atom({ plugin: 'session-kit', key: 'contextFigure' } as const, null)
const chain = atom({ plugin: 'session-kit', key: 'chain' } as const, null)
const newTask = atom({ plugin: 'session-kit', key: 'newTask' } as const, null)
const lastPrompt = atom({ plugin: 'session-kit', key: 'lastPrompt' } as const, '')

const THRESHOLD_TOKENS = 250000
const STEP_TOKENS = 25000
const FIRMER_AT = 2
const STOP_AT = 3

const TOOL_NAME = 'clear_point'
const TOOL = 'mcp__session-kit__clear_point'
const NEW_TASK_NAME = 'new_task'
const NEW_TASK_TOOL = 'mcp__session-kit__new_task'
const HANDOFF_COMMAND = 'session-kit:handoff'
const CLEAR_COMMAND = 'clear'
const COMPACT_COMMAND = 'compact'
const COMPACT_TRIES = 20
const COMPACT_RETRY_MS = 1000

const TOOL_DESCRIPTION =
  'Call this at a clear point: the tree is committed and green, nothing is in ' +
  'flight, and the next step is known. When this turn ends, session-kit writes ' +
  'the handoff (CLAUDE.local.md), compacts the context, and continues with the ' +
  'next step, or stops when that step waits on the owner. Then end the turn ' +
  'with nothing more started.'

const NEW_TASK_DESCRIPTION =
  'Call this when the prompt just given is a task unrelated to the one in ' +
  'CLAUDE.local.md, before starting on it: one task per context. session-kit ' +
  'then offers the person the handoff and a clear, or to keep going here, and ' +
  'sends their prompt again after. Then end the turn, saying in one line that ' +
  'it is a new task, with nothing started.'

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

export function advice(tokens: number, trigger: number, chainOn = false): string {
  const close = chainOn
    ? `then call the ${TOOL_NAME} tool.`
    : 'then tell the user it is safe to compact.'
  if (tokens >= trigger * STOP_AT) {
    return (
      'Stop starting anything new. Commit or discard what is in the tree, ' +
      (chainOn
        ? `and call the ${TOOL_NAME} tool now.`
        : 'write CLAUDE.local.md now, and end this turn saying you are ready to compact.')
    )
  }
  if (tokens >= trigger * FIRMER_AT) {
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

export function warning(f: ContextFigure, trigger: number, chainOn = false): string {
  return `Context at ${f.tokens.toLocaleString('en-US')} tokens (${f.percent}% of ${f.window.toLocaleString('en-US')}). ${advice(f.tokens, trigger, chainOn)}`
}

/** Where the warning starts: the token count, or the percent of the window, whichever is reached first; 0 turns one off. */
export function triggerTokens(thresholdTokens: number, thresholdPercent: number, window: number): number {
  const byCount = thresholdTokens > 0 ? thresholdTokens : Infinity
  const byPercent = thresholdPercent > 0 ? (window * thresholdPercent) / 100 : Infinity
  const trigger = Math.min(byCount, byPercent)

  return Number.isFinite(trigger) ? trigger : THRESHOLD_TOKENS
}

function asNumber(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) && value > 0 ? value : fallback
}

function asCount(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : fallback
}

function reason(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

/** A registered tool answers with its text: the engine's output schema for one takes a string. */
function answer(text: string) {
  return { result: text }
}

function refuse(text: string) {
  return { deny: text }
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

/** Where a session's chain writes its stages: a host that draws no log line still leaves this file. */
export function journalPath(tempdir: string, sessionId: string): string {
  const safe = sessionId.replace(/[^\w-]/g, '_') || 'session'

  return `${tempdir.replace(/\/+$/, '')}/session-kit-chain-${safe}.log`
}

let journal: Promise<void> = Promise.resolve()

async function journalLine($: EngineInterface, line: string): Promise<void> {
  const path = journalPath((await $.env.get('TMPDIR')) ?? '/tmp', await $.session.id())
  let before = ''
  try {
    before = await $.fs.read(path)
  } catch {
    before = ''
  }
  await $.fs.write(path, `${before}${line}\n`)
}

/** One line per stage of a chain, in the transcript and in the session's chain file, so a run that stops can be read back. */
function stage($: EngineInterface, text: string): void {
  $.ui.log(`session-kit chain: ${text}`)
  journal = journal
    .then(async () => journalLine($, `${new Date(await $.clock.now()).toISOString()} ${text}`))
    .catch(() => undefined)
}

async function runHandoff($: EngineInterface): Promise<void> {
  stage($, 'running the handoff command')
  try {
    await $.command.run({ command: HANDOFF_COMMAND })
    stage($, 'the handoff command returned')
  } catch (error) {
    await update($, chain, () => null)
    stage($, `the handoff did not run (${reason(error)}), so the chain stops here`)
    $.ui.toast(`session-kit: the handoff did not run (${reason(error)}), so the chain stops here.`)
  }
}

async function compactThenContinue($: EngineInterface, state: ChainState, tries = COMPACT_TRIES): Promise<void> {
  let compacted
  try {
    compacted = await $.session.compact({ instructions: COMPACT_INSTRUCTIONS })
  } catch (error) {
    // The turn that just ended may not have let go yet: try again shortly.
    stage($, `the compaction was refused (${reason(error)}), ${tries - 1} tries left`)
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
    stage($, `the compaction was skipped (${compacted.skip}), so the chain stops here`)
    $.ui.toast(`session-kit: the compaction was skipped (${compacted.skip}), so the chain stops here.`)

    return
  }
  await afterCompaction($, state)
}

async function afterCompaction($: EngineInterface, state: ChainState): Promise<void> {
  if (state.waitsOnOwner) {
    await update($, chain, () => ({ ...state, stage: 'waiting' }))
    stage($, 'compacted, and waiting on the owner')

    return
  }
  await update($, chain, () => null)
  stage($, 'compacted, sending the continue prompt')
  await $.prompt.submit({ text: continuePrompt(state.note) })
}

/**
 * Where no person is at the prompt (the SDK, the desktop app), `$.session.compact`
 * is refused and a compaction runs inside a turn, so the chain runs `/compact`.
 */
async function compactByCommand($: EngineInterface, state: ChainState): Promise<void> {
  stage($, 'compacting through the /compact command, since no person is at the prompt')
  try {
    await $.command.run({ command: COMPACT_COMMAND, args: COMPACT_INSTRUCTIONS })
  } catch (error) {
    await update($, chain, () => null)
    stage($, `the /compact command did not run (${reason(error)}), so the chain stops here`)
    $.ui.toast(`session-kit: the compaction did not run (${reason(error)}), so the chain stops here.`)

    return
  }
  await afterCompaction($, state)
}

function newTaskLine(state: NewTaskState): string {
  switch (state.stage) {
    case 'offered':
      return `New task: ${state.task}`
    case 'handoff':
      return 'session-kit is writing the handoff before the clear.'
    case 'clearing':
      return 'Clearing the context, then sending your prompt again.'
  }
}

async function resend($: EngineInterface): Promise<void> {
  const text = await read($, lastPrompt)
  if (text !== '') {
    await $.prompt.submit({ text, asUser: true })
  }
}

async function keepGoing($: EngineInterface): Promise<void> {
  await update($, newTask, () => null)
  await resend($)
}

async function runHandoffBeforeClear($: EngineInterface): Promise<void> {
  try {
    await $.command.run({ command: HANDOFF_COMMAND })
  } catch (error) {
    await update($, newTask, () => null)
    $.ui.toast(`session-kit: the handoff did not run (${reason(error)}), so the context was not cleared.`)
  }
}

async function handoffThenClear($: EngineInterface, state: NewTaskState): Promise<void> {
  await update($, newTask, () => ({ ...state, stage: 'handoff' }))
  // Outside this dispatch: a command run inside a hook the turn waits on is refused.
  $.clock.after(0, () => {
    void runHandoffBeforeClear($)
  })
}

async function clearThenResend($: EngineInterface): Promise<void> {
  // The clear ends this session's state, so nothing is read from it after.
  await update($, newTask, () => null)
  try {
    await $.command.run({ command: CLEAR_COMMAND })
  } catch (error) {
    $.ui.toast(`session-kit: the clear did not run (${reason(error)}).`)

    return
  }
  await resend($)
}

export const register: Register = (on, options) => {
  const thresholdTokens = asCount(options.thresholdTokens, THRESHOLD_TOKENS)
  const thresholdPercent = asCount(options.threshold, 0)
  const step = asNumber(options.step, STEP_TOKENS)
  const chainOn = options.chain === true

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined || e.tool === TOOL || e.tool === NEW_TASK_TOOL) {
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

    const trigger = triggerTokens(thresholdTokens, thresholdPercent, context.window)
    if (now.tokens < trigger) {
      return ran
    }
    const warned = await read($, warnedAt)
    // A context smaller than the last warning has been compacted: warn afresh.
    if (warned && warned <= now.tokens && now.tokens < warned + step) {
      return ran
    }
    await update($, warnedAt, () => now.tokens)

    return { ...ran, context: [...(ran.context ?? []), warning(now, trigger, chainOn)] }
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
    const offered = await read($, newTask)
    const running = await read($, chain)
    const now = await read($, figure)
    const past = now !== null && now.tokens >= triggerTokens(thresholdTokens, thresholdPercent, now.window)
    if (e.props.hasSurvey || (offered === null && running === null && !past)) {
      return next(e)
    }
    const { Box, Button, Text } = $.ui.resolve(e)
    if (offered !== null) {
      return (
        <Box>
          <Text dimColor>{newTaskLine(offered)} </Text>
          {offered.stage === 'offered' ? (
            <Button key="new-task-clear" label="Handoff and clear" variant="primary" onPress={() => handoffThenClear($, offered)} />
          ) : null}
          {offered.stage === 'offered' ? (
            <Button key="new-task-here" label="Keep going here" onPress={() => keepGoing($)} />
          ) : null}
        </Box>
      )
    }
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
          Context {now?.tokens.toLocaleString('en-US')} tokens ({now?.percent}% of {now?.window.toLocaleString('en-US')}): find a clear point, commit, write the handoff, {chainOn ? `call ${TOOL_NAME}.` : 'ask to compact.'}
        </Text>
      </Box>
    )
  }).catch(($, e, next) => next(e))

  on('prompt.submit', async ($, e, next) => {
    if (e.origin?.kind !== 'plugin' && e.text.trim() !== '') {
      await update($, lastPrompt, () => e.text)
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  if (!chainOn) {
    return
  }

  let isInteractive = true
  on('session.start', async ($, e, next) => {
    isInteractive = e.isInteractive
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
    await $.tool.register({
      name: NEW_TASK_NAME,
      description: NEW_TASK_DESCRIPTION,
      inputSchema: {
        type: 'object',
        properties: { task: { type: 'string', description: 'The new task, in one line.' } },
        required: ['task'],
      },
      isDeferred: false,
    })

    return next(e)
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: NEW_TASK_TOOL }, async ($, e) => {
    const task = typeof e.task === 'string' && e.task.trim() !== '' ? e.task.trim() : ''
    if (task === '') {
      return refuse('task must name the new task in one line.')
    }
    await update($, newTask, () => ({ stage: 'offered', task }))

    return answer(
      'New task noted. Start nothing on it. End this turn now, saying in one line ' +
        'that it is a new task: the band offers the handoff and a clear, or to keep ' +
        'going here, and the prompt is sent again after.',
    )
  }).catch(() => refuse('session-kit could not record the new task.'))

  on('tool.call', { tool: TOOL }, async ($, e) => {
    const nextStep = e.next_step
    const note = typeof e.note === 'string' && e.note.trim() !== '' ? e.note.trim() : ''
    if ((nextStep !== 'session' && nextStep !== 'owner') || note === '') {
      return refuse('next_step must be "session" or "owner", and note the next step in one line.')
    }
    const waitsOnOwner = nextStep === 'owner'
    await update($, chain, () => ({ stage: 'requested', waitsOnOwner, note }))

    return answer(
      'Clear point noted. End this turn now, with nothing more started. When it ' +
        'ends, session-kit writes the handoff and compacts the context, then ' +
        (waitsOnOwner ? 'stops, since the next step is the owner\'s.' : `continues with: ${note}`),
    )
  }).catch(() => refuse('session-kit could not record the clear point, so the chain did not start.'))

  on('turn.complete', async ($, e, next) => {
    if (e.agentId !== undefined) {
      return next(e)
    }
    const offered = await read($, newTask)
    if (offered !== null) {
      if (e.reason !== 'answer') {
        await update($, newTask, () => null)
      } else if (offered.stage === 'handoff') {
        await update($, newTask, () => ({ ...offered, stage: 'clearing' }))
        $.clock.after(0, () => {
          void clearThenResend($)
        })
      }
    }
    const state = await read($, chain)
    if (state === null) {
      return next(e)
    }
    if (e.reason !== 'answer') {
      await update($, chain, () => null)
      stage($, `the turn ended by ${e.reason} at the ${state.stage} stage, so the chain stops here`)

      return next(e)
    }
    switch (state.stage) {
      case 'requested': {
        await update($, chain, () => ({ ...state, stage: 'handoff' }))
        stage($, 'the turn ended: writing the handoff')
        // Outside this dispatch: a command run inside a hook the turn waits on is refused.
        $.clock.after(0, () => {
          void runHandoff($)
        })
        break
      }
      case 'handoff': {
        await update($, chain, () => ({ ...state, stage: 'compacting' }))
        stage($, 'the handoff turn ended: compacting')
        $.clock.after(0, () => {
          void (isInteractive ? compactThenContinue($, state) : compactByCommand($, state))
        })
        break
      }
      case 'compacting':
        // Where the compaction is a /compact turn, its own end lands here.
        stage($, 'a turn ended while compacting')
        break
      default:
        // A turn ended with the chain waiting on the owner: the person moved on.
        await update($, chain, () => null)
        stage($, `a turn ended at the ${state.stage} stage, so the chain stops here`)
    }

    return next(e)
  }).catch(($, e, next) => next(e))
}
