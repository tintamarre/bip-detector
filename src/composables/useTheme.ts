import { ref, watch, onMounted } from 'vue'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'bip-detector-theme'

export function useTheme() {
  const theme = ref<Theme>('dark')

  function applyTheme(newTheme: Theme) {
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  function setTheme(newTheme: Theme) {
    theme.value = newTheme
  }

  // Watch for changes and persist
  watch(theme, (newTheme) => {
    applyTheme(newTheme)
    localStorage.setItem(STORAGE_KEY, newTheme)
  })

  // Initialize on mount
  onMounted(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null
    if (stored) {
      theme.value = stored
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      theme.value = prefersDark ? 'dark' : 'light'
    }
    applyTheme(theme.value)
  })

  return {
    theme,
    toggleTheme,
    setTheme,
  }
}
