import { atom, read, update } from 'claude-code'
import type { EngineInterface, HookStream, ProcessSpawnChunk, ProcessSpawnResult, Register } from 'claude-code'

import { utterances } from './speech'

const PLUGIN = 'read-aloud'
const SAY = '/usr/bin/say'
const KILLED: ProcessSpawnResult = { code: null, signal: 'SIGTERM' }
const USAGE = 'Usage: /read-aloud reads the last answer or stops the reading, /read-aloud stop, /read-aloud auto [on|off].'

const answer = atom({ plugin: 'read-aloud', key: 'answer' } as const, null)
const isSpeaking = atom({ plugin: 'read-aloud', key: 'isSpeaking' } as const, false)
const isAuto = atom({ plugin: 'read-aloud', key: 'isAuto' } as const, null)

// The options, read again by each load of the module.
let voice: string | undefined
let autoByDefault = false
// Each reading takes the next number; a reading whose number is no longer the last stops before its next utterance.
let reading = 0
// The `say` speaking now. Closing its stream kills it, so a stop silences the voice at once.
let speaker: HookStream<ProcessSpawnChunk, ProcessSpawnResult> | undefined

function silence(): void {
  const child = speaker
  speaker = undefined
  void child?.return(KILLED)
}

// One utterance through `say`, which reads it from its input; resolves when it ends or is silenced.
async function say($: EngineInterface, text: string): Promise<void> {
  const child = $.process.spawn({ argv: voice === undefined ? [SAY] : [SAY, '-v', voice], input: text })
  speaker = child
  let stderr = ''
  for await (const chunk of child) {
    if (chunk.stream === 'stderr') {
      stderr += chunk.text
    }
  }
  if (speaker !== child) {
    return
  }
  speaker = undefined
  const { code, signal } = await child.result
  if (code !== 0) {
    throw new Error(stderr.trim() || `say ended with ${code ?? signal}`)
  }
}

async function readAloud($: EngineInterface, text: string): Promise<void> {
  reading += 1
  const mine = reading
  silence()
  await update($, isSpeaking, () => true)
  try {
    for (const piece of utterances(text)) {
      if (mine !== reading) {
        return
      }
      await say($, piece)
    }
  } catch (error) {
    if (mine === reading) {
      $.ui.toast(`read-aloud: ${error instanceof Error ? error.message : String(error)}`)
    }
  } finally {
    if (mine === reading) {
      await update($, isSpeaking, () => false)
    }
  }
}

// The reading starts once the hook that asked for it has returned, so no turn or press waits on the voice.
function startReading($: EngineInterface, text: string): void {
  $.clock.after(0, () => {
    void readAloud($, text)
  })
}

async function stopReading($: EngineInterface): Promise<void> {
  reading += 1
  silence()
  await update($, isSpeaking, () => false)
}

async function autoOn($: EngineInterface): Promise<boolean> {
  return (await read($, isAuto)) ?? autoByDefault
}

async function setAuto($: EngineInterface, value: boolean): Promise<string> {
  await update($, isAuto, () => value)

  return value ? 'Auto-read on: each answer is read as its turn ends.' : 'Auto-read off.'
}

// With no argument the command toggles: it stops a reading, or reads the last answer.
async function playOrStop($: EngineInterface): Promise<string> {
  if (await read($, isSpeaking)) {
    await stopReading($)

    return 'Stopped.'
  }
  const last = await read($, answer)
  if (last === null) {
    return 'No answer to read yet.'
  }
  startReading($, last)

  return 'Reading the last answer.'
}

async function commandText($: EngineInterface, args: string): Promise<string> {
  const [word = '', value = '', ...rest] = args.trim().toLowerCase().split(/\s+/).filter(one => one !== '')
  if (rest.length > 0) {
    return USAGE
  }
  if (word === '') {
    return playOrStop($)
  }
  if (word === 'stop' && value === '') {
    await stopReading($)

    return 'Stopped.'
  }
  if (word === 'auto' && value === '') {
    return setAuto($, !(await autoOn($)))
  }
  if (word === 'auto' && (value === 'on' || value === 'off')) {
    return setAuto($, value === 'on')
  }

  return USAGE
}

export const register: Register = (on, options) => {
  voice = typeof options.voice === 'string' && options.voice.trim() !== '' ? options.voice.trim() : undefined
  autoByDefault = options.auto === true

  on('session.start', async ($, e, next) => {
    await $.command.register({ name: PLUGIN, description: 'Read the last answer aloud, stop it, or turn auto-read on or off (auto [on|off])' })

    return next(e)
  })

  on('command.run', { command: PLUGIN }, async ($, e) => ({ text: await commandText($, e.args) })).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (e.agentId === undefined && e.reason === 'answer' && !e.isAborted && e.answer.trim() !== '') {
      await update($, answer, () => e.answer)
      if (await autoOn($)) {
        startReading($, e.answer)
      }
    }

    return result
  }).catch(($, e, next) => next(e))

  // The read-aloud row draws above whatever the plugins beneath drew, so no band of theirs is hidden.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const below = await next(e)
    if (e.props.hasSurvey || (await read($, answer)) === null) {
      return below
    }
    const speaking = await read($, isSpeaking)
    const auto = await autoOn($)
    const { Box, Button } = $.ui.resolve(e)

    return (
      <Box flexDirection="column">
        <Box key="read-aloud">
          {speaking ? (
            <Button key="read-aloud-stop" label="Stop reading" onPress={() => stopReading($)} />
          ) : (
            <Button key="read-aloud-play" label={'\u{1F50A} Read answer'} onPress={() => playOrStop($)} />
          )}
          <Button key="read-aloud-auto" label={auto ? 'Auto-read on' : 'Auto-read off'} dimColor onPress={() => setAuto($, !auto)} />
        </Box>
        {below}
      </Box>
    )
  }).catch(($, e, next) => next(e))
}
