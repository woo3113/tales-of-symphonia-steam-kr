import struct, os, zlib, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ORIG_TL=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
PATCH_TL=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
def parse(header):
    d=open(header,"rb").read(); base=40+84385*8; recs=[]
    for i in range((len(d)-base)//40):
        o=base+40*i
        fs,cs,off,hv=struct.unpack_from("<QQQI", d, o)
        ext=d[o+28:o+36].split(b"\x00")[0].decode("latin1")
        recs.append(dict(i=i,fs=fs,cs=cs,off=off,hv=hv,ext=ext))
    return recs
ol=parse(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
pl=parse(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
om={r["hv"]:r for r in ol}; pm={r["hv"]:r for r in pl}
byidx_p={r["i"]:r for r in pl}
def get(tl,r):
    with open(tl,"rb") as f: f.seek(r["off"]); d=f.read(r["cs"])
    if r["cs"]==r["fs"]: return d
    return zlib.decompress(d[24:],-15) if d[:4]==b"TLZC" else None
def name_of_picture(idx):
    # descriptor is the entry just before the picture
    d=byidx_p.get(idx-1)
    if not d: return None
    b=get(PATCH_TL,d) if d["hv"] in pm else None
    if not b: return None
    m=re.search(rb"[\x20-\x7e]{4,}", b)
    return m.group().decode('latin1') if m else None
print("=== changed pictures (orig fs -> patch fs) with names ===")
for r in pl:
    o=om.get(r["hv"])
    if o and o["fs"]!=r["fs"] and r["ext"] in ("TOTEXP_P","BAK"):
        nm=name_of_picture(r["i"])
        print("  idx %5d hv %-12d %-8s fs %-9d -> %-9d (d=%+d) name=%s"%(r["i"],r["hv"],r["ext"],o["fs"],r["fs"],r["fs"]-o["fs"],nm))
print("\n=== all font-ish descriptor names (FONT/PAL/SYSTEM/TYPE) ===")
names={}
for r in pl:
    if r["ext"]=="TOTEXB_D":
        b=get(PATCH_TL,r)
        if b:
            m=re.search(rb"[\x20-\x7e]{4,}", b)
            if m:
                nm=m.group().decode('latin1')
                if re.search(r"(FONT|font|PAL_)", nm):
                    names.setdefault(nm, []).append(r["i"])
for nm in sorted(names):
    print("   %-40s idx=%s"%(nm, names[nm][:6]))
