<script setup lang="ts">
import { ref } from 'vue'
import type { BipEvent } from '../types/bip'
import { copyText, durationS, eventToText, formatDuration, formatTimestamp } from '../composables/useFormat'

const props = defineProps<{ event: BipEvent; now: number }>()
const emit = defineEmits<{ remove: [id: number] }>()

const copied = ref(false)

async function copy() {
  copied.value = await copyText(eventToText(props.event))
  setTimeout(() => (copied.value = false), 1500)
}
</script>

<template>
  <div
    class="rounded-xl p-4 bg-white dark:bg-dark-800 shadow-sm border"
    :class="event.end === null ? 'border-accent' : 'border-gray-200 dark:border-dark-700'"
  >
    <div class="flex items-center justify-between mb-2">
      <div class="font-semibold">
        BIP #{{ event.id }}
        <span v-if="event.end === null" class="ml-2 text-xs px-2 py-0.5 rounded-full bg-accent text-white animate-pulse">on</span>
      </div>
      <div class="flex gap-2">
        <button
          @click="copy"
          class="px-3 py-1 text-sm rounded-lg bg-beat text-white hover:opacity-90 transition-opacity"
        >
          {{ copied ? 'Copied' : 'Copy' }}
        </button>
        <button
          v-if="event.end !== null"
          @click="emit('remove', event.id)"
          class="px-2 py-1 text-sm rounded-lg bg-gray-200 dark:bg-dark-700 hover:bg-gray-300 dark:hover:bg-dark-900 transition-colors"
          title="Remove"
        >
          ✕
        </button>
      </div>
    </div>
    <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm font-mono">
      <dt class="text-gray-500">start</dt>
      <dd>{{ formatTimestamp(event.start) }}</dd>
      <dt class="text-gray-500">end</dt>
      <dd>{{ event.end ? formatTimestamp(event.end) : '…' }}</dd>
      <dt class="text-gray-500">duration</dt>
      <dd>{{ formatDuration(durationS(event, now)) }}</dd>
      <dt class="text-gray-500">frequency</dt>
      <dd>{{ event.freqHz.toFixed(0) }} Hz <span class="text-gray-500">({{ event.freqMinHz.toFixed(0) }}–{{ event.freqMaxHz.toFixed(0) }})</span></dd>
      <dt class="text-gray-500">level</dt>
      <dd>peak {{ event.levelPeakDb.toFixed(1) }} dBFS <span class="text-gray-500">· mean {{ event.levelMeanDb.toFixed(1) }}</span></dd>
      <dt class="text-gray-500">prominence</dt>
      <dd>{{ event.prominenceDb.toFixed(1) }} dB</dd>
    </dl>
  </div>
</template>
