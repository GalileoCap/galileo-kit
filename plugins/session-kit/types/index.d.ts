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
  /** The effort the model proposed for the new task with its reason, kept only when it differs from the session's. */
  effort?: { level: Effort; reason: string }
  /** True once the person chose the clear at the proposed effort. */
  setsEffort?: boolean
}

/**
 * A failure the person has not dismissed: what did not run and what the kit
 * did about it. A chain failure carries `retry`, the stage to run again with the
 * note and the owner's say the chain had.
 */
export type Failure = {
  text: string
  retry?: { stage: 'handoff' | 'compacting'; waitsOnOwner: boolean; note: string }
}

/** One line of the chain's journal, kept for the pane: when it was written, in epoch milliseconds, and what it says. */
export type StageLine = {
  at: number
  text: string
}

/** The context percent a main-loop turn ended at, keyed by the turn's duration, which is what the turn line carries to find it. */
export type TurnFigure = {
  durationMs: number
  percent: number
}

/** A reasoning effort as the engine's `ModelEffort` spells it. */
export type Effort = 'low' | 'medium' | 'high' | 'xhigh' | 'max'

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
  /** The person was told at a turn's end that the run is stale, and the tree has not come back to it since. */
  staleShown?: boolean
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

/** One item of the owner's tagged lines: its id (the tag word, a hyphen, a number), its tag, and its first words. */
export type TaggedItem = {
  id: string
  tag: 'Do' | 'Decide' | 'Ask' | 'Later'
  text: string
}

/** A message the pre-send check held: the text as the person wrote it (the `??` taken off), Haiku's findings, and its rewrite when it gave one. */
export type PresendHeld = {
  text: string
  findings: string[]
  rewrite: string | null
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
      /** The effort the session's last main-loop request was sent at; null before any, or for a model that takes none. */
      sessionEffort: Effort | null
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
      /** The failure the band shows until the person dismisses it; null while none is. */
      failure: Failure | null
      /** The last lines of the chain's journal, for the pane; the newest last. */
      stages: StageLine[]
      /** The context percent at the end of the last main-loop turns, for the turn line. */
      turnFigures: TurnFigure[]
      /** The last test run, stamped with the tree it ran on; null before any. */
      lastTest: TestRun | null
      /** The titles of the pane's folded sections; null until the first fold of the session, when the store's are read. */
      paneFolded: string[] | null
      /** Per list of the pane, the first item its window shows; a list left out starts at its top. */
      paneScroll: Record<string, number>
      /** The message the pre-send check holds for the person's decision; null while none is. */
      presendHeld: PresendHeld | null
      /** The text Send as is sent or Use the rewrite prepared, let through unchecked once; empty while none is. */
      presendPass: string
      /** Per tag, the last number given to an item in this session; a clear starts them over. */
      tagCounts: Record<string, number>
      /** The owner's tagged items not yet reported done, decided, parked or answered, oldest first. */
      openItems: TaggedItem[]
      /** The open items the last checked reply left without a line, for the band; emptied by a dismissal. */
      itemsMissed: TaggedItem[]
      /** The ids the kit has already prompted the session about, once each. */
      itemsPrompted: string[]
      /** True from a tagged prompt (the person's, or the kit's own about a missed item) until its turn ends. */
      tagCheckDue: boolean
      /** The test command failing the same way, counted across edits; null while none is, and after a pass. */
      testRetry: TestRetry | null
    }
  }
}
