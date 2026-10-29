// The kit's pane, the session's dashboard (`A89`): the owner's open tagged
// items, what this session committed and left uncommitted with the last test
// run, the next step and the open questions the handoff records, the context
// with its thresholds, its curve over the turns and the handoff's buttons, each
// usage window, and the chain while one runs or has failed. A section with
// nothing to say is left out. Each section is a card: its title and the figure
// that sums it up on one line, then its body, the fact that matters in full
// weight and its context dim. The desktop draws the gauges and the
// curve as SVG, the terminal as cells. A `kit` chip in the footer's mode labels
// shows and hides the pane, as `/kit` does, and the next session starts with
// the pane as the last press left it; the pane's own close mark hides it for
// this session alone (`A87`). The validator cuts a line of its report at about
// a thousand characters (`A60`), so the pane and the chip share one drawing
// hook, every read of the files and of git goes through `paneFacts`, and the
// context concern's `session.start` hook registers the command and opens the
// pane again with direct calls.

import { atom, read } from 'claude-code'
import type { ElementTable, EngineInterface, Register, RenderChildren, SessionRateLimit } from 'claude-code'

import type { StageLine, TaggedItem, TestRun, TurnFigure } from '../types'
import { chainByPerson, handoffByPerson } from './context'
import { gitOutput, handoffState } from './checkout'
import { LIMIT_FIRM, LIMIT_WARN, bar, clockTime, compact, limitFigures, newTaskLine, stageLine } from './lines'
import { readOptions, triggerTokens } from './options'
import { verdictOf } from './test_log'
import type { Verdict } from './test_log'

const NO_WINDOWS: SessionRateLimit[] = []
const NO_STAGES: StageLine[] = []
const NO_ITEMS: TaggedItem[] = []
const NO_TURNS: TurnFigure[] = []

const chain = atom({ plugin: 'session-kit', key: 'chain' } as const, null)
const coldTimerAt = atom({ plugin: 'session-kit', key: 'coldTimerAt' } as const, 0)
const failure = atom({ plugin: 'session-kit', key: 'failure' } as const, null)
const figure = atom({ plugin: 'session-kit', key: 'contextFigure' } as const, null)
const newTask = atom({ plugin: 'session-kit', key: 'newTask' } as const, null)
const rateLimits = atom({ plugin: 'session-kit', key: 'rateLimits' } as const, NO_WINDOWS)
const stages = atom({ plugin: 'session-kit', key: 'stages' } as const, NO_STAGES)
const turnGrowth = atom({ plugin: 'session-kit', key: 'turnGrowth' } as const, 0)
const turnFigures = atom({ plugin: 'session-kit', key: 'turnFigures' } as const, NO_TURNS)
const openItems = atom({ plugin: 'session-kit', key: 'openItems' } as const, NO_ITEMS)
const lastTest = atom({ plugin: 'session-kit', key: 'lastTest' } as const, null)

export const PANE = 'kit'
export const PANE_TITLE = 'session-kit'
export const COMMAND = 'kit'
export const COMMAND_DESCRIPTION = 'Show or hide the session-kit pane: your items, this session, the next step, context, usage and chain'
// The `$.store` key that keeps, across sessions, whether the person left the pane open.
export const KEPT_OPEN = 'paneOpen'

const HANDOFF = 'CLAUDE.local.md'
const SHOWN = 6
const CURVE_TURNS = 24
// The band's two higher tiers of the context, as multiples of the trigger (`A86`).
const FIRM_TIER = 1.2
const STOP_TIER = 1.6
const GAUGE_WIDTH = 240
const GAUGE_HEIGHT = 10
const CURVE_HEIGHT = 24
const SPARKS = '▁▂▃▄▅▆▇█'
// Colours the SVG draws in, readable on the desktop's light and dark themes alike.
const INK = { success: '#3fb950', warning: '#d29922', error: '#f85149', track: '#8b949e55', mark: '#8b949e' } as const

type Tone = 'success' | 'warning' | 'error'
type Parts = Pick<ElementTable<'desktop'>, 'Box' | 'Button' | 'Text'>
type Svg = ElementTable<'desktop'>['Svg'] | null

/** What the pane reads off the checkout and the handoff, once per drawing. */
type Facts = {
  commits: string[]
  files: string[]
  handoff: string
  next: string | null
  questions: string[]
  verdict: Verdict | null
}

/** The body of the `## <heading>` section of a markdown text, trimmed; empty when there is none. */
export function sectionOf(text: string, heading: string): string {
  const lines = text.split('\n')
  const start = lines.findIndex((line) => line.trim() === `## ${heading}`)
  if (start === -1) {
    return ''
  }
  const end = lines.findIndex((line, i) => i > start && line.startsWith('## '))

  return lines
    .slice(start + 1, end === -1 ? undefined : end)
    .join('\n')
    .trim()
}

/** The bullets of a section, or its first paragraph as one item when it has none. */
export function itemsOf(body: string): string[] {
  const bullets = body
    .split('\n')
    .filter((line) => /^\s*[-*]\s+/.test(line))
    .map((line) => line.replace(/^\s*[-*]\s+/, '').trim())

  return bullets.length > 0 ? bullets : body === '' ? [] : [body.split('\n\n')[0]?.replace(/\s+/g, ' ').trim() ?? '']
}

/** Every read the pane makes of git and the files; a part that cannot be read is empty. */
async function paneFacts($: EngineInterface, last: TestRun | null): Promise<Facts> {
  const cwd = await $.session.cwd()
  const since = Math.floor((await $.session.usage()).startedAt / 1000)
  const log = await gitOutput($, cwd, ['log', `--since=@${since}`, '--format=%h %s'])
  const status = await gitOutput($, cwd, ['status', '--porcelain'])
  let local = ''
  try {
    local = await $.fs.read(`${cwd}/${HANDOFF}`)
  } catch {
    // No handoff file: the next step and the questions stay empty.
  }
  let handoff = 'unknown'
  try {
    handoff = await handoffState($, cwd)
  } catch {
    // The state stays unknown where git or the file system cannot say.
  }
  let verdict: Verdict | null = null
  if (last !== null) {
    try {
      verdict = await verdictOf($, cwd, last)
    } catch {
      verdict = 'UNKNOWN'
    }
  }
  const nonEmpty = (out: string | null) => (out ?? '').split('\n').filter((line) => line.trim() !== '')
  const next = itemsOf(sectionOf(local, 'Next step'))

  return {
    commits: nonEmpty(log),
    files: nonEmpty(status).map((line) => line.slice(3)),
    handoff,
    next: next[0] ?? null,
    questions: itemsOf(sectionOf(local, 'Open questions for the user')).filter((q) => !/^none\.?$/i.test(q)),
    verdict,
  }
}

function toneOf(percent: number, warnAt: number, errorAt: number): Tone {
  return percent >= errorAt ? 'error' : percent >= warnAt ? 'warning' : 'success'
}

/** A horizontal gauge as SVG: the track, the fill to `percent` and a tick at each mark. */
export function gaugeSvg(percent: number, tone: Tone, marks: readonly number[]): string {
  const fill = (Math.max(0, Math.min(100, percent)) * GAUGE_WIDTH) / 100
  const ticks = marks
    .filter((m) => m > 0 && m < 100)
    .map((m) => `<rect x="${((m * GAUGE_WIDTH) / 100).toFixed(1)}" y="0" width="2" height="${GAUGE_HEIGHT}" fill="${INK.mark}"/>`)
    .join('')

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${GAUGE_WIDTH}" height="${GAUGE_HEIGHT}" viewBox="0 0 ${GAUGE_WIDTH} ${GAUGE_HEIGHT}"><rect width="${GAUGE_WIDTH}" height="${GAUGE_HEIGHT}" rx="3" fill="${INK.track}"/><rect width="${fill.toFixed(1)}" height="${GAUGE_HEIGHT}" rx="3" fill="${INK[tone]}"/>${ticks}</svg>`
}

/** The context percent over the last turns as an SVG line, its scale from 0 to the highest percent. */
export function curveSvg(percents: readonly number[]): string {
  const top = Math.max(1, ...percents)
  const step = percents.length > 1 ? GAUGE_WIDTH / (percents.length - 1) : 0
  const points = percents.map((p, i) => `${(i * step).toFixed(1)},${(CURVE_HEIGHT - 1 - (p * (CURVE_HEIGHT - 2)) / top).toFixed(1)}`).join(' ')

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${GAUGE_WIDTH}" height="${CURVE_HEIGHT}" viewBox="0 0 ${GAUGE_WIDTH} ${CURVE_HEIGHT}"><polyline points="${points}" fill="none" stroke="${INK.mark}" stroke-width="1.5"/></svg>`
}

/** The same curve in cells, one per turn. */
export function sparkline(percents: readonly number[]): string {
  const top = Math.max(1, ...percents)

  return percents.map((p) => SPARKS[Math.min(SPARKS.length - 1, Math.floor((p / top) * (SPARKS.length - 1)))]).join('')
}

/** A section's card: its title and the figure that sums it up on one line, then its body. */
function card(p: Parts, title: string, summary: RenderChildren, body: RenderChildren[]) {
  const { Box, Text } = p

  return (
    <Box key={title} flexDirection="column" borderStyle="round" borderColor="subtle" paddingX={1} rowGap={0}>
      <Box justifyContent="space-between" gap={1}>
        <Text weight="semibold">{title}</Text>
        {summary}
      </Box>
      {body}
    </Box>
  )
}

/** A commit's subject as far as its first clause: the words before a colon or a parenthesis. */
export function headline(subject: string): string {
  const cut = subject.search(/: | \(|; /)

  return cut === -1 ? subject : subject.slice(0, cut)
}

/** A test command without the `cd <dir>;` or `cd <dir> &&` that leads it. */
export function commandShown(command: string): string {
  return command
    .split(/\s*(?:;|&&)\s*/)
    .filter((part) => !/^cd\s/.test(part) && part.trim() !== '')
    .join('; ')
}

/** Up to `SHOWN` lines, then `+n more`. */
function capped<T>(p: Parts, all: readonly T[], draw: (item: T, i: number) => RenderChildren) {
  const { Text } = p
  const shown = all.slice(0, SHOWN).map(draw)

  return all.length > SHOWN ? [...shown, <Text dimColor>{`+${all.length - SHOWN} more`}</Text>] : shown
}

function gauge(p: Parts, svg: Svg, percent: number, tone: Tone, marks: readonly number[], alt: string) {
  const { Text } = p

  if (svg === null) {
    return <Text color={tone}>{bar(percent)}</Text>
  }
  const Picture = svg

  return <Picture source={gaugeSvg(percent, tone, marks)} alt={alt} />
}

function curve(p: Parts, svg: Svg, percents: readonly number[]) {
  const { Text } = p
  if (svg === null) {
    return <Text dimColor>{sparkline(percents)}</Text>
  }
  const Picture = svg

  return <Picture source={curveSvg(percents)} alt={`Context over the last ${percents.length} turns`} />
}

const VERDICT_TONE: Record<Verdict, Tone | 'subtle'> = { PASS: 'success', FAIL: 'error', STALE: 'warning', UNKNOWN: 'subtle' }

export const register: Register = (on, options) => {
  const { thresholdTokens, thresholdPercent, chainOn } = readOptions(options)

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
    const table = $.ui.resolve(e)
    const p: Parts = { Box: table.Box, Button: table.Button, Text: table.Text }
    const svg: Svg = 'Svg' in table ? table.Svg : null
    const { Box, Button, Text } = p
    const items = await read($, openItems)
    const last = await read($, lastTest)
    const now = await read($, figure)
    const grewBy = await read($, turnGrowth)
    const turns = await read($, turnFigures)
    const coldAt = await read($, coldTimerAt)
    const windows = await read($, rateLimits)
    const held = await read($, failure)
    const offered = await read($, newTask)
    const running = await read($, chain)
    const journal = await read($, stages)
    const facts = await paneFacts($, last)
    const sections: RenderChildren[] = []

    if (items.length > 0) {
      sections.push(
        card(
          p,
          'Your items',
          <Text dimColor>{`${items.length} open`}</Text>,
          capped(p, items, (item) => (
            <Box gap={1}>
              <Text weight="semibold" color="claude">
                {item.id}
              </Text>
              <Text>{item.text}</Text>
            </Box>
          )),
        ),
      )
    }

    const session: RenderChildren[] = []
    session.push(
      ...capped(p, facts.commits, (c) => (
        <Box gap={1}>
          <Text mono dimColor>
            {c.slice(0, c.indexOf(' '))}
          </Text>
          <Text wrap="truncate-end">{headline(c.slice(c.indexOf(' ') + 1))}</Text>
        </Box>
      )),
    )
    if (facts.files.length > 0) {
      session.push(<Text color="warning">{`${facts.files.length} uncommitted`}</Text>)
      session.push(
        ...capped(p, facts.files, (f) => (
          <Text mono dimColor wrap="truncate-start">
            {f}
          </Text>
        )),
      )
    }
    if (last !== null && facts.verdict !== null) {
      session.push(
        <Box gap={1}>
          <Text weight="semibold" color={VERDICT_TONE[facts.verdict]}>
            {facts.verdict}
          </Text>
          <Text mono dimColor wrap="truncate-end">
            {commandShown(last.command)}
          </Text>
          <Text dimColor>{clockTime(new Date(last.at))}</Text>
        </Box>,
      )
    }
    if (session.length > 0) {
      const summary = `${facts.commits.length} ${facts.commits.length === 1 ? 'commit' : 'commits'}`
      sections.push(card(p, 'This session', <Text dimColor>{summary}</Text>, session))
    }

    const ahead: RenderChildren[] = []
    if (facts.next !== null) {
      ahead.push(<Text>{facts.next}</Text>)
    }
    if (facts.questions.length > 0) {
      ahead.push(
        <Text size="footnote" dimColor>
          Open questions
        </Text>,
      )
      ahead.push(...capped(p, facts.questions, (q) => <Text>{`· ${q}`}</Text>))
    }
    const handoffTone = facts.handoff === 'current' ? 'subtle' : 'warning'
    sections.push(card(p, 'Next', <Text color={handoffTone}>{`handoff ${facts.handoff}`}</Text>, ahead))

    if (now !== null) {
      const trigger = triggerTokens(thresholdTokens, thresholdPercent, now.window)
      const marks = [trigger, trigger * FIRM_TIER, trigger * STOP_TIER].map((t) => (t * 100) / now.window)
      const tone = toneOf(now.tokens, trigger * FIRM_TIER, trigger * STOP_TIER)
      const percents = turns.slice(-CURVE_TURNS).map((t) => t.percent)
      sections.push(
        card(
          p,
          'Context',
          <Text weight="semibold" tabular color={tone}>{`${now.percent}%`}</Text>,
          [
            <Box gap={1}>
              <Text weight="semibold" tabular>{`${compact(now.tokens)} / ${compact(now.window)}`}</Text>
              <Text dimColor tabular>{`${grewBy > 0 ? `+${compact(grewBy)} last turn · ` : ''}trigger ${compact(trigger)}`}</Text>
            </Box>,
            gauge(p, svg, now.percent, tone, marks, `Context ${now.percent}%, trigger at ${compact(trigger)}`),
            percents.length > 1 ? (
              <Box flexDirection="column">
                <Text size="footnote" dimColor>{`The last ${percents.length} turns`}</Text>
                {curve(p, svg, percents)}
              </Box>
            ) : null,
            coldAt === 0 ? null : <Text size="footnote" dimColor>{`Handoff and compact run by themselves at ${clockTime(new Date(coldAt))}.`}</Text>,
            <Box gap={1}>
              <Button key="pane-handoff" label="Handoff" variant={chainOn ? undefined : 'primary'} onPress={() => handoffByPerson($)} />
              {chainOn ? <Button key="pane-chain" label="Handoff and compact" variant="primary" onPress={() => chainByPerson($)} /> : null}
            </Box>,
          ],
        ),
      )
    }

    if (windows.length > 0) {
      const top = Math.max(...windows.map((w) => w.percentUsed))
      sections.push(
        card(
          p,
          'Usage',
          <Text weight="semibold" tabular color={toneOf(top, LIMIT_WARN, LIMIT_FIRM)}>{`${top}%`}</Text>,
          windows.map((w) => {
            const [name, reset] = limitFigures(w).split(' · ')

            return (
              <Box flexDirection="column">
                <Box justifyContent="space-between" gap={1}>
                  <Text tabular>{name}</Text>
                  <Text dimColor>{reset ?? ''}</Text>
                </Box>
                {gauge(p, svg, w.percentUsed, toneOf(w.percentUsed, LIMIT_WARN, LIMIT_FIRM), [LIMIT_WARN, LIMIT_FIRM], limitFigures(w))}
              </Box>
            )
          }),
        ),
      )
    }

    if (held !== null || offered !== null || running !== null) {
      const head = held !== null ? <Text color="error">{`${held.text}.`}</Text> : <Text>{offered !== null ? newTaskLine(offered) : running === null ? '' : stageLine(running)}</Text>
      sections.push(
        card(p, 'Chain', <Text color={held !== null ? 'error' : 'subtle'}>{held !== null ? 'failed' : offered !== null ? 'offer' : 'running'}</Text>, [
          head,
          ...journal.map((st) => (
            <Box gap={1}>
              <Text mono dimColor>
                {clockTime(new Date(st.at))}
              </Text>
              <Text dimColor wrap="truncate-end">
                {st.text}
              </Text>
            </Box>
          )),
        ]),
      )
    }

    return (
      <Box flexDirection="column" gap={1}>
        {sections}
      </Box>
    )
  }).catch(($, e, next) => next(e))
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
