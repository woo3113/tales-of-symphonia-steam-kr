import pefile, sys, re, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS); D=pe.__data__; IMG=0x400000
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData:
            return IMG+s.VirtualAddress+(o-s.PointerToRawData)
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)

for magic in ["DPDF","TOTEXB","TLFNT","TLFNTB","TOANMB","TLCLR","TLPIC"]:
    b=magic.encode(); offs=[m.start() for m in re.finditer(re.escape(b), D)][:6]
    print("%-8s count=%d at %s"%(magic, len(re.findall(re.escape(b),D)), [hex(off2va(o)) for o in offs]))
# xrefs (imm32) to the ASCII table 0x8AD868 and to width tables
for label,va in [("ascii_map 0x8AD868",0x8AD868),("width_tbl 0x8AD970",0x8AD970),("width_tbl2 0x8ADA90",0x8ADA90),("kanji_tbl 0x7304EA",0x7304EA)]:
    tgt=(IMG+va).to_bytes(4,'little')
    hits=[off2va(i) for i in range(len(D)-4) if D[i:i+4]==tgt]
    print("%-22s xrefs=%s"%(label,[hex(h) for h in hits[:8]]))
