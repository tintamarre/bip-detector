import subprocess, numpy as np
from scipy.signal import butter, sosfiltfilt, resample_poly
from scipy.ndimage import uniform_filter1d
SR=8000
def load(p):
    raw=subprocess.run(["ffmpeg","-v","error","-i",p,"-ac","1","-ar",str(SR),"-f","f32le","-"],capture_output=True,check=True).stdout
    return np.frombuffer(raw,dtype=np.float32).astype(float)
def env(x, hop=80):
    b=sosfiltfilt(butter(4,[300,2500],btype='band',fs=SR,output='sos'),x)
    n=len(b)//hop; e=np.log(np.array([np.sqrt(np.mean(b[i*hop:(i+1)*hop]**2)) for i in range(n)])+1e-6)
    e=e-uniform_filter1d(e,200)          # remove trends slower than 2 s
    return (e-e.mean())/e.std()
def best_corr(a,b):
    res=[]
    for lag in range(-len(a)+300, len(b)-300):
        lo=max(0,lag); hi=min(len(b),lag+len(a))
        if hi-lo<500: continue
        res.append((np.corrcoef(a[lo-lag:hi-lag],b[lo:hi])[0,1],lag*0.01))
    res.sort(reverse=True); return res[0], np.median([c for c,_ in res]), np.std([c for c,_ in res])
m=load("bip.mp3")[int(1.5*SR):-int(1.0*SR)]; r=3151.19/2942.08
variants={"native":m,"slowed":resample_poly(m,10711,10000),"sped":resample_poly(m,10000,10711)}
for vp in ["MicrosoftTeams-video.mp4","MicrosoftTeams-video (1).mp4"]:
    v=env(load(vp))
    for name,mm in variants.items():
        (c,lag),med,sd=best_corr(env(mm),v)
        print(f"{vp:30s} mp3 {name:7s}: best corr {c:.3f} at lag {lag:6.2f}s   (median over lags {med:.3f}, sd {sd:.3f}, z={(c-med)/sd:.1f})")
# print broadband envelopes at 0.5 s to eyeball events
for p in ["bip.mp3","MicrosoftTeams-video.mp4","MicrosoftTeams-video (1).mp4"]:
    x=load(p); b=sosfiltfilt(butter(4,[300,2500],btype='band',fs=SR,output='sos'),x); hop=SR//2
    e=[20*np.log10(np.sqrt(np.mean(b[i*hop:(i+1)*hop]**2))+1e-9) for i in range(len(b)//hop)]
    print(p, "300-2500 Hz level per 0.5 s:", " ".join(f"{v:.0f}" for v in e))
