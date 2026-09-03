import sys, numpy as np
from scipy.io import wavfile
from scipy.signal import stft

path = sys.argv[1]
sr, x = wavfile.read(path)
x = x.astype(np.float64) / 32768.0
print(f"file={path} sr={sr} dur={len(x)/sr:.2f}s rms={20*np.log10(np.sqrt(np.mean(x**2))+1e-12):.1f} dBFS")

# Long-term average spectrum: first half vs last 3 s
def lta(seg):
    f, t, Z = stft(seg, fs=sr, nperseg=8192, noverlap=4096, window='hann')
    return f, 20*np.log10(np.mean(np.abs(Z), axis=1)+1e-12)

def top_peaks(f, S, n=12, fmin=100):
    m = f >= fmin
    fi, Si = f[m], S[m]
    idx = [i for i in range(1, len(Si)-1) if Si[i] > Si[i-1] and Si[i] >= Si[i+1]]
    idx = sorted(idx, key=lambda i: -Si[i])[:n]
    return sorted([(fi[i], Si[i]) for i in idx])

dur = len(x)/sr
for name, seg in [("first 3s", x[:3*sr]), ("mid", x[int(dur/2*sr)-int(1.5*sr):int(dur/2*sr)+int(1.5*sr)]), ("last 3s", x[-3*sr:])]:
    f, S = lta(seg)
    print(f"\n[{name}] top spectral peaks (Hz, dB):")
    for fr, s in top_peaks(f, S):
        print(f"  {fr:8.1f} Hz  {s:6.1f} dB")

# Time evolution: dominant peak per 100 ms frame in 500-6000 Hz
f, t, Z = stft(x, fs=sr, nperseg=4096, noverlap=4096-4800, window='hann')
A = np.abs(Z)
band = (f >= 300) & (f <= 8000)
print("\nDominant peak per 0.1 s (t, Hz, dB, peak-to-median ratio dB):")
for j in range(A.shape[1]):
    col = A[band, j]
    i = np.argmax(col)
    pk = 20*np.log10(col[i]+1e-12)
    med = 20*np.log10(np.median(col)+1e-12)
    print(f"  {t[j]:6.2f}s {f[band][i]:8.1f} Hz {pk:6.1f} dB  prominence {pk-med:5.1f} dB")
