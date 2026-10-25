// The session-kit hooks module: the engine loads one module per plugin, so
// this one calls the register of each concern, one file each.

import type { Register } from 'claude-code'

import { register as context } from './context'
import { register as docLength } from './doc_length'
import { register as nudge } from './nudge'
import { register as testLog } from './test_log'

export const register: Register = (on, options) => {
  context(on, options)
  testLog(on, options)
  docLength(on, options)
  nudge(on, options)
}
