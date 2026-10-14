import os, subprocess, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KF=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf"
# reference header from original font page (768x576 DXT5 mips=3)
ref=open(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\FONTTYPEC_PIC015.dds","rb").read(128)
def dxt5_data(png, W, H):
    tmp=os.path.join(KF,"_t.dds")
    subprocess.run(["magick", png, "-resize","%dx%d!"%(W,H), "-define","dds:compression=dxt5", tmp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return open(tmp,"rb").read()[128:]
for i in range(12):
    n="%02d"%i
    png=os.path.join(KF,"page_%s.png"%n)
    d0=dxt5_data(png,768,576)
    d1=dxt5_data(png,384,288)
    d2=dxt5_data(png,192,144)
    out=ref+d0+d1+d2
    op=os.path.join(KF,"page_%s.dds"%n)
    open(op,"wb").write(out)
    print("page_%s.dds  mip0=%d mip1=%d mip2=%d total=%d"%(n,len(d0),len(d1),len(d2),len(out)))
