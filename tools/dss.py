import pefile, math, re, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS)
def ent(b):
    if not b: return 0
    c=Counter(b); n=len(b)
    return -sum((v/n)*math.log2(v/n) for v in c.values())
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin1')
    d=s.get_data()
    print("%-10s VS=%08X ent=%.2f"%(nm, s.Misc_VirtualSize, ent(d[:400000])))
# .dsstext head
s=[x for x in pe.sections if x.Name.startswith(b".dsstext")][0]
o=s.PointerToRawData
print(".dsstext head ascii:", ''.join(chr(b) if 32<=b<127 else '.' for b in pe.__data__[o:o+160]))
print(".dsstext head hex  :", pe.__data__[o:o+48].hex())
# is .dsstext referenced by .text code? check for a couple of immediate refs
seg=pe.__data__[o:o+200000]
print("strings in first 200KB of .dsstext:", [m.group().decode('latin1') for m in re.finditer(rb"[\x20-\x7e]{6,}", seg)][:20])
