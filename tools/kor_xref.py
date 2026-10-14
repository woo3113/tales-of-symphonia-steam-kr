import pefile, capstone, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOR=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\korfnt\korfnt.dll"
pe=pefile.PE(KOR); D=pe.__data__; IMG=pe.OPTIONAL_HEADER.ImageBase
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData:
            return IMG+s.VirtualAddress+(o-s.PointerToRawData)
def refs(va,limit=12):
    t=struct.pack("<I", va); out=[]
    for i in range(len(D)-4):
        if D[i:i+4]==t:
            v=off2va(i)
            if v is not None and IMG+0x1000<=v<IMG+0x2D000: out.append(v)
    return out[:limit]
# pattern string VAs (file offsets from aob.py)
pat_offs=[0x343A8,0x34404,0x34488,0x344C8,0x3450C,0x34560,0x34570,0x345A4,0x345CC,0x345F8]
print("=== xrefs to AOB pattern strings ===")
for po in pat_offs:
    va=off2va(po)
    print("  pattern@%06X VA=0x%X  xrefs=%s"%(po,va,[hex(x) for x in refs(va)]))
# also xrefs to my_ASMHook strings
for po in [0x343E8,0x34448,0x34468,0x344AC,0x344F4,0x34548]:
    va=off2va(po)
    print("  str@%06X VA=0x%X xrefs=%s"%(po,va,[hex(x) for x in refs(va)]))
