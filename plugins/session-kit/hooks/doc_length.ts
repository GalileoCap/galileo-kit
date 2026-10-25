// The document-length warning, in-process: after an Edit or a Write of a
// markdown file under `docs/`, the model is told when the file is past the
// cap (the `docLines` option, 1500), since a file pushed past a length cap is
// split by whoever pushed it. A hook that fails leaves the call as it ran.

import type { EngineInterface, Register } from 'claude-code'

const DOC_LINES = 1500

function countLines(text: string): number {
  if (text === '') {
    return 0
  }
  const newlines = text.split('\n').length - 1

  return text.endsWith('\n') ? newlines : newlines + 1
}

async function past($: EngineInterface, path: string, limit: number): Promise<string | null> {
  if (!path.includes('/docs/') || !path.endsWith('.md')) {
    return null
  }
  const lines = countLines(await $.fs.read(path))

  return lines > limit ? `${path} is ${lines} lines, past the ${limit}-line cap: split it at the seam it shows.` : null
}

export const register: Register = (on, options) => {
  const limit = typeof options.docLines === 'number' && options.docLines > 0 ? options.docLines : DOC_LINES

  on('tool.call', { tool: 'Edit' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined) {
      return ran
    }
    const note = await past($, e.file_path, limit)

    return note === null ? ran : { ...ran, context: [...(ran.context ?? []), note] }
  }).catch(($, e, next) => next(e))

  on('tool.call', { tool: 'Write' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined) {
      return ran
    }
    const note = await past($, e.file_path, limit)

    return note === null ? ran : { ...ran, context: [...(ran.context ?? []), note] }
  }).catch(($, e, next) => next(e))
}
