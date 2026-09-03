# Bip detector

A small web app that listens to the microphone and logs every occurrence of a continuous ~3 kHz
"bip" (a pure, stable tone). Each detection is an event with the information needed to report it:
start and end timestamp, duration, frequency, sound level. Events can be copied as plain text
(one event) or CSV (all events).

Live: https://www.tintamarre.be/bip-detector/ (HTTPS is required for microphone access)

## How it works

1. Press **Start listening**. The browser asks for microphone access (no processing: echo
   cancellation, auto gain and noise suppression are disabled).
2. Every 50 ms an 8192-point FFT is taken. Inside the search band (2.5-3.5 kHz by default) the
   strongest bin is compared to the median of the band: this is the **prominence**.
3. A frame counts as "tone" when the prominence is above the threshold (15 dB) and the peak
   frequency has not moved (±15 Hz over the last 0.5 s). Speech and music sweep; the bip does not.
4. Hysteresis: the bip is declared **ON** after 0.3 s of consecutive tone frames. While ON, the peak
   must stay on the event's own frequency; the bip is declared **OFF** when a sliding 1 s window
   contains almost no tone frames.
5. Each ON/OFF pair becomes an event card. The running event shows a live duration.

Events are kept in `localStorage` so they survive a reload. The screen is kept awake while
listening (where the browser supports it), and the phone vibrates on detection.

### Event fields

| Field | Meaning |
|---|---|
| start / end | local time, millisecond precision |
| duration | seconds between ON and OFF |
| frequency | median peak frequency while on (min–max in parentheses) |
| level | peak and mean level of the tone bin, approximate dBFS as reported by the Web Audio analyser |
| prominence | mean dB of the peak above the band median |

Text copied for one event:

```
BIP #3
start:      2026-09-03 09:41:12.350
end:        2026-09-03 09:41:29.100
duration:   16.8 s
frequency:  3151 Hz (min 3146, max 3158)
level:      peak -53.2 dBFS, mean -55.8 dBFS
prominence: 28.4 dB above band median
```

"Copy all" gives a CSV with the same fields and ISO timestamps.

## Settings

The **Detector settings** panel exposes the parameters (band, prominence, minimum level,
frequency tolerance, stability window, ON/OFF frame counts). They are saved in the browser.
The defaults come from the analysis of real recordings, see [`analysis/README.md`](analysis/README.md):
the bip was measured at 3151 Hz in one recording and 2942 Hz in two others, hence the wide band.

## Development

```bash
npm install
npm run dev       # http://localhost:5173/bip-detector/
npm run build     # type-check + production build in dist/
```

Deployed to GitHub Pages by `.github/workflows/deploy.yml` on every push to `main`
(Pages must be set to "GitHub Actions" as source in the repository settings).

Microphone access requires HTTPS or `localhost`.

## Repository layout

- `src/composables/useBipDetector.ts`: microphone, FFT, detection state machine, event log
- `src/composables/useFormat.ts`: text/CSV formatting and clipboard
- `src/components/BandSpectrum.vue`: live spectrum of the search band
- `src/components/EventCard.vue`: one event with its Copy button
- `analysis/`: Python characterisation of the bip (scripts, plots, and a reference detector)

---

Built with Vue 3, TypeScript, Vite and Tailwind CSS, same stack as
[metronome](https://github.com/tintamarre/metronome).
