// The corpus of the local-voice measurement: final answers from this project's
// transcripts, turned into utterances by read-aloud's own speech.ts.
//
//   node docs/measurements/local-voice/corpus.mjs <out.json> <transcript.jsonl>...
//
// A turn's final answer is the text its main-session messages wrote after the
// turn's last tool call. Three short answers, four medium and three long are
// kept, spread evenly over the answers found in each band.

import { readFileSync, writeFileSync } from 'node:fs'
import { basename } from 'node:path'

import { utterances } from '../../../plugins/read-aloud/hooks/speech.ts'

const BANDS = [
  { name: 'short', min: 120, max: 500, count: 3 },
  { name: 'medium', min: 500, max: 1500, count: 4 },
  { name: 'long', min: 1500, max: 2600, count: 3 },
]

function finalAnswers(path) {
  const answers = []
  let texts = []
  const close = () => {
    const answer = texts.join('\n\n').trim()
    if (answer !== '') {
      answers.push(answer)
    }
    texts = []
  }
  for (const line of readFileSync(path, 'utf8').split('\n')) {
    if (line.trim() === '') {
      continue
    }
    const record = JSON.parse(line)
    if (record.isSidechain || record.isMeta) {
      continue
    }
    const content = record.message?.content
    if (record.type === 'user') {
      const isPrompt = typeof content === 'string' || content?.some(block => block.type === 'text')
      if (isPrompt) {
        close()
      }
    } else if (record.type === 'assistant' && Array.isArray(content)) {
      for (const block of content) {
        if (block.type === 'tool_use') {
          texts = []
        } else if (block.type === 'text') {
          texts.push(block.text)
        }
      }
    }
  }
  close()

  return answers
}

const [out, ...paths] = process.argv.slice(2)
// A transcript forked from another repeats its answers, and each is kept once.
const seen = new Set()
const found = paths
  .flatMap(path => finalAnswers(path).map((text, index) => ({ source: `${basename(path, '.jsonl')}#${index}`, text })))
  .filter(one => !seen.has(one.text) && seen.add(one.text))
const readings = BANDS.flatMap(band => {
  const inBand = found.filter(one => one.text.length >= band.min && one.text.length < band.max)
  if (inBand.length < band.count) {
    throw new Error(`${band.name}: ${inBand.length} answers found, ${band.count} needed`)
  }
  const step = inBand.length / band.count

  return Array.from({ length: band.count }, (_, i) => inBand[Math.floor(i * step)]).map((one, i) => ({
    id: `${band.name}-${i + 1}`,
    source: one.source,
    chars: one.text.length,
    utterances: utterances(one.text),
  }))
})
writeFileSync(out, JSON.stringify({ readings }, null, 2))
for (const one of readings) {
  console.log(`${one.id}\t${one.source}\t${one.chars} characters\t${one.utterances.length} utterances`)
}
