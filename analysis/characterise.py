import sys, numpy as np
from scipy.io import wavfile
from scipy.signal import stft, butter, sosfiltfilt
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

path = sys.argv[1]; tag = sys.argv[2]
sr, x = wavfile.read(path); x = x.astype(np.float64)/32768.0
dur = len(x)/sr

# 1) precise frequency: zero-padded FFT of a quiet section (0.5-7.5 s) if long enough
seg = x[int(0.5*sr):int(min(7.5,dur-0.5)*sr)]
N = 1<<20
W = np.abs(np.fft.rfft(seg*np.hanning(len(seg)), N)); F = np.fft.rfftfreq(N, 1/sr)
m = (F>2500)&(F<4000); i = np.argmax(W[m]); f0 = F[m][i]
# parabolic interpolation
j = np.where(m)[0][i]; a,b,c = np.log(W[j-1]),np.log(W[j]),np.log(W[j+1]); f0 += (0.5*(a-c)/(a-2*b+c))*(F[1]-F[0])
pk = W[j]
# -3 dB bandwidth
half = pk/np.sqrt(2); lo=j; hi=j
while W[lo]>half: lo-=1
while W[hi]>half: hi+=1
print(f"[{tag}] fundamental f0 = {f0:.2f} Hz, -3 dB bandwidth ~ {F[hi]-F[lo]:.2f} Hz (window-limited)")
for k in range(2,6):
    mk=(F>f0*k-30)&(F<f0*k+30); ik=np.argmax(W[mk]); print(f"   harmonic {k}: {F[mk][ik]:.1f} Hz  {20*np.log10(W[mk][ik]/pk):.1f} dB rel. f0")

# 2) narrow-band energy vs time (10 ms hops) around f0 vs neighbouring bands
def bandpass(lo,hi): return sosfiltfilt(butter(6,[lo,hi],btype='band',fs=sr,output='sos'),x)
tone = bandpass(f0-40, f0+40)
ctrl = bandpass(f0-400, f0-100) + bandpass(f0+100, f0+400)  # neighbours, excluding tone
hop=int(0.01*sr); n=len(x)//hop
def rms_db(sig): return np.array([20*np.log10(np.sqrt(np.mean(sig[i*hop:(i+1)*hop]**2))+1e-9) for i in range(n)])
t=np.arange(n)*hop/sr; T=rms_db(tone); C=rms_db(ctrl); tot=rms_db(x)
snr=T-C
np.save(f"analysis/{tag}_snr.npy", np.vstack([t,T,C,tot]))
print(f"   tone band level: median {np.median(T):.1f} dBFS, max {T.max():.1f}, min {T.min():.1f}")
present = snr>10
print(f"   frames with tone SNR>10 dB: {present.mean()*100:.1f}%")
# segments
edges=np.flatnonzero(np.diff(present.astype(int)))
segs=[]; start=0 if present[0] else None
for e in edges:
    if present[e+1]: start=e+1
    else:
        if start is not None: segs.append((start,e))
        start=None
if start is not None: segs.append((start,n-1))
segs=[(a,b) for a,b in segs if b-a>=5]
print(f"   present segments (>=50 ms): {len(segs)}")
for a,b in segs[:40]: print(f"     {t[a]:7.2f}s -> {t[b]:7.2f}s  ({(b-a)*0.01:.2f}s)")
if len(segs)>40: print("     ...")
if segs: print(f"   last tone frame: {t[segs[-1][1]]:.2f}s of {dur:.2f}s")

# amplitude modulation on tone envelope while present (0.5..min(7.5,dur))
env=np.abs(tone[int(0.5*sr):int(min(7.5,dur-0.5)*sr)])
from scipy.signal import find_peaks
e=env[::48]  # 1 kHz
E=np.abs(np.fft.rfft((e-e.mean())*np.hanning(len(e)))); Fe=np.fft.rfftfreq(len(e),1/1000)
mm=(Fe>0.5)&(Fe<200); ie=np.argmax(E[mm]); print(f"   strongest envelope modulation: {Fe[mm][ie]:.1f} Hz (rel. {20*np.log10(E[mm][ie]/E[0]+1e-12):.1f} dB vs DC) -> {'pulsed' if 20*np.log10(E[mm][ie]/E[0]+1e-12)>-20 else 'continuous'}")

# 3) plots
fig,ax=plt.subplots(3,1,figsize=(14,10),sharex=True)
f,tt,Z=stft(x,fs=sr,nperseg=2048,noverlap=1536); ax[0].pcolormesh(tt,f,20*np.log10(np.abs(Z)+1e-9),vmin=-120,vmax=-40,shading='auto',cmap='magma'); ax[0].set_ylim(0,8000); ax[0].set_ylabel("Hz"); ax[0].set_title(f"{tag}: spectrogram")
ax[0].axhline(f0,color='cyan',lw=0.5,ls='--')
ax[1].plot(t,T,label=f"tone band {f0:.0f}±40 Hz"); ax[1].plot(t,C,label="neighbour bands"); ax[1].plot(t,tot,label="total",alpha=0.5); ax[1].set_ylabel("dBFS"); ax[1].legend(); ax[1].grid()
ax[2].plot(t,snr); ax[2].axhline(10,color='r',ls='--'); ax[2].set_ylabel("tone SNR (dB)"); ax[2].set_xlabel("s"); ax[2].grid()
plt.tight_layout(); plt.savefig(f"analysis/{tag}_profile.png",dpi=110)
