export interface DetectorSettings {
  /** Search band, Hz */
  bandLow: number
  bandHigh: number
  /** Peak must stand this many dB above the band median */
  prominenceDb: number
  /** Ignore peaks below this level (dBFS, approx.) */
  minLevelDb: number
  /** Max deviation of the peak frequency from its running median, Hz */
  freqTolHz: number
  /** Frames (50 ms each) used for the frequency-stability test */
  stableFrames: number
  /** Consecutive tone frames to declare ON */
  onFrames: number
  /** Consecutive non-tone frames to declare OFF */
  offFrames: number
  /** A bip reappearing at the same frequency within this many seconds is merged into the previous event */
  mergeGapS: number
}

export const DEFAULT_SETTINGS: DetectorSettings = {
  bandLow: 2500,
  bandHigh: 3500,
  prominenceDb: 15,
  minLevelDb: -90,
  freqTolHz: 15,
  stableFrames: 10,
  onFrames: 6,
  offFrames: 20,
  mergeGapS: 3,
}

export interface BipEvent {
  id: number
  /** Epoch ms */
  start: number
  /** Epoch ms, null while the bip is still on */
  end: number | null
  /** Median peak frequency while on, Hz */
  freqHz: number
  freqMinHz: number
  freqMaxHz: number
  /** Peak level, dBFS (approx.) */
  levelPeakDb: number
  levelMeanDb: number
  /** Mean prominence above the band median, dB */
  prominenceDb: number
  /** Number of 50 ms frames flagged as tone */
  frames: number
}

export type DetectorStatus = 'idle' | 'listening' | 'bip'
