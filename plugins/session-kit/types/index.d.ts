// The values session-kit keeps in `$.state`, declared for the engine's
// contract check (`claude plugin validate`) and for the editor.

export type ContextFigure = {
  tokens: number
  window: number
  percent: number
}

declare module 'claude-code' {
  interface PluginState {
    'session-kit': {
      /** The context size at which the model was last warned; 0 before any. */
      contextWarnedAt: number
      /** The last figure read from the engine, for the band; null before any. */
      contextFigure: ContextFigure | null
    }
  }
}
