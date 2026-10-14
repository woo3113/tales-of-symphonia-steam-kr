import pefile, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS); D=pe.__data__; IMG=0x400000
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData:
            return IMG+s.VirtualAddress+(o-s.PointerToRawData)
def refs(va, limit=12):
    tgt=va.to_bytes(4,'little')
    out=[]
    for i in range(len(D)-4):
        if D[i:i+4]==tgt:
            v=off2va(i)
            if v is not None and 0x401000<=v<0x705000:  # only .text code
                out.append(v)
    return out[:limit], len(out)
for label,va in [("ascii_map",0x8AD868),("width_tbl",0x8AD970),("width_tbl2",0x8ADA90),
                 ("kanji_tbl",0x7304EA),("str_TLFNTB",0x87CA7C),("str_TLCLRB",0x87CB08),
                 ("str_TLPICB",0x87CA38),("str_fontb0",0x877934),("str_FontData",0x87796C),
                 ("str_DPDF",0x5DF2B3),("glyphfunc_578680",0x578680),("conv_57A810",0x57A810),
                 ("widthfunc_57ACD0",0x57ACD0)]:
    h,c=refs(va)
    print("%-18s VA=%08X refs(%d)=%s"%(label,va,c,[hex(x) for x in h]))
