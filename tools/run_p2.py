import subprocess, time, struct, os, sys, collections, ctypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
OUT=os.path.join(GAME,"krcodes.bin"); RING=4096
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
    if os.path.exists(OUT) and os.path.getsize(OUT)>=8+RING*8:
        d=open(OUT,"rb").read(); i0,ns=struct.unpack_from("<II",d,0)
        hx=rd(0x57A8DA,6); h2=rd(0x57A81C,6)
        print("t=%ds idx=%d sites=%d 57A8DA=%s 57A81C=%s"%(4*(t+1),i0,ns, hx.hex() if hx else None, h2.hex() if h2 else None))
        if i0>0: best=d; break
if best is None and os.path.exists(OUT): best=open(OUT,"rb").read()
d=best; i0,ns=struct.unpack_from("<II",d,0)
conv=[struct.unpack_from("<II",d,8+8*k) for k in range(RING)]
cc=collections.Counter(c for c,_ in conv if c)
print("CONV idx",i0,"sites patched",ns,"distinct",len(cc))
print("  2byte(>0xFF):", sum(v for k,v in cc.items() if k>0xFF), "distinct:", sum(1 for k in cc if k>0xFF))
print("  top:",[(hex(k),v) for k,v in cc.most_common(30)])
print("  callers:",[(hex(k),v) for k,v in collections.Counter(b for _,b in conv if b).most_common(12)])
p.terminate(); print("done")
