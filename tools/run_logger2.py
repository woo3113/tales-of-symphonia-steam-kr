import subprocess, time, struct, os, sys, collections, ctypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
OUT=os.path.join(GAME,"krcodes.bin")
RING=1024
k32=ctypes.WinDLL("kernel32", use_last_error=True)
if os.path.exists(OUT): os.remove(OUT)
p=subprocess.Popen([os.path.join(GAME,"TOS.exe")], cwd=GAME)
print("pid",p.pid)
h=k32.OpenProcess(0x410,False,p.pid)
def rd(a,n):
    b=(ctypes.c_char*n)(); c=ctypes.c_size_t(0)
    return b.raw if k32.ReadProcessMemory(h,ctypes.c_void_p(a),b,n,ctypes.byref(c)) else None
def dumpread():
    if not os.path.exists(OUT): return None
    d=open(OUT,"rb").read()
    if len(d)<4+RING*16: return None
    i0,i1=struct.unpack_from("<II",d,0)
    return d,i0,i1
for t in range(14):
    time.sleep(4)
    hook=rd(0x57A81C,5)
    r=dumpread()
    ex=ctypes.c_ulong(); k32.GetExitCodeProcess(h,ctypes.byref(ex))
    print("t=%2ds exit=%d hook@57A81C=%s idx=%s"%(4*(t+1), ex.value, hook.hex() if hook else None, (r[1],r[2]) if r else None))
    if ex.value!=259: break
r=dumpread()
if r:
    d,i0,i1=r; off=8
    conv=[struct.unpack_from("<II",d,off+8*k) for k in range(RING)]; off+=RING*8
    gly=[struct.unpack_from("<II",d,off+8*k) for k in range(RING)]
    def cat(c):
        x=c&0xFFFF
        if x<0x20: return "ctrl"
        if x<0x80: return "ascii"
        if 0x8140<=x<=0x9FFC: return "sjis"
        if 0xB0A1<=x<=0xC8FE: return "euckr"
        return "other"
    cc=collections.Counter(c for c,_ in conv if c)
    print("CONV idx",i0,"distinct",len(cc),"cats",collections.Counter(cat(c) for c in cc).most_common())
    print("  top:",[(hex(k),v) for k,v in cc.most_common(30)])
    print("  callers:",[(hex(k),v) for k,v in collections.Counter(b for _,b in conv if b).most_common(15)])
    gc=collections.Counter(a for a,_ in gly if a)
    print("GLYPH idx",i1,"distinct",len(gc),"top:",[(hex(k),v) for k,v in gc.most_common(20)])
    print("  ctx:",[(hex(k),v) for k,v in collections.Counter(b for _,b in gly if b).most_common(10)])
k32.CloseHandle(h); p.terminate(); print("done")
