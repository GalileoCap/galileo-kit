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
      /** Chains that continued since the person's last prompt; the third signal is refused. */
      chainsUnattended: number
      /** The new task offered to the person; null while none is. */
      newTask: NewTaskState | null
      /** The person's last prompt, sent again after a clear or when they keep going. */
      lastPrompt: string
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
    }
  }
}
