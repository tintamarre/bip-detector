<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useBipDetector } from './composables/useBipDetector'
import { useTheme } from './composables/useTheme'
import { copyText, eventsToCsv, formatDuration } from './composables/useFormat'
import BandSpectrum from './components/BandSpectrum.vue'
import EventCard from './components/EventCard.vue'

const {
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
  toggle,
  clearEvents,
  removeEvent,
  saveSettings,
  resetSettings,
} = useBipDetector()

const { theme, toggleTheme } = useTheme()

// Clock for live durations
const now = ref(Date.now())
let clock: number | null = null
onMounted(() => (clock = window.setInterval(() => (now.value = Date.now()), 250)))
onUnmounted(() => clock !== null && clearInterval(clock))

const copiedAll = ref(false)
async function copyAll() {
  copiedAll.value = await copyText(eventsToCsv(events.value))
  setTimeout(() => (copiedAll.value = false), 1500)
}

const showSettings = ref(false)
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-dark-900 text-gray-900 dark:text-white flex flex-col transition-colors duration-200">
    <!-- Header -->
    <header class="w-full max-w-md mx-auto pt-4 px-4 flex items-center justify-between">
      <h1 class="text-xl font-bold">Bip detector</h1>
      <button
        @click="toggleTheme"
        class="p-2 rounded-lg bg-gray-200 dark:bg-dark-700 hover:bg-gray-300 dark:hover:bg-dark-800 transition-colors"
        :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
      >
        <svg v-if="theme === 'dark'" class="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd" />
        </svg>
        <svg v-else class="w-5 h-5 text-gray-700" fill="currentColor" viewBox="0 0 20 20">
          <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
        </svg>
      </button>
    </header>

    <main class="flex-1 w-full max-w-md mx-auto px-4 py-4 flex flex-col gap-4">
      <!-- Status -->
      <div
        class="rounded-2xl p-6 text-center transition-colors duration-300"
        :class="{
          'bg-gray-200 dark:bg-dark-800': status === 'idle',
          'bg-beat/20 dark:bg-beat/20': status === 'listening',
          'bg-accent text-white': status === 'bip',
        }"
      >
        <div class="text-3xl font-bold tracking-wide">
          <template v-if="status === 'idle'">Idle</template>
          <template v-else-if="status === 'listening'">Listening…</template>
          <template v-else>BIP</template>
        </div>
        <div v-if="currentEvent" class="mt-1 font-mono text-lg">
          {{ formatDuration((now - currentEvent.start) / 1000) }}
        </div>
        <div v-else-if="status === 'listening'" class="mt-1 text-sm opacity-70">no bip detected</div>
        <div v-else class="mt-1 text-sm opacity-70">press Start to listen</div>
      </div>

      <!-- Start / Stop -->
      <button
        @click="toggle"
        class="w-full py-4 rounded-2xl text-lg font-semibold text-white transition-colors"
        :class="isListening ? 'bg-gray-600 hover:bg-gray-700' : 'bg-beat hover:opacity-90'"
      >
        {{ isListening ? 'Stop' : 'Start listening' }}
      </button>
      <p v-if="error" class="text-sm text-red-500">Microphone error: {{ error }}</p>

      <!-- Live values -->
      <div v-if="isListening" class="rounded-xl p-4 bg-white dark:bg-dark-800 shadow-sm">
        <BandSpectrum
          :bins="bandDb"
          :freqs="bandFreqs"
          :peak-index="peakIndex"
          :is-tone="liveIsTone"
          :threshold-db="settings.prominenceDb"
        />
        <div class="grid grid-cols-3 gap-2 mt-3 text-center font-mono text-sm">
          <div>
            <div class="text-gray-500 text-xs">peak</div>
            <div>{{ liveFreq.toFixed(0) }} Hz</div>
          </div>
          <div>
            <div class="text-gray-500 text-xs">level</div>
            <div>{{ isFinite(liveLevel) ? liveLevel.toFixed(0) : '–' }} dBFS</div>
          </div>
          <div>
            <div class="text-gray-500 text-xs">prominence</div>
            <div :class="liveProminence >= settings.prominenceDb ? 'text-accent font-bold' : ''">{{ liveProminence.toFixed(0) }} dB</div>
          </div>
        </div>
        <div class="text-xs text-gray-500 text-center mt-2">sample rate {{ sampleRate }} Hz · frame 50 ms</div>
      </div>

      <!-- Settings -->
      <div class="rounded-xl bg-white dark:bg-dark-800 shadow-sm">
        <button @click="showSettings = !showSettings" class="w-full px-4 py-3 text-left text-sm font-semibold flex justify-between">
          <span>Detector settings</span>
          <span>{{ showSettings ? '▴' : '▾' }}</span>
        </button>
        <div v-if="showSettings" class="px-4 pb-4 grid grid-cols-2 gap-3 text-sm">
          <label class="flex flex-col gap-1">
            <span class="text-gray-500">band low (Hz)</span>
            <input v-model.number="settings.bandLow" @change="saveSettings" type="number" step="50" class="rounded-lg px-2 py-1 bg-gray-100 dark:bg-dark-700" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-gray-500">band high (Hz)</span>
            <input v-model.number="settings.bandHigh" @change="saveSettings" type="number" step="50" class="rounded-lg px-2 py-1 bg-gray-100 dark:bg-dark-700" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-gray-500">prominence (dB)</span>
            <input v-model.number="settings.prominenceDb" @change="saveSettings" type="number" step="1" class="rounded-lg px-2 py-1 bg-gray-100 dark:bg-dark-700" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-gray-500">min level (dBFS)</span>
            <input v-model.number="settings.minLevelDb" @change="saveSettings" type="number" step="5" class="rounded-lg px-2 py-1 bg-gray-100 dark:bg-dark-700" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-gray-500">freq tolerance (Hz)</span>
            <input v-model.number="settings.freqTolHz" @change="saveSettings" type="number" step="5" class="rounded-lg px-2 py-1 bg-gray-100 dark:bg-dark-700" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-gray-500">stability window (frames)</span>
            <input v-model.number="settings.stableFrames" @change="saveSettings" type="number" step="1" class="rounded-lg px-2 py-1 bg-gray-100 dark:bg-dark-700" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-gray-500">ON after (frames)</span>
            <input v-model.number="settings.onFrames" @change="saveSettings" type="number" step="1" class="rounded-lg px-2 py-1 bg-gray-100 dark:bg-dark-700" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-gray-500">OFF after (frames)</span>
            <input v-model.number="settings.offFrames" @change="saveSettings" type="number" step="1" class="rounded-lg px-2 py-1 bg-gray-100 dark:bg-dark-700" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-gray-500">merge gap (s)</span>
            <input v-model.number="settings.mergeGapS" @change="saveSettings" type="number" step="0.5" min="0" class="rounded-lg px-2 py-1 bg-gray-100 dark:bg-dark-700" />
          </label>
          <button @click="resetSettings" class="col-span-2 py-1 rounded-lg bg-gray-200 dark:bg-dark-700 hover:bg-gray-300 dark:hover:bg-dark-900 transition-colors">
            Reset to defaults
          </button>
        </div>
      </div>

      <!-- Events -->
      <section class="flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">Events <span class="text-gray-500 font-normal">({{ events.length }})</span></h2>
          <div class="flex gap-2" v-if="events.length">
            <button @click="copyAll" class="px-3 py-1 text-sm rounded-lg bg-beat text-white hover:opacity-90 transition-opacity">
              {{ copiedAll ? 'Copied' : 'Copy all (CSV)' }}
            </button>
            <button @click="clearEvents" class="px-3 py-1 text-sm rounded-lg bg-gray-200 dark:bg-dark-700 hover:bg-gray-300 dark:hover:bg-dark-900 transition-colors">
              Clear
            </button>
          </div>
        </div>
        <p v-if="!events.length" class="text-sm text-gray-500">No event yet. Each detected bip appears here with its start time, duration, frequency and level.</p>
        <EventCard v-for="e in events" :key="e.id" :event="e" :now="now" @remove="removeEvent" />
      </section>
    </main>

    <footer class="text-center text-xs text-gray-500 py-4">
      Events are stored in this browser only. Levels are approximate dBFS from the browser's FFT.
    </footer>
  </div>
</template>
