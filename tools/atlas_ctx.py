import struct, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from collections import Counter
def parse_list(path):
    d=open(path,"rb").read(); base=40+84385*8; recs=[]
    for i in range((len(d)-base)//40):
        o=base+40*i
        fs,cs,off,hv=struct.unpack_from("<QQQI", d, o)
        ext=d[o+28:o+36].split(b"\x00")[0].decode("latin1")
        recs.append(dict(i=i,fs=fs,cs=cs,off=off,hv=hv,ext=ext))
    return recs
orig=parse_list(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
patch=parse_list(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
om={r["hv"]:r for r in orig}; pm={r["hv"]:r for r in patch}
# neighbors of the atlas entry
idx=pm[3085344091]["i"]
print("atlas entry index", idx, "ext", pm[3085344091]["ext"], "off", pm[3085344091]["off"])
for j in range(idx-6, idx+7):
    r=pm[list(pm)[0]] if False else next((x for x in patch if x["i"]==j), None)
    if not r: continue
    o=om.get(r["hv"])
    print("  idx %5d ext %-9s hv %-12d fs %-10d cs %-10d  origfs=%s" % (j, r["ext"], r["hv"], r["fs"], r["cs"], (o["fs"] if o else "-")))
# all changed TOTEXP_P
print("\nchanged TOTEXP_P (size changed):")
for r in patch:
    o=om.get(r["hv"])
    if r["ext"]=="TOTEXP_P" and o and o["fs"]!=r["fs"]:
        print("   hv=%-12d fs %-9d -> %-9d (d=%+d)" % (r["hv"], o["fs"], r["fs"], r["fs"]-o["fs"]))
# count changed by ext precisely
ch=Counter()
for r in patch:
    o=om.get(r["hv"])
    if o and o["fs"]!=r["fs"]: ch[r["ext"]]+=1
print("\nall changed ext:", ch.most_common())
