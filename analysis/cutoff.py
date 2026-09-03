import subprocess, numpy as np
def load(p,sr):
    raw=subprocess.run(["ffmpeg","-v","error","-i",p,"-ac","1","-ar",str(sr),"-f","f32le","-"],capture_output=True,check=True).stdout
    return np.frombuffer(raw,dtype=np.float32).astype(float)
for p,sr in [("bip.mp3",48000),("MicrosoftTeams-video.mp4",44100),("MicrosoftTeams-video (1).mp4",44100)]:
    x=load(p,sr); N=8192; W=[]
    for i in range(0,len(x)-N,N//2): W.append(np.abs(np.fft.rfft(x[i:i+N]*np.hanning(N)))**2)
    S=10*np.log10(np.mean(W,axis=0)+1e-20); F=np.fft.rfftfreq(N,1/sr)
    print(p, "band level (dB) per kHz from 10 kHz:", " ".join(f"{k}k:{S[(F>=k*1000)&(F<(k+1)*1000)].mean():.0f}" for k in range(10,int(sr/2000))))
