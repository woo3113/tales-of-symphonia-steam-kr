import subprocess, time, struct, os, sys, collections, ctypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
OUT=os.path.join(GAME,"krcodes.bin"); RING=1024
k32=ctypes.WinDLL("kernel32", use_last_error=True)
if os.path.exists(OUT): os.remove(OUT)
p=subprocess.Popen([os.path.join(GAME,"TOS.exe")], cwd=GAME); print("pid",p.pid)
h=k32.OpenProcess(0x410,False,p.pid)
best=None
for t in range(20):
    time.sleep(4)
    if os.path.exists(OUT) and os.path.getsize(OUT)>=8+RING*16:
        d=open(OUT,"rb").read(); i0,i1=struct.unpack_from("<II",d,0)
        print("t=%ds idx=%s"%(4*(t+1),(i0,i1)))
        if i0>0 or i1>0: best=d; break
if best is None and os.path.exists(OUT): best=open(OUT,"rb").read()
d=best; i0,i1=struct.unpack_from("<II",d,0); off=8
conv=[struct.unpack_from("<II",d,off+8*k) for k in range(RING)]; off+=RING*8
gly=[struct.unpack_from("<II",d,off+8*k) for k in range(RING)]
cc=collections.Counter(c for c,_ in conv if c)
print("CONV idx",i0,"distinct",len(cc))
print("  top:",[(hex(k),v) for k,v in cc.most_common(30)])
print("  2byte(>0xFF) count:", sum(v for k,v in cc.items() if k>0xFF), " distinct:", sum(1 for k in cc if k>0xFF))
print("  callers:",[(hex(k),v) for k,v in collections.Counter(b for _,b in conv if b).most_common(12)])
gc=collections.Counter(a for a,_ in gly if a)
print("GLYPH idx",i1,"distinct",len(gc),"top:",[(hex(k),v) for k,v in gc.most_common(20)])
p.terminate(); print("done")
