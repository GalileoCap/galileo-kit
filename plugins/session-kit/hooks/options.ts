// The kit's plugin options, read once where the hooks are registered, and the
// two figures that follow from them: where the context warning starts and
// whether the context has grown a step past a mark.

export const THRESHOLD_TOKENS = 250000
const STEP_TOKENS = 25000
const CACHE_MINUTES = 60
const CACHE_LEAD_MINUTES = 5

/** The cold-cache timer's settings: the cache's lifetime and the lead, in minutes, and the floor of context in tokens (0: the warning's trigger). */
export type ColdOptions = {
  lifetime: number
  lead: number
  floor: number
}

export type KitOptions = {
  thresholdTokens: number
  thresholdPercent: number
  step: number
  chainOn: boolean
  /** Whether the kit keeps a status line under the prompt; off, the usage windows draw on the band from 80%. */
  statusLine: boolean
  cold: ColdOptions
}

export function asNumber(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) && value > 0 ? value : fallback
}

export function asCount(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : fallback
}

export function readOptions(options: Readonly<Record<string, unknown>>): KitOptions {
  return {
    thresholdTokens: asCount(options.thresholdTokens, THRESHOLD_TOKENS),
    thresholdPercent: asCount(options.threshold, 0),
    step: asNumber(options.step, STEP_TOKENS),
    chainOn: options.chain === true,
    statusLine: options.statusLine !== false,
    cold: {
      lifetime: asCount(options.cacheMinutes, CACHE_MINUTES),
      lead: asCount(options.cacheLeadMinutes, CACHE_LEAD_MINUTES),
      floor: asCount(options.cacheFloorTokens, 0),
    },
  }
}

/** Where the warning starts: the token count, or the percent of the window, whichever is reached first; 0 turns one off. */
export function triggerTokens(thresholdTokens: number, thresholdPercent: number, window: number): number {
  const byCount = thresholdTokens > 0 ? thresholdTokens : Infinity
  const byPercent = thresholdPercent > 0 ? (window * thresholdPercent) / 100 : Infinity
  const trigger = Math.min(byCount, byPercent)

  return Number.isFinite(trigger) ? trigger : THRESHOLD_TOKENS
}

/** Whether `tokens` is within a step above `mark`: a context smaller than the mark has been compacted. */
export function withinStep(mark: number, tokens: number, step: number): boolean {
  return mark > 0 && mark <= tokens && tokens < mark + step
}
