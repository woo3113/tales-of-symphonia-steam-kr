import pefile, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS); D=pe.__data__; IMG=0x400000
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData:
            return IMG+s.VirtualAddress+(o-s.PointerToRawData)
def callers(target, limit=40):
    out=[]
    for o in range(len(D)-5):
        if D[o]==0xE8:
            rel=struct.unpack_from("<i", D, o+1)[0]
            tgt=(off2va(o))+5+rel
            if tgt==target:
                out.append(off2va(o))
    return out
for name,t in [("glyph 0x578680",0x578680),("width 0x57ACD0",0x57ACD0),("conv 0x57A810",0x57A810),
               ("fontbank_ctor 0x614120",0x614120),("fontbank_get 0x614210",0x614210),
               ("fontload 0x6120C0",0x6120C0),("maintext 0x57A880",0x57A880)]:
    c=callers(t)
    print("%-22s callers(%d): %s"%(name,len(c),[hex(x) for x in c[:20]]))
