#!/usr/bin/env python3
"""
Prototype "bip sensor": detects the continuous ~3 kHz pure tone characterised in README.md.

Algorithm (per frame of 100 ms, hop 50 ms):
  1. Hann-windowed FFT of the frame.
  2. Find the strongest bin inside the search band (default 2500-3500 Hz).
  3. Prominence = peak level - median level of the band (excluding +-60 Hz around the peak).
  4. Frame is "tone" if prominence >= PROM_DB and peak level >= MIN_LEVEL_DBFS.
  5. Frequency stability: the peak must stay within +-FREQ_TOL Hz of the running median
     over the last STABLE_FRAMES frames (a pure tone doesn't move; speech harmonics do).
  6. Hysteresis: ON after ON_FRAMES consecutive tone frames, OFF after OFF_FRAMES consecutive non-tone frames.

Usage:  python detect_bip.py file.wav [file2 ...]     (any format ffmpeg can read)
"""
import sys, subprocess, numpy as np

SR = 16000            # 16 kHz is enough (tone < 4 kHz incl. margin), cheap for an embedded sensor
FRAME = 0.100         # s
HOP = 0.050           # s
BAND = (2500, 3500)   # Hz, search band (covers 2942 Hz and 3151 Hz seen in the recordings)
PROM_DB = 15.0        # peak vs. band-median prominence
MIN_LEVEL_DBFS = -80  # ignore peaks below this (noise floor guard)
FREQ_TOL = 15.0       # Hz, max deviation of peak freq from running median
STABLE_FRAMES = 10    # 0.5 s window for the stability test
ON_FRAMES = 6         # 0.3 s of continuous tone to declare ON
OFF_FRAMES = 20       # 1.0 s without tone to declare OFF

def load(path):
    raw = subprocess.run(["ffmpeg","-v","error","-i",path,"-ac","1","-ar",str(SR),"-f","f32le","-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def detect(x, sr=SR):
    n_frame, n_hop = int(FRAME*sr), int(HOP*sr)
    w = np.hanning(n_frame); f = np.fft.rfftfreq(n_frame, 1/sr)
    band = (f >= BAND[0]) & (f <= BAND[1]); fb = f[band]
    n = (len(x)-n_frame)//n_hop + 1
    t = np.arange(n)*HOP
    peak_f = np.zeros(n); peak_db = np.zeros(n); prom = np.zeros(n)
    for i in range(n):
        S = np.abs(np.fft.rfft(x[i*n_hop:i*n_hop+n_frame]*w))*2/np.sum(w)
        Sb = 20*np.log10(S[band]+1e-12)
        k = np.argmax(Sb); peak_f[i] = fb[k]; peak_db[i] = Sb[k]
        others = Sb[np.abs(fb-fb[k]) > 60]
        prom[i] = Sb[k] - np.median(others)
    frame_ok = (prom >= PROM_DB) & (peak_db >= MIN_LEVEL_DBFS)
    # stability test
    stable = np.zeros(n, bool)
    for i in range(n):
        lo = max(0, i-STABLE_FRAMES+1); win = peak_f[lo:i+1][frame_ok[lo:i+1]]
        stable[i] = frame_ok[i] and len(win) >= min(STABLE_FRAMES, i+1)//2 and abs(peak_f[i]-np.median(win)) <= FREQ_TOL
    # hysteresis state machine
    state = np.zeros(n, bool); on = False; run_on = run_off = 0; events = []
    for i in range(n):
        if stable[i]: run_on += 1; run_off = 0
        else:         run_off += 1; run_on = 0
        if not on and run_on >= ON_FRAMES:
            on = True; events.append(["ON", t[i]-(ON_FRAMES-1)*HOP, None])
        elif on and run_off >= OFF_FRAMES:
            on = False; events[-1][2] = t[i]-(OFF_FRAMES-1)*HOP
        state[i] = on
    if events and events[-1][2] is None: events[-1][2] = t[-1]
    return t, peak_f, peak_db, prom, state, events

if __name__ == "__main__":
    for path in sys.argv[1:]:
        x = load(path); t, pf, pdb, pr, st, ev = detect(x)
        print(f"{path}: {len(x)/SR:.1f} s")
        for _, a, b in ev:
            m = st & (t >= a) & (t <= b)
            print(f"  BIP  {a:6.2f}s -> {b:6.2f}s  ({b-a:5.2f}s)  f = {np.median(pf[m]):.0f} Hz  level = {np.median(pdb[m]):.0f} dBFS  prominence = {np.median(pr[m]):.0f} dB")
        if not ev: print("  no bip")
