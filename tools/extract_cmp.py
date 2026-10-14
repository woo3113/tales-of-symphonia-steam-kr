import struct, sys, os, zlib, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def parse_idx(path):
    d=open(path,"rb").read(); base=40+84385*8
    recs={}
    for i in range((len(d)-base)//40):
        o=base+40*i
        fs,cs,off,hv=struct.unpack_from("<QQQI", d, o)
        ext=d[o+28:o+36].split(b"\x00")[0].decode("latin1")
        recs[hv]=dict(fs=fs,cs=cs,off=off,hv=hv,ext=ext)
    return recs

ORIG_TL=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
PATCH_TL=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
oi=parse_idx(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
pi=parse_idx(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")

def get(tl, rec):
    with open(tl,"rb") as f:
        f.seek(rec["off"]); d=f.read(rec["cs"])
    if rec["cs"]==rec["fs"]: return d
    if d[:4]==b"TLZC": return zlib.decompress(d[24:], -15)
    return None

# 1) TXB
h=2662614099
ot,pt=get(ORIG_TL,oi[h]),get(PATCH_TL,pi[h])
print("TXB orig",len(ot),"patch",len(pt))
open("TXB_orig.bin","wb").write(ot); open("TXB_patch.bin","wb").write(pt)
print("TXB orig head:", ot[:32].hex(), " patch head:", pt[:32].hex())
# NBXT count field at 0x64 in orig
for name,d in [("orig",ot),("patch",pt)]:
    i=d.find(b"NBXT"); cnt=struct.unpack_from("<I",d,i+4)[0]
    print("  %s NBXT-relative@%X count=%d"%(name,i,cnt))

# 2) TOTEXP_P big
h=3085344091
pt2=get(PATCH_TL,pi[h])
ot2=get(ORIG_TL,oi[h]) if h in oi else None
print("\nTOTEXP_P orig",len(ot2) if ot2 else None,"patch",len(pt2))
if ot2: open("TEXP_orig.bin","wb").write(ot2)
open("TEXP_patch.bin","wb").write(pt2)
for name,d in [("orig",ot2),("patch",pt2)]:
    if not d: continue
    print("  %s head: %s"%(name, ''.join(chr(b) if 32<=b<127 else '.' for b in d[:64])))
    print("  %s hex : %s"%(name, d[:32].hex()))
    for m in re.finditer(rb"[\x20-\x7e]{4,}", d[:600]):
        print("    str:", m.group().decode())

# 3) one changed BIN, one changed SKP
chg=[]
for hv in set(oi)&set(pi):
    if oi[hv]["fs"]!=pi[hv]["fs"] and oi[hv]["ext"] in ("BIN","SKP"):
        chg.append((oi[hv]["ext"],hv))
chg.sort()
print("\nchanged BIN/SKP sample:", chg[:5])
for ext,hv in chg[:2]:
    o=get(ORIG_TL,oi[hv]); p=get(PATCH_TL,pi[hv])
    print("--- %s hv=%d orig %d -> patch %d"%(ext,hv,len(o),len(p)))
    print("   orig head:", ''.join(chr(b) if 32<=b<127 else '.' for b in o[:120]))
    print("   patch head:", ''.join(chr(b) if 32<=b<127 else '.' for b in p[:120]))
