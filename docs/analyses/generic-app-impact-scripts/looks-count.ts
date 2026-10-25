// Count class strings of two or more classes written in more than one place under a src/.
import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
const { repeatedLooks } = await import(process.argv[2])
const src = process.argv[3]
const sources = readdirSync(src, { recursive: true, encoding: 'utf8' })
  .filter((p: string) => /\.tsx?$/.test(p) && !p.startsWith(join('components', 'ui')))
  .map((p: string) => ({ path: p, text: readFileSync(join(src, p), 'utf8') }))
const found = repeatedLooks(sources, [])
const places = found.reduce((n: number, r: { places: string[] }) => n + r.places.length, 0)
console.log(JSON.stringify({ repeatedLooks: found.length, places }))
