<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

const props = defineProps<{
  bins: Float32Array
  freqs: Float32Array
  peakIndex: number
  isTone: boolean
  thresholdDb: number
}>()

const canvas = ref<HTMLCanvasElement | null>(null)
const MIN_DB = -130
const MAX_DB = -20

function draw() {
  const c = canvas.value
  if (!c) return
  const ctx = c.getContext('2d')
  if (!ctx) return
  const dpr = window.devicePixelRatio || 1
  const w = c.clientWidth
  const h = c.clientHeight
  if (c.width !== w * dpr || c.height !== h * dpr) {
    c.width = w * dpr
    c.height = h * dpr
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, w, h)

  const n = props.bins.length
  if (n === 0) return
  const y = (db: number) => h - ((Math.max(MIN_DB, Math.min(MAX_DB, db)) - MIN_DB) / (MAX_DB - MIN_DB)) * h

  // band median line
  const sorted = Array.from(props.bins).sort((a, b) => a - b)
  const med = sorted[sorted.length >> 1]!
  ctx.strokeStyle = 'rgba(128,128,128,0.6)'
  ctx.setLineDash([4, 4])
  ctx.beginPath()
  ctx.moveTo(0, y(med))
  ctx.lineTo(w, y(med))
  ctx.stroke()
  // threshold line (median + prominence)
  ctx.strokeStyle = 'rgba(231,111,81,0.7)'
  ctx.beginPath()
  ctx.moveTo(0, y(med + props.thresholdDb))
  ctx.lineTo(w, y(med + props.thresholdDb))
  ctx.stroke()
  ctx.setLineDash([])

  // spectrum
  ctx.strokeStyle = props.isTone ? '#e76f51' : '#2a9d8f'
  ctx.lineWidth = 1.5
  ctx.beginPath()
  for (let i = 0; i < n; i++) {
    const x = (i / (n - 1)) * w
    const yy = y(props.bins[i]!)
    if (i === 0) ctx.moveTo(x, yy)
    else ctx.lineTo(x, yy)
  }
  ctx.stroke()

  // peak marker
  if (props.peakIndex >= 0 && props.peakIndex < n) {
    const x = (props.peakIndex / (n - 1)) * w
    ctx.fillStyle = props.isTone ? '#e76f51' : '#9ca3af'
    ctx.beginPath()
    ctx.arc(x, y(props.bins[props.peakIndex]!), 4, 0, Math.PI * 2)
    ctx.fill()
  }

  // axis labels
  ctx.fillStyle = 'rgba(128,128,128,0.9)'
  ctx.font = '10px system-ui'
  ctx.textAlign = 'left'
  ctx.fillText(`${props.freqs[0]!.toFixed(0)} Hz`, 2, h - 2)
  ctx.textAlign = 'right'
  ctx.fillText(`${props.freqs[n - 1]!.toFixed(0)} Hz`, w - 2, h - 2)
  ctx.textAlign = 'left'
  ctx.fillText(`${MAX_DB} dB`, 2, 10)
}

watch(() => props.bins, draw)
onMounted(draw)
</script>

<template>
  <canvas ref="canvas" class="w-full h-32 rounded-lg bg-gray-100 dark:bg-dark-800"></canvas>
</template>
