import sys, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt, hilbert

for tag, f0 in [("bip",3151.19),("video1",2942.08),("video2",2941.46)]:
    sr,x = wavfile.read(f"analysis/{tag}_mono.wav"); x=x.astype(np.float64)/32768.0; dur=len(x)/sr
    print(f"===== {tag}  f0={f0:.2f} Hz  dur={dur:.2f}s")
    # --- Goertzel-style narrow-band tracking: 200 ms windows, 50 ms hop
    win=int(0.2*sr); hop=int(0.05*sr); n=(len(x)-win)//hop
    t=np.arange(n)*hop/sr; w=np.hanning(win); k=np.arange(win)
    osc=np.exp(-2j*np.pi*f0*k/sr)
    def lvl(sig,off):
        oscx=np.exp(-2j*np.pi*(f0+off)*k/sr)
        return np.array([20*np.log10(abs(np.sum(sig[i*hop:i*hop+win]*w*oscx))*2/np.sum(w)+1e-12) for i in range(n)])
    L=lvl(x,0)
    # neighbour reference: median of bins at +-60,+-120,+-180,+-240 Hz
    R=np.median(np.vstack([lvl(x,o) for o in (-240,-180,-120,-60,60,120,180,240)]),axis=0)
    P=L-R
    np.save(f"analysis/{tag}_track.npy",np.vstack([t,L,R,P]))
    print("  time   tone(dBFS) neighbours(dBFS) prominence(dB)")
    for i in range(0,n,10): print(f"  {t[i]:6.2f} {L[i]:8.1f} {R[i]:8.1f} {P[i]:8.1f}")
    on = (P>12)&(L>-75)
    last=t[np.flatnonzero(on)[-1]] if on.any() else None
    print(f"  tone stable level while on: median {np.median(L[on]):.1f} dBFS  (min {L[on].min():.1f}, max {L[on].max():.1f})")
    print(f"  LAST detection (prominence>12 dB): {last:.2f}s ; after that, tone-bin level median {np.median(L[t>last+0.3]):.1f} dBFS, max {L[t>last+0.3].max():.1f}, prominence max {P[t>last+0.3].max():.1f} dB")
    # --- sidebands: fine FFT around f0 over clean section
    a,b=(0.5,7.5) if tag=="bip" else (9.5,20.0)
    seg=x[int(a*sr):int(b*sr)]; N=1<<20
    W=np.abs(np.fft.rfft(seg*np.hanning(len(seg)),N)); F=np.fft.rfftfreq(N,1/sr)
    m=(F>f0-400)&(F<f0+400); ref=W[m].max(); Wd=20*np.log10(W[m]/ref+1e-12); Fm=F[m]
    pk=[i for i in range(2,len(Wd)-2) if Wd[i]>Wd[i-1] and Wd[i]>=Wd[i+1] and Wd[i]>-35 and Wd[i]>=Wd[i-2] and Wd[i]>=Wd[i+2]]
    # cluster to 2 Hz
    out=[];
    for i in pk:
        if out and abs(Fm[i]-out[-1][0])<2: 
            if Wd[i]>out[-1][1]: out[-1]=(Fm[i],Wd[i])
        else: out.append((Fm[i],Wd[i]))
    print(f"  spectral lines within +-400 Hz of f0 (> -35 dB rel. carrier), analysed {a}-{b}s:")
    for fr,d in out: print(f"     {fr:8.1f} Hz  ({fr-f0:+7.1f})  {d:6.1f} dB")
    # --- modulation depth from envelope of narrow band-pass
    bp=sosfiltfilt(butter(4,[f0-300,f0+300],btype='band',fs=sr,output='sos'),seg)
    env=np.abs(hilbert(bp)); 
    print(f"  envelope (band f0+-300 Hz): mean {env.mean():.5f}, p5 {np.percentile(env,5):.5f}, p95 {np.percentile(env,95):.5f} -> AM depth (p95-p5)/(p95+p5) = {(np.percentile(env,95)-np.percentile(env,5))/(np.percentile(env,95)+np.percentile(env,5))*100:.0f}%")
    e=env[::48]; E=np.abs(np.fft.rfft((e-e.mean())*np.hanning(len(e)))); Fe=np.fft.rfftfreq(len(e),1/1000)
    mm=(Fe>2)&(Fe<300); top=np.argsort(E[mm])[-4:][::-1]
    print("  envelope spectrum top lines (Hz, modulation index approx):", ", ".join(f"{Fe[mm][i]:.1f} Hz ({2*E[mm][i]/np.sum(np.hanning(len(e)))/e.mean()*100:.0f}%)" for i in top))
