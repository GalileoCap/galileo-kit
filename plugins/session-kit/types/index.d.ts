// The values session-kit keeps in `$.state`, declared for the engine's
// contract check (`claude plugin validate`) and for the editor.

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

declare module 'claude-code' {
  interface PluginState {
    'session-kit': {
      /** The context size at which the model was last warned; 0 before any. */
      contextWarnedAt: number
      /** The last figure read from the engine, for the band; null before any. */
      contextFigure: ContextFigure | null
      /** The chain under way; null while none is. */
      chain: ChainState | null
    }
  }
}
