// The owner's working window, held for them alone (A92): outside it, the
// owner's prompt waits on the band for a one-line reason, which sends it on
// unchanged, logs it and opens a pass for every session for 30 minutes. Each
// prompt that goes on is tagged against the owner's focus list (A94). Nothing
// of it reaches the model.

import { expect, mock, test } from 'claude-code/testing'

import type { On, PromptOrigin } from 'claude-code'

const HOME = '/home/me'
const LOAD = `${HOME}/.claude/session-kit/load`
const MINUTE = 60_000
// Thursday 2026-10-29 in Buenos Aires (UTC-3).
const AT_19 = Date.UTC(2026, 9, 29, 22, 0)
const AT_09 = Date.UTC(2026, 9, 29, 12, 0)
const AT_23 = Date.UTC(2026, 9, 30, 2, 0)

const SETTINGS = {
  timeZone: 'America/Argentina/Buenos_Aires',
  work: { days: ['mon', 'tue', 'wed', 'thu', 'fri'], hours: ['06:00-11:00', '15:00-17:00'] },
  personal: { days: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'], hours: ['05:30-22:00'], folders: ['~/devel/galileo'] },
  passMinutes: 30,
}

const BAND = {
  plugin: 'session-kit',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 5, bodyColumns: 80, scroll: { offset: 0, bodyRows: 4 }, view: {} },
} as const

const COMPOSER: PromptOrigin = { kind: 'composer' }

function engine(on: On, options: { now: number; cwd: string; settings?: boolean; files?: { [path: string]: string } }) {
  const files: { [path: string]: string } = { ...(options.settings === false ? {} : { [`${LOAD}/settings.json`]: JSON.stringify(SETTINGS) }), ...options.files }
  const status: (string | undefined)[] = []
  const entered: string[] = []
  const box = { text: '' }
  const waiting: { path: string; resolve: () => void }[] = []
  const clock = mock.clock(on, { now: options.now })
  mock.env(on, { HOME, TMPDIR: '/var/tmp/t' })
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: options.cwd }))
  on('session.id', () => ({ value: 'sess-1' }))
  on('session.usage', () => ({ value: { startedAt: 0, context: { tokens: 100_000, window: 1_000_000, percent: 10 }, rateLimits: [] } }))
  on('fs.read', (_, e) => {
    const text = files[e.path]
    if (text === undefined) {
      throw new Error(`ENOENT: ${e.path}`)
    }

    return { value: text }
  })
  on('fs.write', (_, e) => {
    files[e.path] = e.text
    for (const w of waiting.filter((x) => x.path === e.path && e.text !== '')) {
      w.resolve()
    }

    return { value: undefined }
  })
  on('fs.exists', (_, e) => ({ value: e.path in files }))
  // The hold's wait: a shell loop that ends once the reason file holds text.
  on('process.run', async (_, e) => {
    const path = e.argv.at(-1) ?? ''
    if (path.startsWith(LOAD)) {
      if ((files[path] ?? '') === '') {
        await new Promise<void>((resolve) => waiting.push({ path, resolve }))
      }

      return { value: { exitCode: 0, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
    }

    return { value: { exitCode: 128, stdout: '', stderr: 'fatal: not a git repository', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('prompt.submit', (_, e) => {
    entered.push(e.text)

    return { text: e.text, context: e.context }
  })
  on('prompt.read', () => ({ value: { text: box.text } }))
  on('prompt.fill', (_, e) => {
    box.text = e.text

    return { value: undefined }
  })
  on('tool.register', (_, e) => ({ value: { tool: `mcp__session-kit__${e.name}` } }))
  on('ui.status', (_, e) => {
    status.push(e.text)

    return { value: undefined }
  })
  on('ui.log', () => ({ value: undefined }))
  on('ui.toast', () => ({ value: undefined }))
  on('session.surfaces', () => ({ value: ['desktop'] }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>engine</Text>
  })

  const log = () =>
    (files[`${LOAD}/holds.jsonl`] ?? '')
      .split('\n')
      .filter((l) => l !== '')
      .map((l): { [k: string]: unknown } => JSON.parse(l))

  return { clock, entered, files, log, box, status }
}

test('outside its window a work prompt waits for a reason on the band; the reason sends it unchanged, logs it, and opens a pass for every session', async ($, on) => {
  const { clock, entered, files, log } = engine(on, { now: AT_19, cwd: '/home/me/devel/iquall/tagents/lane5' })
  await $.session.start({ cwd: '/home/me/devel/iquall/tagents/lane5', surface: 'desktop', isInteractive: true })

  const sending = $.prompt.submit({ text: 'merge lane5', wait: false, origin: COMPOSER })
  await clock.settle()
  expect(entered).toEqual([])

  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  const texts = (await ui.findAll({ type: 'Text' })).map((t) => t.text).join(' | ')
  expect(texts).toContain('Outside your work window')
  await ui.input({ key: 'load-reason', text: 'the demo is tomorrow at 9' })
  await ui.unmount()
  await sending
  expect(entered).toEqual(['merge lane5'])

  expect(log()).toEqual([expect.objectContaining({ session: 'sess-1', kind: 'work', reason: 'the demo is tomorrow at 9', via: 'band', outcome: 'sent' })])
  const pass = JSON.parse(files[`${LOAD}/pass.json`] ?? '{}')
  expect(pass.until).toBe(AT_19 + 30 * MINUTE)

  // Within the pass the next prompt goes straight on; past it, it is held again.
  await clock.advance(10 * MINUTE)
  await $.prompt.submit({ text: 'and push', wait: false, origin: COMPOSER })
  expect(entered).toEqual(['merge lane5', 'and push'])
  await clock.advance(25 * MINUTE)
  void $.prompt.submit({ text: 'one more', wait: false, origin: COMPOSER })
  await clock.settle()
  expect(entered).toEqual(['merge lane5', 'and push'])
})

test('a personal prompt in its slot, a work prompt in its window and any prompt without settings go straight on; in the sleeping hours a personal one waits', async ($, on) => {
  const { clock, entered } = engine(on, { now: AT_19, cwd: '/home/me/devel/galileo/misc/galileo-kit' })
  await $.session.start({ cwd: '/home/me/devel/galileo/misc/galileo-kit', surface: 'desktop', isInteractive: true })
  await $.prompt.submit({ text: 'kit work in the evening', wait: false, origin: COMPOSER })
  expect(entered).toEqual(['kit work in the evening'])

  await clock.advance(AT_23 - AT_19)
  void $.prompt.submit({ text: 'kit work at night', wait: false, origin: COMPOSER })
  await clock.settle()
  expect(entered).toEqual(['kit work in the evening'])
})

test('a work prompt inside the window goes straight on', async ($, on) => {
  const { entered } = engine(on, { now: AT_09, cwd: '/home/me/devel/iquall/tagents/lane5' })
  await $.session.start({ cwd: '/home/me/devel/iquall/tagents/lane5', surface: 'desktop', isInteractive: true })
  await $.prompt.submit({ text: 'morning work', wait: false, origin: COMPOSER })
  expect(entered).toEqual(['morning work'])
})

test('without settings nothing is held', async ($, on) => {
  const { entered } = engine(on, { now: AT_23, cwd: '/home/me/devel/iquall/tagents/lane5', settings: false })
  await $.session.start({ cwd: '/home/me/devel/iquall/tagents/lane5', surface: 'desktop', isInteractive: true })
  await $.prompt.submit({ text: 'night work', wait: false, origin: COMPOSER })
  expect(entered).toEqual(['night work'])
})

test('a prompt from the phone, which draws no band, goes on and is logged with no reason', async ($, on) => {
  const { entered, log } = engine(on, { now: AT_23, cwd: '/home/me/devel/iquall/tagents/lane5' })
  await $.session.start({ cwd: '/home/me/devel/iquall/tagents/lane5', surface: 'desktop', isInteractive: true })
  await $.prompt.submit({ text: 'status?', wait: false, origin: { kind: 'bridge' } })
  expect(entered).toEqual(['status?'])
  expect(log()).toEqual([expect.objectContaining({ kind: 'work', reason: null, via: 'phone', outcome: 'sent' })])
})

test("each prompt that goes on is tagged against this week's focus list by its folder, the week's share counted from its log; a list of another week tags it stale", async ($, on) => {
  const focus = '# Week of 2026-10-26\n\n- value metrics (O18): `~/devel/iquall/tagents/lane5`\n- the MAT demo ~/devel/iquall/demo-mat-porting\n'
  const earlier = `${JSON.stringify({ at: 0, session: 's0', cwd: '/home/me/devel/galileo/brain-dumping', focus: null })}\n`
  const { entered, files, status } = engine(on, {
    now: AT_09,
    cwd: '/home/me/devel/iquall/tagents/lane5/.claude/worktrees/w1',
    files: { [`${HOME}/.claude/session-kit/focus.md`]: focus, [`${LOAD}/prompts-2026-10-26.jsonl`]: earlier },
  })
  await $.session.start({ cwd: '/home/me/devel/iquall/tagents/lane5', surface: 'desktop', isInteractive: true })
  await $.prompt.submit({ text: 'morning work', wait: false, origin: COMPOSER })

  expect(entered).toEqual(['morning work'])
  expect(status.at(-1)).toContain('on focus: value metrics (O18), 50% on this week')
  expect(files[`${LOAD}/focus-2026-10-26.md`]).toBe(focus)
  expect(files[`${LOAD}/prompts-2026-10-26.jsonl`]?.split('\n').filter((l) => l !== '').at(-1)).toContain('"focus":"value metrics (O18)"')

  files[`${HOME}/.claude/session-kit/focus.md`] = focus.replace('2026-10-26', '2026-10-19')
  await $.prompt.submit({ text: 'more work', wait: false, origin: COMPOSER })
  expect(status.at(-1)).toContain("the focus list is not this week's")
})
