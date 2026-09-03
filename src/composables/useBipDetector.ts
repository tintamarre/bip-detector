import { ref, shallowRef, computed } from 'vue'
import { DEFAULT_SETTINGS, type BipEvent, type DetectorSettings, type DetectorStatus } from '../types/bip'

const FFT_SIZE = 8192
const HOP_MS = 50
const EXCLUDE_HZ = 60
const STORAGE_KEY = 'bip-detector-events'
const SETTINGS_KEY = 'bip-detector-settings'

function median(values: number[]): number {
  if (values.length === 0) return NaN
  const s = [...values].sort((a, b) => a - b)
  const m = s.length >> 1
  return s.length % 2 ? s[m]! : (s[m - 1]! + s[m]!) / 2
}

function loadJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? { ...fallback, ...JSON.parse(raw) } : fallback
  } catch {
    return fallback
  }
}

export function useBipDetector() {
  const settings = ref<DetectorSettings>(loadJson(SETTINGS_KEY, DEFAULT_SETTINGS))
  const events = ref<BipEvent[]>(loadJson<{ list: BipEvent[] }>(STORAGE_KEY, { list: [] }).list)

  const isListening = ref(false)
  const status = ref<DetectorStatus>('idle')
  const error = ref<string | null>(null)
  const sampleRate = ref(0)

  // Live values (updated every frame)
  const liveFreq = ref(0)
  const liveLevel = ref(-Infinity)
  const liveProminence = ref(0)
  const liveIsTone = ref(false)
  const bandDb = shallowRef<Float32Array>(new Float32Array(0))
  const bandFreqs = shallowRef<Float32Array>(new Float32Array(0))
  const peakIndex = ref(-1)

  const currentEvent = computed(() => events.value.find((e) => e.end === null) ?? null)

  let audioContext: AudioContext | null = null
  let analyser: AnalyserNode | null = null
  let mediaStream: MediaStream | null = null
  let timer: number | null = null
  let wakeLock: WakeLockSentinel | null = null
  let spectrum = new Float32Array(0)

  // Detector state
  let recentFreqs: number[] = []
  let runOn = 0
  let recentTone: boolean[] = []
  let on = false
  let lockFreq = 0
  type Acc = { freqs: number[]; levelPeak: number; levelSum: number; promSum: number; n: number }
  const emptyAcc = (): Acc => ({ freqs: [], levelPeak: -Infinity, levelSum: 0, promSum: 0, n: 0 })
  let acc: Acc = emptyAcc()
  /** Accumulator of the last closed event, kept so a quick re-appearance can be merged */
  let lastAcc: Acc | null = null

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ list: events.value }))
    } catch {
      /* storage may be unavailable */
    }
  }

  function saveSettings() {
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings.value))
    } catch {
      /* ignore */
    }
  }

  function resetSettings() {
    settings.value = { ...DEFAULT_SETTINGS }
    saveSettings()
  }

  function processFrame() {
    if (!analyser || !audioContext) return
    const s = settings.value
    const sr = audioContext.sampleRate
    const binHz = sr / FFT_SIZE
    analyser.getFloatFrequencyData(spectrum)

    const lo = Math.max(1, Math.floor(s.bandLow / binHz))
    const hi = Math.min(spectrum.length - 1, Math.ceil(s.bandHigh / binHz))
    if (hi - lo < 10) return

    // Peak in band
    let k = lo
    for (let i = lo + 1; i <= hi; i++) if (spectrum[i]! > spectrum[k]!) k = i
    const peakDb = spectrum[k]!
    const peakHz = k * binHz

    // Median of the band excluding +-EXCLUDE_HZ around the peak
    const excl = Math.ceil(EXCLUDE_HZ / binHz)
    const others: number[] = []
    for (let i = lo; i <= hi; i++) if (Math.abs(i - k) > excl) others.push(spectrum[i]!)
    const prom = peakDb - median(others)

    // Expose live values
    const nb = hi - lo + 1
    if (bandDb.value.length !== nb) {
      bandFreqs.value = Float32Array.from({ length: nb }, (_, i) => (lo + i) * binHz)
    }
    bandDb.value = spectrum.slice(lo, hi + 1)
    peakIndex.value = k - lo
    liveFreq.value = peakHz
    liveLevel.value = peakDb
    liveProminence.value = prom

    // Frame test + frequency stability
    const frameOk = prom >= s.prominenceDb && peakDb >= s.minLevelDb
    let stable = false
    if (frameOk) {
      recentFreqs.push(peakHz)
      if (recentFreqs.length > s.stableFrames) recentFreqs.shift()
      stable =
        recentFreqs.length >= Math.max(1, Math.floor(s.stableFrames / 2)) &&
        Math.abs(peakHz - median(recentFreqs)) <= s.freqTolHz
    } else {
      recentFreqs = []
    }
    // While an event is running, the peak must stay on the event's own frequency
    if (on && stable && Math.abs(peakHz - lockFreq) > s.freqTolHz) stable = false
    liveIsTone.value = stable

    recentTone.push(stable)
    if (recentTone.length > s.offFrames) recentTone.shift()
    const toneInWindow = recentTone.filter(Boolean).length
    const offCondition = recentTone.length >= s.offFrames && toneInWindow <= Math.floor(s.offFrames / 10)

    if (stable) {
      runOn++
      acc.freqs.push(peakHz)
      acc.levelPeak = Math.max(acc.levelPeak, peakDb)
      acc.levelSum += peakDb
      acc.promSum += prom
      acc.n++
    } else {
      runOn = 0
    }

    const now = Date.now()
    if (!on && runOn >= s.onFrames) {
      on = true
      status.value = 'bip'
      const start = now - (s.onFrames - 1 + Math.floor(s.stableFrames / 2)) * HOP_MS
      const prev = events.value[0]
      const freq = median(acc.freqs)
      const canMerge =
        prev !== undefined &&
        prev.end !== null &&
        lastAcc !== null &&
        start - prev.end <= s.mergeGapS * 1000 &&
        Math.abs(freq - prev.freqHz) <= 2 * s.freqTolHz
      if (canMerge && prev && lastAcc) {
        // Same bip coming back after a short dip: reopen the previous event
        acc = {
          freqs: lastAcc.freqs.concat(acc.freqs),
          levelPeak: Math.max(lastAcc.levelPeak, acc.levelPeak),
          levelSum: lastAcc.levelSum + acc.levelSum,
          promSum: lastAcc.promSum + acc.promSum,
          n: lastAcc.n + acc.n,
        }
        prev.end = null
        updateCurrent()
      } else {
        events.value.unshift({
          id: (prev?.id ?? 0) + 1,
          start,
          end: null,
          freqHz: freq,
          freqMinHz: Math.min(...acc.freqs),
          freqMaxHz: Math.max(...acc.freqs),
          levelPeakDb: acc.levelPeak,
          levelMeanDb: acc.levelSum / acc.n,
          prominenceDb: acc.promSum / acc.n,
          frames: acc.n,
        })
      }
      lastAcc = null
      lockFreq = currentEvent.value?.freqHz ?? freq
      try {
        navigator.vibrate?.(200)
      } catch {
        /* not supported */
      }
    } else if (on && stable && acc.n % 4 === 0) {
      updateCurrent()
      lockFreq = currentEvent.value?.freqHz ?? lockFreq
    } else if (on && offCondition) {
      on = false
      status.value = 'listening'
      updateCurrent()
      const ev = currentEvent.value
      if (ev) ev.end = now - (s.offFrames - 1) * HOP_MS
      lastAcc = acc
      acc = emptyAcc()
      persist()
    }
    if (!on && !stable) {
      // no tone: drop accumulated stats from spurious frames
      acc = emptyAcc()
    }
  }

  function updateCurrent() {
    const ev = currentEvent.value
    if (!ev || acc.n === 0) return
    ev.freqHz = median(acc.freqs)
    ev.freqMinHz = Math.min(...acc.freqs)
    ev.freqMaxHz = Math.max(...acc.freqs)
    ev.levelPeakDb = acc.levelPeak
    ev.levelMeanDb = acc.levelSum / acc.n
    ev.prominenceDb = acc.promSum / acc.n
    ev.frames = acc.n
  }

  async function start() {
    if (isListening.value) return
    error.value = null
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: false, autoGainControl: false, noiseSuppression: false },
      })
      audioContext = new AudioContext()
      analyser = audioContext.createAnalyser()
      analyser.fftSize = FFT_SIZE
      analyser.smoothingTimeConstant = 0
      audioContext.createMediaStreamSource(mediaStream).connect(analyser)
      spectrum = new Float32Array(analyser.frequencyBinCount)
      sampleRate.value = audioContext.sampleRate

      recentFreqs = []
      recentTone = []
      runOn = 0
      on = false
      acc = emptyAcc()
      lastAcc = null

      isListening.value = true
      status.value = 'listening'
      timer = window.setInterval(processFrame, HOP_MS)

      try {
        wakeLock = (await navigator.wakeLock?.request('screen')) ?? null
      } catch {
        wakeLock = null
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
      stop()
    }
  }

  function stop() {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
    if (on) {
      // Close the running event at stop time
      const ev = currentEvent.value
      if (ev) ev.end = Date.now()
      on = false
      persist()
    }
    mediaStream?.getTracks().forEach((t) => t.stop())
    mediaStream = null
    audioContext?.close()
    audioContext = null
    analyser = null
    wakeLock?.release()
    wakeLock = null
    isListening.value = false
    status.value = 'idle'
    liveIsTone.value = false
  }

  function toggle() {
    if (isListening.value) stop()
    else void start()
  }

  function clearEvents() {
    events.value = events.value.filter((e) => e.end === null)
    persist()
  }

  function removeEvent(id: number) {
    events.value = events.value.filter((e) => e.id !== id)
    persist()
  }

  return {
    settings,
    events,
    currentEvent,
    isListening,
    status,
    error,
    sampleRate,
    liveFreq,
    liveLevel,
    liveProminence,
    liveIsTone,
    bandDb,
    bandFreqs,
    peakIndex,
    start,
    stop,
    toggle,
    clearEvents,
    removeEvent,
    saveSettings,
    resetSettings,
  }
}
