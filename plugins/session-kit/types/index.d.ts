// The values session-kit keeps in `$.state`, declared for the engine's
// contract check (`claude plugin validate`) and for the editor. The contract
// must be self-contained, so a type of the engine's it keeps is spelled here.

/** One rate-limit window as the engine's `SessionRateLimit` spells it: the kind, the percent used, and when it resets. */
export type UsageWindow = {
  kind: string
  percentUsed: number
  resetsAt?: string
}

export type ContextFigure = {
  tokens: number
  window: number
  percent: number
}

/**
 * The chain, from the model's signal to the continue: `requested` while the
 * signalling turn runs, `handoff` while the handoff is written, `compacting`
 * while the context is compacted, `waiting` once compacted with the next step
 * the owner's.
 */
export type ChainState = {
  stage: 'requested' | 'handoff' | 'compacting' | 'waiting'
  /** True when the next step is the owner's, so the chain stops after the compaction. */
  waitsOnOwner: boolean
  /** The next step, in one line, as the model gave it. */
  note: string
  /** Why the judge stopped the chain, when it did: the next step is then the owner's. */
  stopped?: string
}

/** One chain that went on by itself: the next step it named, and HEAD when it continued (null outside a repository). */
export type ChainStep = {
  note: string
  head: string | null
}

/**
 * A new task the model named: `offered` while the band offers the handoff
 * and the clear, `handoff` while the handoff is written, `clearing` while
 * the context is cleared and the prompt sent again.
 */
export type NewTaskState = {
  stage: 'offered' | 'handoff' | 'clearing'
  /** The new task, in one line, as the model gave it. */
  task: string
}

/**
 * The session's last test run: the command, when it ended, whether it passed,
 * and a fingerprint of the working tree's content after it, null when git
 * could not give one (no repository, a merge under way, too many files).
 */
export type TestRun = {
  command: string
  at: number
  passed: boolean
  tree: string | null
}

/**
 * The same test command failing with the same error: the failed runs after
 * an edit, the second of which names the two-tries rule to the model, and
 * whether a file was edited since the last failed run.
 */
export type TestRetry = {
  command: string
  signature: string
  tries: number
  edited: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'session-kit': {
      /** The context size at which the model was last warned; 0 before any. */
      contextWarnedAt: number
      /** The last figure read from the engine, for the band; null before any. */
      contextFigure: ContextFigure | null
      /** The context size at which the person dismissed the figure's band; 0 before any. */
      contextDismissedAt: number
      /** The chain under way; null while none is. */
      chain: ChainState | null
      /** The chains that went on by themselves since the person's last prompt, the evidence the judge reads. */
      chainSteps: ChainStep[]
      /** The new task offered to the person; null while none is. */
      newTask: NewTaskState | null
      /** The person's last prompt, sent again after a clear or when they keep going. */
      lastPrompt: string
      /** When the person's last prompt was submitted, in epoch milliseconds; 0 before any. The handoff's facts count the commits since. */
      lastPromptAt: number
      /** True while the prompt under way opened a context that held no task (new or just cleared). */
      freshContext: boolean
      /** When the cold-cache timer runs the handoff and the compaction, in epoch milliseconds; 0 while none is set. */
      coldTimerAt: number
      /** The prompt cache's lifetime in minutes as the engine last stated it; 0 before any statement, when the option holds. */
      cacheMinutes: number
      /** The context size at the last main-loop turn's end; 0 before any. */
      turnEndTokens: number
      /** How much the context grew over the last main-loop turn; 0 before a second turn, and when it shrank. */
      turnGrowth: number
      /** The account's rate-limit windows as the engine last measured them; empty off a subscription. */
      rateLimits: UsageWindow[]
      /** Per window kind, the percent used at which the person dismissed its line; dropped when the window resets. */
      limitsDismissed: Record<string, number>
      /** The last test run, stamped with the tree it ran on; null before any. */
      lastTest: TestRun | null
      /** The test command failing the same way, counted across edits; null while none is, and after a pass. */
      testRetry: TestRetry | null
    }
  }
}
