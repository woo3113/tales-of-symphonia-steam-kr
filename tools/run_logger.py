import subprocess, time, struct, os, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
OUT=os.path.join(GAME,"krcodes.bin")
RING=1024
if os.path.exists(OUT): os.remove(OUT)
p=subprocess.Popen([os.path.join(GAME,"TOS.exe")], cwd=GAME)
print("pid",p.pid)
for t in range(10):
    time.sleep(3)
    if os.path.exists(OUT) and os.path.getsize(OUT)>=8+RING*16:
        print("krcodes.bin ready at t=%ds size=%d"%(3*(t+1), os.path.getsize(OUT))); break
data=open(OUT,"rb").read() if os.path.exists(OUT) else b""
print("file size", len(data))
if len(data)>=4+RING*16:
    i0,i1=struct.unpack_from("<II",data,0)
    off=8
    conv=[struct.unpack_from("<II",data,off+8*k) for k in range(RING)]
    off+=RING*8
    gly=[struct.unpack_from("<II",data,off+8*k) for k in range(RING)]
    print("conv idx",i0,"glyph idx",i1)
    cc=collections.Counter(c for c,_ in conv if c)
    gc=collections.Counter(a for a,_ in gly)
    cctx=collections.Counter(b for _,b in gly)
    def cat(c):
        x=c&0xFFFF
        if x<0x20: return "ctrl"
        if x<0x80: return "ascii"
        if 0x8140<=x<=0x9FFC: return "sjis"
        if 0xB0A1<=x<=0xC8FE: return "euckr"
        return "other"
    print("CONVERTER distinct codes",len(cc),"cats",collections.Counter(cat(c) for c in cc).most_common())
    print("  top codes:",[(hex(k),v) for k,v in cc.most_common(25)])
    print("  top callers:",[(hex(k),v) for k,v in collections.Counter(b for _,b in conv).most_common(12)])
    print("GLYPH distinct codes",len(gc),"top:",[(hex(k),v) for k,v in gc.most_common(20)])
    print("  font contexts (ecx):",[(hex(k),v) for k,v in cctx.most_common(10)])
else:
    print("no data")
p.terminate(); print("done")
