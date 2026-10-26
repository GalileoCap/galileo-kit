// The values read-aloud keeps in `$.state`, declared for the engine's
// contract check (`claude plugin validate`) and for the editor.

/** Whether each answer is read as its turn ends, as /read-aloud auto set it; null leaves it to the `auto` option. */
export type AutoRead = boolean | null

declare module 'claude-code' {
  interface PluginState {
    'read-aloud': {
      /** The final answer of the last main-session turn that ended with one, as the model wrote it. */
      answer: string | null
      /** True while an answer is being read. */
      isSpeaking: boolean
      isAuto: AutoRead
    }
  }
}
