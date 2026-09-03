import subprocess, numpy as np
def load(p):
    raw=subprocess.run(["ffmpeg","-v","error","-i",p,"-ac","1","-ar","8000","-f","f32le","-"],capture_output=True,check=True).stdout
    return np.frombuffer(raw,dtype=np.float32).astype(float)
r=3151.19/2942.0
for p in ["bip.mp3","MicrosoftTeams-video.mp4","MicrosoftTeams-video (1).mp4"]:
    x=load(p); N=1<<21; W=np.abs(np.fft.rfft(x*np.hanning(len(x)),N)); F=np.fft.rfftfreq(N,1/8000)
    def line(f):  # peak within +-0.5 Hz vs median of +-2..6 Hz ring
        c=(F>f-0.5)&(F<f+0.5); ring=((F>f-6)&(F<f-2))|((F>f+2)&(F<f+6))
        return 20*np.log10(W[c].max()/np.median(W[ring]))
    print(p)
    print("   native 50 Hz family : "+"  ".join(f"{f:6.1f}Hz:{line(f):5.1f}dB" for f in (50,100,150,200,250,300)))
    print("   shifted x%.4f    : "%r+"  ".join(f"{f*r:6.1f}Hz:{line(f*r):5.1f}dB" for f in (50,100,150,200,250,300)))
    print("   native 60 Hz family : "+"  ".join(f"{f:6.1f}Hz:{line(f):5.1f}dB" for f in (60,120,180,240)))
