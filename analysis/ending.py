import numpy as np
for tag,(a,b) in [("bip",(12.0,18.0)),("video1",(25.5,28.0)),("video2",(20.5,23.0))]:
    t,L,R,P=np.load(f"analysis/{tag}_track.npy"); m=(t>=a)&(t<=b)
    print(f"== {tag} {a}-{b}s : t  tone  prominence")
    print(" ".join(f"{tt:.2f}:{ll:.0f}/{pp:.0f}" for tt,ll,pp in zip(t[m],L[m],P[m])))
# onset of bip and video (first 1.5s)
for tag in ("bip","video1","video2"):
    t,L,R,P=np.load(f"analysis/{tag}_track.npy"); m=t<=1.2
    print(f"== {tag} onset: "+" ".join(f"{tt:.2f}:{ll:.0f}" for tt,ll in zip(t[m],L[m])))
