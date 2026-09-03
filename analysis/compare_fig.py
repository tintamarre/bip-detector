import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.io import wavfile; from scipy.signal import stft
fig,ax=plt.subplots(3,1,figsize=(14,9))
for a,(tag,title) in zip(ax,[("bip","bip.mp3"),("video1","MicrosoftTeams-video.mp4"),("video2","MicrosoftTeams-video (1).mp4")]):
    sr,x=wavfile.read(f"analysis/{tag}_mono.wav"); x=x.astype(float)/32768
    f,t,Z=stft(x,fs=sr,nperseg=4096,noverlap=3072)
    a.pcolormesh(t,f,20*np.log10(np.abs(Z)+1e-9),vmin=-115,vmax=-45,shading='auto',cmap='magma'); a.set_ylim(2000,7000); a.set_ylabel("Hz"); a.set_title(title)
ax[-1].set_xlabel("s"); plt.tight_layout(); plt.savefig("analysis/compare_spectrograms.png",dpi=100)
