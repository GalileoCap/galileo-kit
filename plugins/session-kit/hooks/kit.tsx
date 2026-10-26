// The session-kit hooks module: the engine loads one module per plugin, so
// this one calls the register of each concern, one file each. The hooks of
// one module nest in the order they are registered, the first outermost: the
// timeline's own hooks come first, and a stopwatch stands before each concern
// and after the last, so the timeline times each concern by name. The
// handoff's facts come before the context concern, so they are in the file
// before the chain asks for the compaction.

import type { Register } from 'claude-code'

import { register as checkout } from './checkout'
import { register as context } from './context'
import { register as docLength } from './doc_length'
import { register as facts } from './facts'
import { lap, lapBeneath, register as measure } from './measure'
import { register as nudge } from './nudge'
import { register as suppressions } from './suppressions'
import { register as testLog } from './test_log'

export const register: Register = (on, options) => {
  measure(on, options)
  lap(on, options, 'facts')
  facts(on, options)
  lap(on, options, 'context')
  context(on, options)
  lap(on, options, 'test_log')
  testLog(on, options)
  lap(on, options, 'doc_length')
  docLength(on, options)
  lap(on, options, 'nudge')
  nudge(on, options)
  lap(on, options, 'checkout')
  checkout(on, options)
  lap(on, options, 'suppressions')
  suppressions(on, options)
  lapBeneath(on, options)
}
