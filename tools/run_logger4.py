import subprocess, time, struct, os, sys, collections, ctypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
OUT=os.path.join(GAME,"krcodes.bin"); RING=1024
k32=ctypes.WinDLL("kernel32", use_last_error=True)
if os.path.exists(OUT): os.remove(OUT)
p=subprocess.Popen([os.path.join(GAME,"TOS.exe")], cwd=GAME); print("pid",p.pid)
h=k32.OpenProcess(0x410,False,p.pid)
def rd(a,n):
    b=(ctypes.c_char*n)(); c=ctypes.c_size_t(0)
    return b.raw if k32.ReadProcessMemory(h,ctypes.c_void_p(a),b,n,ctypes.byref(c)) else None
best=None
for t in range(20):
    time.sleep(4)
    if os.path.exists(OUT) and os.path.getsize(OUT)>=12+RING*20:
        d=open(OUT,"rb").read()
        i0,i1,i2=struct.unpack_from("<III",d,0)
        print("t=%ds idx=%s"%(4*(t+1),(i0,i1,i2)))
        if i2>0: best=d; break
if best is None and os.path.exists(OUT): best=open(OUT,"rb").read()
d=best
i0,i1,i2=struct.unpack_from("<III",d,0); off=12
conv=[struct.unpack_from("<II",d,off+8*k) for k in range(RING)]; off+=RING*8
gly=[struct.unpack_from("<II",d,off+8*k) for k in range(RING)]; off+=RING*8
ptrs=[struct.unpack_from("<I",d,off+4*k)[0] for k in range(RING)]
cc=collections.Counter(c for c,_ in conv if c)
print("CONV idx",i0,"distinct",len(cc),"top:",[(hex(k),v) for k,v in cc.most_common(25)])
print("  callers:",[(hex(k),v) for k,v in collections.Counter(b for _,b in conv if b).most_common(12)])
gc=collections.Counter(a for a,_ in gly if a)
print("GLYPH idx",i1,"distinct",len(gc),"top:",[(hex(k),v) for k,v in gc.most_common(15)])
print("TEXT idx",i2)
seen=set(); n=0
for pv in ptrs:
    if pv and pv not in seen:
        seen.add(pv); n+=1
        if n>30: break
        b=rd(pv,96)
        if b: print("  ptr 0x%08X: %s | %s"%(pv, b.hex(), ''.join(chr(x) if 32<=x<127 else '.' for x in b)))
p.terminate(); print("done")
