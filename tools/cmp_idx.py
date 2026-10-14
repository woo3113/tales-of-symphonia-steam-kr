import struct, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from collections import Counter, defaultdict

def parse(path):
    d=open(path,"rb").read()
    n=len(d)
    HDR=40; FH=84385*8
    base=HDR+FH
    nrec=(n-base)//40
    recs=[]
    for i in range(nrec):
        o=base+40*i
        fs,cs,off,hv = struct.unpack_from("<QQQI", d, o)
        ext=d[o+28:o+36].split(b"\x00")[0].decode("latin1")
        flags=struct.unpack_from("<I", d, o+36)[0]
        recs.append(dict(i=i,fs=fs,cs=cs,off=off,hv=hv,ext=ext,flags=flags))
    return recs

orig=parse(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
patch=parse(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
print("orig recs", len(orig), "patch recs", len(patch))
om={r["hv"]:r for r in orig}
pm={r["hv"]:r for r in patch}
print("orig unique hv", len(om), "patch unique hv", len(pm))
only_o=set(om)-set(pm); only_p=set(pm)-set(om)
print("only orig", len(only_o), "only patch", len(only_p))
if only_o: print("  only-orig exts", Counter(om[h]["ext"] for h in only_o).most_common(10))
if only_p: print("  only-patch exts", Counter(pm[h]["ext"] for h in only_p).most_common(10))

fs_changed=[]; cs_only=[]
for h in set(om)&set(pm):
    a,b=om[h],pm[h]
    if a["fs"]!=b["fs"]:
        fs_changed.append((h,a,b))
    elif a["cs"]!=b["cs"]:
        cs_only.append((h,a,b))
print("same hash, FileSize changed (content changed):", len(fs_changed))
print("  by ext:", Counter(a["ext"] for _,a,_ in fs_changed).most_common(30))
print("same hash, only CompressSize changed (recompressed):", len(cs_only))
print("  by ext:", Counter(a["ext"] for _,a,_ in cs_only).most_common(15))
print()
print("=== entries whose uncompressed size changed (top 40 by delta) ===")
fs_changed.sort(key=lambda t: -(abs(t[2]["fs"]-t[1]["fs"])))
for h,a,b in fs_changed[:40]:
    print("  %-10s hv=%-12d fs %d -> %d (d=%+d)  off %d -> %d" % (a["ext"],h,a["fs"],b["fs"],b["fs"]-a["fs"],a["off"],b["off"]))
