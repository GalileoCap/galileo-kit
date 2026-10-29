// Context, in-process: the engine's own figure after every tool call, with
// the tool output landed since the engine last measured counted on top, a
// warning to the model every `step` tokens past `thresholdTokens` (or past
// `threshold` percent of the window, whichever comes first), a band above the prompt with the figure for the person, and, with
// the `chain` option on, two tools: `clear_point`, after which the kit writes
// the handoff, compacts and continues when the turn ends, and `new_task`,
// after which the band offers the handoff and a clear, or to keep going here,
// and sends the person's prompt again. In a context that holds no task yet
// (new, or just cleared) `new_task` offers nothing: there is nothing to clear.
// The band itself is drawn in band.tsx, the status line in status.ts and the
// pane in pane.tsx. This file keeps the state they read and the actions their
// buttons run: `Handoff` and `Handoff and compact` (the person's own signal,
// which starts the chain with the next step theirs), `Run chain now`, and
// `Try again` on a failure that stays on the band until dismissed. A chain's
// failure and the end of a compaction with the next step the owner's also go
// to the person's notifications. A chain goes on by itself, and at
// the third, the fifth and every signal from the seventh since the person's
// last prompt a Haiku judge reads the owner's task, the steps so far, the
// commits between and the step proposed. When the session is going round, or
// the step goes beyond the task, the chain stops after its compaction and the
// next step is the owner's. A prompt that is not the person's own words (a
// notification, a schedule, a peer, a plugin) neither counts as theirs nor is
// sent again in their place. With the chain on, a turn that ends past the
// floor with nobody at the prompt arms the cold-cache timer: a lead before
// the prompt cache's lifetime runs out, the kit writes the handoff and
// compacts, and stops there, so the person's next prompt writes a small
// context to the cache instead of all of it. The lifetime is an option, 60
// minutes on a subscription, and what the engine states (a subagent's
// result, a model switch) replaces it. A 5-minute cache arms no timer. The
// figure's line says how much the context grew over the last turn, read at
// the turn's end, and a usage window of the plan at 80% gets a line of its
// own, naming when it resets, which dismissed stays away until 95%, and from
// there until the window resets. Where a surface draws no band (the phone,
// VS Code), the moments that matter go out as a toast instead: the warning,
// a window reaching 80 or 95, a new task named, a clear point signalled and
// the compaction done, and the cold-cache timer firing.
//
// The model is the one that knows where a clear point is, so the warning
// goes to it, on the tool result, while it can still choose where to stop,
// and the chain starts on its signal and never on the kit's own judgement.
// The end of a turn is left alone: a held stop costs every long turn a
// closing paragraph. Nothing here blocks a tool call. A hook that fails is
// replaced by what ran beneath it, so the kit is never the reason a call
// fails.

import { atom, read, update } from 'claude-code'
import type { EngineInterface, PromptOrigin, Register, RenderSurface, SessionContextUsage, SessionRateLimit, Timer, TurnCompleteInput } from 'claude-code'

import type { ChainState, ChainStep, ContextFigure, Effort, Failure, NewTaskState, StageLine, TurnFigure } from '../types'
import { gitOutput } from './checkout'
import { registerKitCommand } from './pane'
import { clip, limitLine, limitTier, sameWindows, sentence, stageLine } from './lines'
import { readOptions, triggerTokens, withinStep } from './options'
import type { ColdOptions } from './options'
import { holdStatus, refreshStatus } from './status'

const NO_WINDOWS: SessionRateLimit[] = []
const NO_MARKS: Record<string, number> = {}
const NO_STEPS: ChainStep[] = []
const NO_STAGES: StageLine[] = []
const NO_TURNS: TurnFigure[] = []

const warnedAt = atom({ plugin: 'session-kit', key: 'contextWarnedAt' } as const, 0)
const figure = atom({ plugin: 'session-kit', key: 'contextFigure' } as const, null)
const chain = atom({ plugin: 'session-kit', key: 'chain' } as const, null)
const chainSteps = atom({ plugin: 'session-kit', key: 'chainSteps' } as const, NO_STEPS)
const newTask = atom({ plugin: 'session-kit', key: 'newTask' } as const, null)
const sessionEffort = atom({ plugin: 'session-kit', key: 'sessionEffort' } as const, null)
const lastPrompt = atom({ plugin: 'session-kit', key: 'lastPrompt' } as const, '')
const lastPromptAt = atom({ plugin: 'session-kit', key: 'lastPromptAt' } as const, 0)
const freshContext = atom({ plugin: 'session-kit', key: 'freshContext' } as const, false)
const figureDismissedAt = atom({ plugin: 'session-kit', key: 'contextDismissedAt' } as const, 0)
const coldTimerAt = atom({ plugin: 'session-kit', key: 'coldTimerAt' } as const, 0)
const statedCacheMinutes = atom({ plugin: 'session-kit', key: 'cacheMinutes' } as const, 0)
const turnEndTokens = atom({ plugin: 'session-kit', key: 'turnEndTokens' } as const, 0)
const turnGrowth = atom({ plugin: 'session-kit', key: 'turnGrowth' } as const, 0)
const rateLimits = atom({ plugin: 'session-kit', key: 'rateLimits' } as const, NO_WINDOWS)
const limitsDismissed = atom({ plugin: 'session-kit', key: 'limitsDismissed' } as const, NO_MARKS)
const failure = atom({ plugin: 'session-kit', key: 'failure' } as const, null)
const stages = atom({ plugin: 'session-kit', key: 'stages' } as const, NO_STAGES)
const turnFigures = atom({ plugin: 'session-kit', key: 'turnFigures' } as const, NO_TURNS)

const STAGES_KEPT = 8
const TURNS_KEPT = 40
const STAGE_TEXT_SHOWN = 300
const FIRMER_AT = 1.2
const STOP_AT = 1.6
const JUDGE_MODEL = 'haiku'
const JUDGE_MAX_TOKENS = 200
const JUDGE_TIMEOUT_MS = 30000
const TEXT_SHOWN = 2000
const COMMITS_SHOWN = 12
const SUBJECT_SHOWN = 200
const MINUTE_MS = 60000
// Tool output costs 2.42 characters a token over 669 pairs of requests in the
// transcripts on disk, and never more than 3.21: at 3.5 the projection stays
// below the engine's next figure, so a measurement never reads as a compaction.
const CHARS_PER_TOKEN = 3.5

// The kinds of prompt that are not the person's own words. What a plugin's
// `$.command.run` stamps is `plugin` too. The rest (typed, from the phone, the
// SDK host's, a channel's, a Slack ping, one the engine could not stamp) stay
// the person's, since which of them a desktop stamps is not known.
const NOT_THE_PERSONS: ReadonlySet<PromptOrigin['kind']> = new Set([
  'plugin',
  'task-notification',
  'scheduled-trigger',
  'peer',
  'peer-send-message',
  'projects-relay',
  'coordinator',
  'observer',
  'observer-activity',
  'auto-continuation',
])

const TOOL_NAME = 'clear_point'
const TOOL = 'mcp__session-kit__clear_point'
const NEW_TASK_NAME = 'new_task'
const NEW_TASK_TOOL = 'mcp__session-kit__new_task'
const HANDOFF_COMMAND = 'session-kit:handoff'
const CLEAR_COMMAND = 'clear'
const COMPACT_COMMAND = 'compact'
const EFFORT_COMMAND = 'effort'
const EFFORTS: readonly Effort[] = ['low', 'medium', 'high', 'xhigh', 'max']

const TOOL_DESCRIPTION =
  'Call this at a clear point: the tree is committed and green, nothing is in ' +
  'flight, and the next step is known. When this turn ends, session-kit writes ' +
  'the handoff (CLAUDE.local.md), compacts the context, and continues with the ' +
  'next step, or stops when that step waits on the owner. Then end the turn ' +
  'with nothing more started.'

const NEW_TASK_DESCRIPTION =
  'Call this when the prompt just given is a task unrelated to the task this ' +
  'context holds, before starting on it: one task per context. session-kit ' +
  'then offers the person the handoff and a clear, or to keep going here, and ' +
  'sends their prompt again after. Then end the turn, saying in one line that ' +
  'it is a new task, with nothing started. A context that holds no task yet ' +
  '(new, or just cleared) takes the prompt as its task, whatever ' +
  'CLAUDE.local.md describes. When the new task needs another effort than ' +
  'this session runs at, name it with its reason: the person may take it ' +
  'with the clear, and never in this context.'

const NOTHING_TO_CLEAR =
  'This context holds no other task (it is new, or just cleared), so there is ' +
  'nothing to clear: start on the prompt. CLAUDE.local.md still describes the ' +
  'last task, and the next handoff rewrites it for this one.'

const JUDGE_SYSTEM =
  'You judge whether an autonomous coding session should go on by itself while ' +
  'its owner is away. Answer with one line: CONTINUE, LOOP or BEYOND, then a ' +
  'colon and one sentence saying why.'

const JUDGE_RULES =
  'Answer LOOP when the session is going round: the same step again, steps that ' +
  'undo each other, or a fix tried again that keeps failing, with nothing ' +
  'committed between. Answer BEYOND when the proposed step goes further than the ' +
  'owner\'s task asked: work the task does not name, or a decision that is the ' +
  'owner\'s (publishing, pushing, installing, choosing between options the owner ' +
  'has not chosen, approving its own work). Otherwise answer CONTINUE.'

const COLD_NOTE = 'go on from the handoff, written before the cache went cold'
const PRESSED_NOTE = 'go on from the handoff, written at your request'

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

export function continuePrompt(note: string): string {
  return (
    'Continue. Read again in full the documents CLAUDE.local.md lists, then ' +
    `take its next step: ${note}`
  )
}

/** 0 from the trigger, 1 once the model is to end the turn at the next green commit, 2 once it is to stop starting anything. */
export function adviceTier(tokens: number, trigger: number): number {
  if (tokens >= Math.round(trigger * STOP_AT)) {
    return 2
  }

  return tokens >= Math.round(trigger * FIRMER_AT) ? 1 : 0
}

export function advice(tokens: number, trigger: number, chainOn = false): string {
  const close = chainOn
    ? `then call the ${TOOL_NAME} tool.`
    : 'then tell the user it is safe to compact.'
  const tier = adviceTier(tokens, trigger)
  if (tier === 2) {
    return (
      'Stop starting anything new. Commit or discard what is in the tree, ' +
      (chainOn
        ? `and call the ${TOOL_NAME} tool now.`
        : 'write CLAUDE.local.md now, and end this turn saying you are ready to compact.')
    )
  }
  if (tier === 1) {
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

/** The band's line for the person: the figure, how much the last turn grew it when it did, and what to do. */
function figureLine(f: ContextFigure, grewBy: number, chainOn: boolean): string {
  const growth = grewBy > 0 ? `, up ${grewBy.toLocaleString('en-US')} in the last turn` : ''
  const close = chainOn ? `call ${TOOL_NAME}.` : 'ask to compact.'

  return `Context ${f.tokens.toLocaleString('en-US')} tokens (${f.percent}% of ${f.window.toLocaleString('en-US')})${growth}: find a clear point, commit, write the handoff, ${close}`
}

/** The band is raised on the terminal and desktop surfaces only. */
function drawsBand(surface: RenderSurface): boolean {
  return surface === 'terminal' || surface === 'desktop'
}

/** A moment the band would show, sent as a toast where a surface draws no band; an engine that cannot say gets none. */
async function moment($: EngineInterface, text: string): Promise<void> {
  let surfaces: readonly RenderSurface[]
  try {
    surfaces = await $.session.surfaces()
  } catch {
    return
  }
  if (surfaces.some((s) => !drawsBand(s))) {
    $.ui.toast(text)
  }
}

// The engine measures the context once per request, so a step of parallel
// reads lands whole before its figure moves. The projection counts on top of
// the context the last main-loop request was answered over, read from the
// step's own usage, so it holds whenever the engine moves its figure. It is
// null until a step is measured and again from a turn's end, where the
// engine's figure stands in. `landed` is what reached the context since that
// request was sent: the response's output, then each main-loop tool's result
// and context.
let answeredOver: number | null = null
let landed = 0

/** What a tool call puts into the next request, in tokens: the result as the model reads it and the context beside it. */
function tokensLanded(ran: { text?: string; context?: readonly string[] }): number {
  const chars = (ran.text?.length ?? 0) + (ran.context ?? []).reduce((n, c) => n + c.length, 0)

  return Math.ceil(chars / CHARS_PER_TOKEN)
}

/** The figure the next request will carry as far as the kit can tell; the engine's own while nothing has landed on a measured step. */
function projected(context: SessionContextUsage): ContextFigure | null {
  if (answeredOver === null && landed === 0) {
    return context.tokens === undefined || context.percent === undefined ? null : { tokens: context.tokens, window: context.window, percent: context.percent }
  }
  const base = answeredOver ?? context.tokens
  if (base === undefined) {
    return null
  }
  const tokens = base + landed

  return { tokens, window: context.window, percent: Math.round((tokens * 100) / context.window) }
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

/**
 * Whether a prompt about to enter opens a context that holds no task: the
 * person has sent none in it and the model has answered none. A compacted
 * context holds its summary's task, and an engine that cannot say counts as
 * holding one, so the offer stays as it was.
 */
async function opensFreshContext($: EngineInterface): Promise<boolean> {
  try {
    if ((await $.session.turns()) !== 0) {
      return false
    }

    return !(await $.session.messages()).some((m) => m.role === 'assistant')
  } catch {
    return false
  }
}

/** Whether a prompt is the person's own words, which a clear sends again in their place and which lets a chain run again. */
export function isThePersons(origin: PromptOrigin | undefined): boolean {
  return origin === undefined || !NOT_THE_PERSONS.has(origin.kind)
}

/** A registered tool answers with its text: the engine's output schema for one takes a string. */
function answer(text: string) {
  return { result: text }
}

function refuse(text: string) {
  return { deny: text }
}

/** Whether the chain's nth signal since the person's last prompt goes to the judge: the third, the fifth, and every one from the seventh. */
export function judgedAt(n: number): boolean {
  return n === 3 || n === 5 || n >= 7
}

type Judgement = { verdict: 'CONTINUE' | 'LOOP' | 'BEYOND' | null; reason: string }

/** The verdict at the reply's start, bold or not, and the reason after it; null when the reply names none. */
export function readVerdict(text: string): Judgement | null {
  const said = /^\s*\**\s*(CONTINUE|LOOP|BEYOND)\b\**\s*[:.-]?\s*([\s\S]*)$/i.exec(text)
  if (said === null) {
    return null
  }
  const verdict = (said[1] ?? '').toUpperCase()

  return verdict === 'CONTINUE' || verdict === 'LOOP' || verdict === 'BEYOND'
    ? { verdict, reason: clip((said[2] ?? '').split('\n')[0] ?? '', TEXT_SHOWN) }
    : null
}

/** Why the chain stops, as the band and the model read it. */
function stopReason(j: Judgement): string {
  switch (j.verdict) {
    case 'LOOP':
      return `the session is going round: ${sentence(j.reason)}`
    case 'BEYOND':
      return `the next step goes beyond the owner's task: ${sentence(j.reason)}`
    default:
      return `the judge gave no verdict (${j.reason}), and an unjudged chain waits for the owner.`
  }
}

/** The task section of the handoff, the owner's words the chain is held to. */
function taskSection(text: string): string | null {
  const lines = text.split('\n')
  const start = lines.findIndex((line) => /^##\s+Task\s*$/.test(line))
  if (start < 0) {
    return null
  }
  const rest = lines.slice(start + 1)
  const end = rest.findIndex((line) => /^##\s/.test(line))
  const body = (end < 0 ? rest : rest.slice(0, end)).join('\n').trim()

  return body === '' ? null : body
}

type Evidence = { task: string; lastPrompt: string; steps: readonly ChainStep[]; commits: string[]; head: string | null; note: string }

export function judgePrompt(ev: Evidence): string {
  const at = (head: string | null) => (head === null ? '' : ` (at commit ${head})`)
  const steps = ev.steps.map((s, i) => `${i + 1}.${at(s.head)} ${s.note}`).join('\n')
  const commits = ev.commits.length === 0 ? 'none' : ev.commits.map((c) => `- ${c}`).join('\n')

  return [
    `The owner's task, in their words:\n${ev.task}`,
    `The owner's last prompt:\n${ev.lastPrompt === '' ? '(none recorded)' : ev.lastPrompt}`,
    `Since that prompt the session has compacted its context and gone on by itself ${ev.steps.length} times, each time naming its next step:\n${steps}`,
    `Commits since the first of those:\n${commits}`,
    `Now${at(ev.head)} it proposes to go on with:\n${ev.note}`,
    JUDGE_RULES,
  ].join('\n\n')
}

/** Where a session's chain writes its stages: a host that draws no log line still leaves this file. */
export function journalPath(tempdir: string, sessionId: string): string {
  const safe = sessionId.replace(/[^\w-]/g, '_') || 'session'

  return `${tempdir.replace(/\/+$/, '')}/session-kit-chain-${safe}.log`
}

let journal: Promise<void> = Promise.resolve()

// Counts the person's dismissals of the chain's band, so a compaction already
// asked for when one lands continues nothing after it.
let chainDismissals = 0

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
    .then(async () => {
      const at = await $.clock.now()
      await journalLine($, `${new Date(at).toISOString()} ${text}`)
      await update($, stages, (kept) => [...kept, { at, text: clip(text, STAGE_TEXT_SHOWN) }].slice(-STAGES_KEPT))
    })
    .catch(() => undefined)
}

/** A failure the band holds until the person dismisses it, and a toast where no band is drawn. A chain's failure also reaches the person who is away. */
async function failed($: EngineInterface, text: string, retry?: Failure['retry']): Promise<void> {
  const held: Failure = retry === undefined ? { text } : { text, retry }
  await update($, failure, () => held)
  await moment($, `session-kit: ${sentence(text)}`)
  if (retry !== undefined) {
    await notifyOwner($, `session-kit: ${sentence(text)}`)
  }
}

/** A message to the person's notifications, for an end they may not be there to see; a channel that cannot send is not an error. */
async function notifyOwner($: EngineInterface, text: string): Promise<void> {
  try {
    await $.ui.notify(text)
  } catch {
    // Nothing else to do: the band holds the same words.
  }
}

async function gitLines($: EngineInterface, args: string[]): Promise<string[] | null> {
  const out = await gitOutput($, await $.session.cwd(), args)

  return out === null ? null : out.split('\n').filter((line) => line.trim() !== '')
}

async function headOf($: EngineInterface): Promise<string | null> {
  return (await gitLines($, ['rev-parse', '--short', 'HEAD']))?.[0]?.trim() ?? null
}

async function ownerTask($: EngineInterface): Promise<string> {
  try {
    const cwd = (await $.session.cwd()).replace(/\/+$/, '')
    const task = taskSection(await $.fs.read(`${cwd}/CLAUDE.local.md`))

    return task === null ? '(CLAUDE.local.md has no Task section)' : clip(task, TEXT_SHOWN)
  } catch {
    return '(no CLAUDE.local.md)'
  }
}

/** The judge's word on the step proposed, from the owner's task, their last prompt, the steps so far and the commits between. */
async function judgeChain($: EngineInterface, steps: readonly ChainStep[], note: string): Promise<Judgement> {
  const head = await headOf($)
  const first = steps.find((s) => s.head !== null)?.head ?? null
  const log = first === null ? null : await gitLines($, ['log', '--format=%h %s', `-n${COMMITS_SHOWN}`, `${first}..HEAD`])
  const prompt = judgePrompt({
    task: await ownerTask($),
    lastPrompt: clip(await read($, lastPrompt), TEXT_SHOWN),
    steps,
    commits: (log ?? []).map((line) => clip(line, SUBJECT_SHOWN)),
    head,
    note,
  })
  try {
    const r = await $.model.complete({ model: JUDGE_MODEL, system: JUDGE_SYSTEM, prompt, maxTokens: JUDGE_MAX_TOKENS, timeoutMs: JUDGE_TIMEOUT_MS })
    if (!r.isAnswered) {
      return { verdict: null, reason: r.reason }
    }

    return readVerdict(r.text) ?? { verdict: null, reason: 'its reply named none' }
  } catch (error) {
    return { verdict: null, reason: reason(error) }
  }
}

async function runHandoff($: EngineInterface): Promise<void> {
  stage($, 'running the handoff command')
  try {
    await $.command.run({ command: HANDOFF_COMMAND })
    stage($, 'the handoff command returned')
  } catch (error) {
    const state = await read($, chain)
    await update($, chain, () => null)
    stage($, `the handoff did not run (${reason(error)}), so the chain stops here`)
    await failed($, `the handoff did not run (${reason(error)}), so the chain stopped`, state === null ? undefined : { stage: 'handoff', waitsOnOwner: state.waitsOnOwner, note: state.note })
  }
}

async function afterCompaction($: EngineInterface, state: ChainState, asOf: number): Promise<void> {
  if (asOf !== chainDismissals) {
    stage($, 'compacted after the band was dismissed, so nothing continues')

    return
  }
  if (state.waitsOnOwner) {
    const waiting: ChainState = { ...state, stage: 'waiting' }
    await update($, chain, () => waiting)
    stage($, 'compacted, and waiting on the owner')
    await moment($, stageLine(waiting))
    await notifyOwner($, `session-kit: compacted, the next step is yours: ${state.note}`)

    return
  }
  await update($, chain, () => null)
  const step: ChainStep = { note: state.note, head: await headOf($) }
  await update($, chainSteps, (steps) => [...steps, step])
  stage($, 'compacted, sending the continue prompt')
  await $.prompt.submit({ text: continuePrompt(state.note) })
}

/**
 * The chain compacts by running `/compact` in every session, which the engine
 * queues until the session is idle. `$.session.compact` rejects while a turn
 * runs, and where no person is at the prompt (the SDK, the desktop app) it is
 * refused outright. A command's result carries no veto, so the chain file
 * keeps what `/compact` printed.
 */
async function compactByCommand($: EngineInterface, state: ChainState, asOf: number): Promise<void> {
  if (asOf !== chainDismissals) {
    return
  }
  stage($, 'compacting through the /compact command')
  let printed
  try {
    printed = (await $.command.run({ command: COMPACT_COMMAND, args: COMPACT_INSTRUCTIONS })).text?.trim() ?? ''
  } catch (error) {
    await update($, chain, () => null)
    stage($, `the /compact command did not run (${reason(error)}), so the chain stops here`)
    await failed($, `the compaction did not run (${reason(error)}), so the chain stopped`, { stage: 'compacting', waitsOnOwner: state.waitsOnOwner, note: state.note })

    return
  }
  stage($, printed === '' ? 'the /compact command returned' : `the /compact command returned: ${clip(printed, SUBJECT_SHOWN)}`)
  await afterCompaction($, state, asOf)
}

export async function dismissChain($: EngineInterface): Promise<void> {
  chainDismissals += 1
  await update($, chain, () => null)
  stage($, 'the person dismissed the band, so the chain stops here')
}

export async function dismissFigure($: EngineInterface): Promise<void> {
  const now = await read($, figure)
  await update($, figureDismissedAt, () => now?.tokens ?? 0)
}

export async function dismissOffer($: EngineInterface): Promise<void> {
  await update($, newTask, () => null)
}

export async function dismissLimit($: EngineInterface, w: SessionRateLimit): Promise<void> {
  await update($, limitsDismissed, (marks) => ({ ...marks, [w.kind]: w.percentUsed }))
}

// The cold-cache timer under way; a hot reload drops it, and the next
// session.start sets it again from the deadline kept in `$.state`.
let coldTimer: Timer | null = null

/** The cache's lifetime a subagent's result states, by the split of its cache writes; null when it wrote none. */
function lifetimeStated(result: unknown): number | null {
  if (typeof result !== 'object' || result === null || !('usage' in result)) {
    return null
  }
  const { usage } = result
  if (typeof usage !== 'object' || usage === null || !('cache_creation' in usage)) {
    return null
  }
  const split = usage.cache_creation
  if (typeof split !== 'object' || split === null) {
    return null
  }
  const hour = 'ephemeral_1h_input_tokens' in split ? split.ephemeral_1h_input_tokens : 0
  const minutes = 'ephemeral_5m_input_tokens' in split ? split.ephemeral_5m_input_tokens : 0
  if (typeof hour === 'number' && hour > 0) {
    return 60
  }

  return typeof minutes === 'number' && minutes > 0 ? 5 : null
}

/** The cold-cache deadline, kept with the status line that names it. */
async function setColdAt($: EngineInterface, at: number): Promise<void> {
  await update($, coldTimerAt, () => at)
  await refreshStatus($)
}

async function disarmCold($: EngineInterface): Promise<void> {
  coldTimer?.cancel()
  coldTimer = null
  if ((await read($, coldTimerAt)) !== 0) {
    await setColdAt($, 0)
  }
}

export async function dismissCold($: EngineInterface): Promise<void> {
  await disarmCold($)
  stage($, 'the person dismissed the cold-cache timer, so nothing runs before their next turn ends')
}

/** With nobody at the prompt for the lead, the chain runs from the handoff stage and stops after the compaction. */
async function runColdChain($: EngineInterface, lead: number): Promise<void> {
  coldTimer = null
  await setColdAt($, 0)
  const text = `the cache goes cold in ${lead} minutes with nobody at the prompt: writing the handoff`
  if (await beginChain($, COLD_NOTE, text)) {
    await moment($, `session-kit: ${text}.`)
  }
}

/** The chain from its handoff stage, stopping after the compaction since the next step is the owner's; false when a chain or an offer is under way. */
async function beginChain($: EngineInterface, note: string, why: string): Promise<boolean> {
  if ((await read($, chain)) !== null || (await read($, newTask)) !== null) {
    return false
  }
  await update($, failure, () => null)
  await update($, chain, () => ({ stage: 'handoff', waitsOnOwner: true, note }))
  stage($, why)
  await runHandoff($)

  return true
}

// Outside the press's dispatch: a command run inside a hook the turn waits on is refused.
function later($: EngineInterface, run: () => Promise<void>): void {
  $.clock.after(0, () => {
    void run()
  })
}

/** The person's own signal: the handoff, then the compaction, and the next step is theirs. */
export async function chainByPerson($: EngineInterface): Promise<void> {
  later($, async () => {
    await beginChain($, PRESSED_NOTE, 'the person asked for the handoff and the compaction')
  })
}

/** The cold-cache timer run now by the person, in place of the lead's wait. */
export async function runColdNow($: EngineInterface): Promise<void> {
  await disarmCold($)
  await chainByPerson($)
}

export async function handoffByPerson($: EngineInterface): Promise<void> {
  later($, async () => {
    stage($, 'the person asked for the handoff')
    try {
      await $.command.run({ command: HANDOFF_COMMAND })
    } catch (error) {
      await failed($, `the handoff did not run (${reason(error)})`)
    }
  })
}

export async function dismissFailure($: EngineInterface): Promise<void> {
  await update($, failure, () => null)
}

/** A chain's failure run again from its stage, with the note and the owner's say it had. */
export async function retryFailure($: EngineInterface): Promise<void> {
  const held = await read($, failure)
  await update($, failure, () => null)
  if (held?.retry === undefined) {
    return
  }
  const { retry } = held
  if ((await read($, chain)) !== null) {
    return
  }
  const state: ChainState = { stage: retry.stage, waitsOnOwner: retry.waitsOnOwner, note: retry.note }
  await update($, chain, () => state)
  stage($, `the person asked to try the ${retry.stage === 'handoff' ? 'handoff' : 'compaction'} again`)
  const asOf = chainDismissals
  later($, async () => (retry.stage === 'handoff' ? runHandoff($) : compactByCommand($, state, asOf)))
}

function holdColdTimer($: EngineInterface, wait: number, lead: number): void {
  coldTimer?.cancel()
  coldTimer = $.clock.after(wait, () => {
    void runColdChain($, lead)
  })
}

/** At a turn's end past the floor, with no chain or offer under way, the timer is set for the lifetime less the lead. */
async function armCold($: EngineInterface, cold: ColdOptions, trigger: (window: number) => number): Promise<void> {
  if (cold.lifetime === 0) {
    return
  }
  const stated = await read($, statedCacheMinutes)
  const wait = ((stated > 0 ? stated : cold.lifetime) - cold.lead) * MINUTE_MS
  if (wait <= 0 || (await read($, chain)) !== null || (await read($, newTask)) !== null) {
    return
  }
  const now = await read($, figure)
  if (now === null || now.tokens < (cold.floor > 0 ? cold.floor : trigger(now.window))) {
    return
  }
  const at = (await $.clock.now()) + wait
  holdColdTimer($, wait, cold.lead)
  await setColdAt($, at)
}

/** After a hot reload the deadline outlives the timer: set the timer again, or drop a deadline already past. */
async function holdColdTimerAgain($: EngineInterface, lead: number): Promise<void> {
  const at = await read($, coldTimerAt)
  if (at === 0) {
    return
  }
  const now = await $.clock.now()
  if (at > now) {
    holdColdTimer($, at - now, lead)
  } else {
    await setColdAt($, 0)
  }
}

/** The figure at the turn's end, with no tool call to read it after, and how much the turn grew it. */
async function measureTurn($: EngineInterface): Promise<void> {
  const { context } = await $.session.usage()
  if (context.tokens === undefined || context.percent === undefined) {
    return
  }
  const now: ContextFigure = { tokens: context.tokens, window: context.window, percent: context.percent }
  await update($, figure, () => now)
  const last = await read($, turnEndTokens)
  await update($, turnGrowth, () => (last > 0 && now.tokens > last ? now.tokens - last : 0))
  await update($, turnEndTokens, () => now.tokens)
}

/** The context percent this turn ended at, kept under the turn's duration for the turn line to find. */
async function recordTurn($: EngineInterface, durationMs: number): Promise<void> {
  const now = await read($, figure)
  if (now !== null) {
    await update($, turnFigures, (kept) => [...kept, { durationMs, percent: now.percent }].slice(-TURNS_KEPT))
  }
}

async function stepOffer($: EngineInterface, e: Pick<TurnCompleteInput, 'reason'>, offered: NewTaskState): Promise<void> {
  if (e.reason !== 'answer') {
    await update($, newTask, () => null)
  } else if (offered.stage === 'handoff') {
    await update($, newTask, () => ({ ...offered, stage: 'clearing' }))
    $.clock.after(0, () => {
      void clearThenResend($)
    })
  }
}

async function stepChain($: EngineInterface, e: Pick<TurnCompleteInput, 'reason'>, state: ChainState): Promise<void> {
  if (e.reason !== 'answer') {
    await update($, chain, () => null)
    stage($, `the turn ended by ${e.reason} at the ${state.stage} stage, so the chain stops here`)

    return
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
      const asOf = chainDismissals
      $.clock.after(0, () => {
        void compactByCommand($, state, asOf)
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
}

function isEffort(value: unknown): value is Effort {
  return EFFORTS.some((level) => level === value)
}

async function resend($: EngineInterface, text: string): Promise<void> {
  if (text === '') {
    await failed($, 'no prompt of yours was recorded, so none was sent again')

    return
  }
  await $.prompt.submit({ text, asUser: true })
}

export async function keepGoing($: EngineInterface): Promise<void> {
  await update($, newTask, () => null)
  await resend($, await read($, lastPrompt))
}

async function runHandoffBeforeClear($: EngineInterface): Promise<void> {
  try {
    await $.command.run({ command: HANDOFF_COMMAND })
  } catch (error) {
    await update($, newTask, () => null)
    await failed($, `the handoff did not run (${reason(error)}), so the context was not cleared`)
  }
}

export async function handoffThenClear($: EngineInterface, state: NewTaskState, setsEffort: boolean): Promise<void> {
  await update($, newTask, () => ({ ...state, stage: 'handoff' as const, setsEffort }))
  // Outside this dispatch: a command run inside a hook the turn waits on is refused.
  $.clock.after(0, () => {
    void runHandoffBeforeClear($)
  })
}

async function clearThenResend($: EngineInterface): Promise<void> {
  // The clear starts the session's named values over, so the prompt and the effort are taken out first.
  const text = await read($, lastPrompt)
  const offered = await read($, newTask)
  const level = offered?.setsEffort === true ? offered.effort?.level : undefined
  await update($, newTask, () => null)
  stage($, 'new task: clearing the context')
  try {
    await $.command.run({ command: CLEAR_COMMAND })
  } catch (error) {
    stage($, `new task: the clear did not run (${reason(error)})`)
    await failed($, `the clear did not run (${reason(error)})`)

    return
  }
  if (level !== undefined) {
    await setEffort($, level)
  }
  stage($, `new task: the clear returned, sending ${text === '' ? 'no prompt' : 'the prompt'} again`)
  await resend($, text)
}

/** The effort the person chose for the new task, set after the clear, where the change writes no context to the cache again. */
async function setEffort($: EngineInterface, level: Effort): Promise<void> {
  try {
    await $.command.run({ command: EFFORT_COMMAND, args: level })
    stage($, `new task: the effort set to ${level}`)
  } catch (error) {
    stage($, `new task: the effort was not set (${reason(error)})`)
    await failed($, `the effort was not set to ${level} (${reason(error)}), so the prompt runs at the session's`)
  }
}

export const register: Register = (on, options) => {
  const { thresholdTokens, thresholdPercent, step, chainOn, statusLine, cold } = readOptions(options)
  holdStatus(statusLine)

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined || e.tool === TOOL || e.tool === NEW_TASK_TOOL) {
      return ran
    }
    if (chainOn && e.tool === 'Agent') {
      const stated = lifetimeStated(ran.result)
      if (stated !== null) {
        await update($, statedCacheMinutes, () => stated)
      }
    }
    if (e.agentId === undefined) {
      landed += tokensLanded(ran)
    }
    const { context } = await $.session.usage()
    const now = projected(context)
    if (now === null) {
      return ran
    }
    await update($, figure, () => now)
    await refreshStatus($)

    const trigger = triggerTokens(thresholdTokens, thresholdPercent, context.window)
    if (now.tokens < trigger) {
      return ran
    }
    const warned = await read($, warnedAt)
    // A context smaller than the last warning has been compacted: warn afresh.
    // A tier that rose since the last warning is said at once, inside the step too.
    if (withinStep(warned, now.tokens, step) && adviceTier(now.tokens, trigger) <= adviceTier(warned, trigger)) {
      return ran
    }
    await update($, warnedAt, () => now.tokens)
    await moment($, figureLine(now, 0, chainOn))

    return { ...ran, context: [...(ran.context ?? []), warning(now, trigger, chainOn)] }
  }).catch(($, e, next) => next(e))

  // A main-loop request's usage is the engine's measurement of the context:
  // what landed before the request was sent drops out, and its output and
  // what landed while it streamed stay.
  on('turn.step', async function* ($, e, next) {
    if (e.agentId !== undefined) {
      return yield* next(e)
    }
    const level = isEffort(e.effort) ? e.effort : null
    if (level !== (await read($, sessionEffort))) {
      await update($, sessionEffort, () => level)
    }
    const before = landed
    const r = yield* next(e)
    if (r.usage !== null) {
      answeredOver = r.usage.input_tokens + r.usage.cache_read_input_tokens + r.usage.cache_creation_input_tokens
      landed = landed - before + r.usage.output_tokens
    }

    return r
  }).catch(async function* ($, e, next) {
    return yield* next(e)
  })

  // The engine's own measurement, after each main-loop turn and when a usage window moves a point.
  on('session.measure', async ($, e, next) => {
    const { tokens, window, percent } = e.context
    if (tokens !== undefined && percent !== undefined) {
      await update($, figure, () => ({ tokens, window, percent }))
    }
    const before = await read($, rateLimits)
    if (sameWindows(before, e.rateLimits)) {
      await refreshStatus($)

      return next(e)
    }
    await update($, rateLimits, () => e.rateLimits)
    await refreshStatus($)
    // A dismissal is dropped once its window reset below where it was dismissed.
    const marks = await read($, limitsDismissed)
    const kept = Object.fromEntries(
      Object.entries(marks).filter(([kind, mark]) => e.rateLimits.some((w) => w.kind === kind && w.percentUsed >= mark)),
    )
    if (Object.keys(kept).length !== Object.keys(marks).length) {
      await update($, limitsDismissed, () => kept)
    }
    for (const w of e.rateLimits) {
      const was = before.find((b) => b.kind === w.kind)
      if (limitTier(w.percentUsed) > limitTier(was?.percentUsed ?? 0)) {
        await moment($, limitLine(w))
      }
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  on('prompt.submit', async ($, e, next) => {
    if (e.command === undefined && e.text.trim() !== '' && isThePersons(e.origin)) {
      await update($, lastPrompt, () => e.text)
      const at = await $.clock.now()
      await update($, lastPromptAt, () => at)
      await refreshStatus($)
      if (chainOn) {
        await update($, chainSteps, () => NO_STEPS)
      }
    }
    if (chainOn && e.command === undefined) {
      const isFresh = await opensFreshContext($)
      await update($, freshContext, () => isFresh)
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    if (e.agentId !== undefined) {
      return next(e)
    }
    answeredOver = null
    landed = 0
    await measureTurn($)
    await recordTurn($, e.durationMs)
    await refreshStatus($)
    if (!chainOn) {
      return next(e)
    }
    const offered = await read($, newTask)
    if (offered !== null) {
      await stepOffer($, e, offered)
    }
    const state = await read($, chain)
    if (state !== null) {
      await stepChain($, e, state)
    }
    await armCold($, cold, (window) => triggerTokens(thresholdTokens, thresholdPercent, window))

    return next(e)
  }).catch(($, e, next) => next(e))

  on('session.start', async ($, e, next) => {
    // The command is a convenience: an engine without it must not cost the tools below.
    try {
      await registerKitCommand($)
    } catch {
      // Nothing to tell: the pane is reachable by no command then, and the band and the status line stand.
    }
    if (!chainOn) {
      return next(e)
    }
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
        properties: {
          task: { type: 'string', description: 'The new task, in one line.' },
          effort: {
            type: 'string',
            enum: EFFORTS,
            description: 'The effort the new task needs, only when it differs from this session\'s: lower for routine or mechanical work, higher for design or debugging.',
          },
          effort_reason: { type: 'string', description: 'Why that effort, in a few words.' },
        },
        required: ['task'],
      },
      isDeferred: false,
    })
    await holdColdTimerAgain($, cold.lead)

    return next(e)
  }).catch(($, e, next) => next(e))

  if (!chainOn) {
    return
  }


  // A turn starting uses the cache again, so the timer counts from its end instead.
  on('turn.start', async ($, e, next) => {
    if (e.agentId === undefined) {
      await disarmCold($)
    }

    return next(e)
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: NEW_TASK_TOOL }, async ($, e) => {
    const task = typeof e.task === 'string' && e.task.trim() !== '' ? e.task.trim() : ''
    if (task === '') {
      return refuse('task must name the new task in one line.')
    }
    if (e.effort !== undefined && !isEffort(e.effort)) {
      return refuse(`effort must be one of ${EFFORTS.join(', ')}, or left out.`)
    }
    if (await read($, freshContext)) {
      return answer(NOTHING_TO_CLEAR)
    }
    const level = isEffort(e.effort) && e.effort !== (await read($, sessionEffort)) ? e.effort : undefined
    const why = typeof e.effort_reason === 'string' ? e.effort_reason.trim() : ''
    await update($, newTask, () => (level === undefined ? { stage: 'offered', task } : { stage: 'offered', task, effort: { level, reason: why } }))
    await moment($, `New task: ${task}. From a terminal or the desktop, the band offers the handoff and a clear, or to keep going here.`)

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
    const steps = await read($, chainSteps)
    const signal = steps.length + 1
    let stopped: string | undefined
    if (nextStep === 'session' && judgedAt(signal)) {
      const judged = await judgeChain($, steps, note)
      stage($, `the judge read signal ${signal} since the person's last prompt: ${judged.verdict ?? 'no verdict'}, ${judged.reason}`)
      if (judged.verdict !== 'CONTINUE') {
        stopped = stopReason(judged)
      }
    }
    const waitsOnOwner = nextStep === 'owner' || stopped !== undefined
    const requested: ChainState = stopped === undefined ? { stage: 'requested', waitsOnOwner, note } : { stage: 'requested', waitsOnOwner, note, stopped }
    await update($, chain, () => requested)
    await moment($, stageLine(requested))
    if (stopped !== undefined) {
      return answer(
        `Clear point noted. session-kit's judge stops the chain after the compaction: ${stopped} ` +
          'End this turn now, with nothing more started, saying in one line what is left ' +
          'for the owner. When it ends, session-kit writes the handoff and compacts the ' +
          'context, then stops.',
      )
    }

    return answer(
      'Clear point noted. End this turn now, with nothing more started. When it ' +
        'ends, session-kit writes the handoff and compacts the context, then ' +
        (waitsOnOwner ? 'stops, since the next step is the owner\'s.' : `continues with: ${note}`),
    )
  }).catch(() => refuse('session-kit could not record the clear point, so the chain did not start.'))
}
