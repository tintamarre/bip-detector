import type { BipEvent } from '../types/bip'

function pad(n: number, w = 2) {
  return String(n).padStart(w, '0')
}

/** Local time as "YYYY-MM-DD HH:MM:SS.mmm" */
export function formatTimestamp(ms: number): string {
  const d = new Date(ms)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}.${pad(d.getMilliseconds(), 3)}`
}

export function formatTime(ms: number): string {
  const d = new Date(ms)
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

export function durationS(e: BipEvent, now = Date.now()): number {
  return ((e.end ?? now) - e.start) / 1000
}

export function formatDuration(s: number): string {
  if (s < 60) return `${s.toFixed(1)} s`
  const m = Math.floor(s / 60)
  return `${m} min ${(s - m * 60).toFixed(0)} s`
}

export function eventToText(e: BipEvent): string {
  const lines = [
    `BIP #${e.id}`,
    `start:      ${formatTimestamp(e.start)}`,
    `end:        ${e.end ? formatTimestamp(e.end) : '(still on)'}`,
    `duration:   ${durationS(e).toFixed(1)} s`,
    `frequency:  ${e.freqHz.toFixed(0)} Hz (min ${e.freqMinHz.toFixed(0)}, max ${e.freqMaxHz.toFixed(0)})`,
    `level:      peak ${e.levelPeakDb.toFixed(1)} dBFS, mean ${e.levelMeanDb.toFixed(1)} dBFS`,
    `prominence: ${e.prominenceDb.toFixed(1)} dB above band median`,
  ]
  return lines.join('\n')
}

export const CSV_HEADER =
  'id,start,end,duration_s,freq_hz,freq_min_hz,freq_max_hz,level_peak_dbfs,level_mean_dbfs,prominence_db'

export function eventToCsv(e: BipEvent): string {
  return [
    e.id,
    new Date(e.start).toISOString(),
    e.end ? new Date(e.end).toISOString() : '',
    durationS(e).toFixed(2),
    e.freqHz.toFixed(1),
    e.freqMinHz.toFixed(1),
    e.freqMaxHz.toFixed(1),
    e.levelPeakDb.toFixed(1),
    e.levelMeanDb.toFixed(1),
    e.prominenceDb.toFixed(1),
  ].join(',')
}

export function eventsToCsv(events: BipEvent[]): string {
  return [CSV_HEADER, ...[...events].reverse().map(eventToCsv)].join('\n')
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    // Fallback for non-secure contexts
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    return ok
  }
}
