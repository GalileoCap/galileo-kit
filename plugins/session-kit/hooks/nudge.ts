// The single-edit nudge, in-process: a Bash call that is a Python heredoc
// doing one read, one replace and one write is told that the Edit tool makes
// the same change for fewer tokens. A regex, a loop, two replaces or several
// files are left alone, since those are what a script is for. A hook that
// fails leaves the call as it ran.

import type { Register } from 'claude-code'

const NUDGE =
  'This Bash call is a Python heredoc doing one file edit: a read, one replace, ' +
  'a write. The Edit tool makes the same change for about a third fewer tokens ' +
  'and shows it as a diff.'

function heredocBody(command: string): string | null {
  const lines = command.split('\n')
  const start = lines.findIndex((line) => /<<-?\s*['"]?\w+['"]?/.test(line))
  if (start < 0) {
    return null
  }
  const delimiter = /<<-?\s*['"]?(\w+)['"]?/.exec(lines[start] ?? '')?.[1]
  const body = lines.slice(start + 1)
  const end = body.findIndex((line) => line.trim() === delimiter)

  return (end < 0 ? body : body.slice(0, end)).join('\n')
}

function isHeredocEdit(command: string): boolean {
  if (!/^\(?python3(\s|$)/.test(command.trim()) || !command.includes('<<')) {
    return false
  }
  const replaces = /\.replace\(/.test(command)
  const reads = /read_text\(|\.read\(\)/.test(command)
  const writes = /write_text\(|\.write\(/.test(command)

  return replaces || (reads && writes)
}

export function classify(command: string): 'regex' | 'multi_file' | 'multi_edit' | 'single_edit' | null {
  const body = heredocBody(command)
  if (body === null) {
    return null
  }
  if (/\bre\.sub\(/.test(body)) {
    return 'regex'
  }
  const paths = new Set([...body.matchAll(/\b(?:open|Path)\(\s*(['"])([^'"]*)\1/g)].map((m) => m[2]))
  if (/\.(?:glob|rglob)\(|\bos\.walk\(/.test(body) || paths.size > 1) {
    return 'multi_file'
  }
  const replaces = body.match(/\.replace\(/g)?.length ?? 0
  if (/^\s*for\b.*:\s*$/m.test(body) || replaces >= 2) {
    return 'multi_edit'
  }

  return 'single_edit'
}

export function isSingleEdit(command: string): boolean {
  return isHeredocEdit(command) && classify(command) === 'single_edit'
}

export const register: Register = (on) => {
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const ran = await next(e)
    if (ran.deny !== undefined || !isSingleEdit(e.command)) {
      return ran
    }

    return { ...ran, context: [...(ran.context ?? []), NUDGE] }
  }).catch(($, e, next) => next(e))
}
