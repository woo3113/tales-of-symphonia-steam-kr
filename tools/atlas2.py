import struct, os, zlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ORIG_TL=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
def parse_list(path):
    d=open(path,"rb").read(); base=40+84385*8; recs=[]
    for i in range((len(d)-base)//40):
        o=base+40*i
        fs,cs,off,hv=struct.unpack_from("<QQQI", d, o)
        ext=d[o+28:o+36].split(b"\x00")[0].decode("latin1")
        recs.append(dict(i=i,fs=fs,cs=cs,off=off,hv=hv,ext=ext))
    return recs
o=parse_list(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
def get(rec):
    with open(ORIG_TL,"rb") as f: f.seek(rec["off"]); d=f.read(rec["cs"])
    if rec["cs"]==rec["fs"]: return d
    return zlib.decompress(d[24:],-15) if d[:4]==b"TLZC" else None
print("=== entries idx 83330..83400 ===")
for r in o:
    if 83330<=r["i"]<=83400:
        print("  idx %5d ext %-9s hv %-12d fs %-9d cs %-9d"%(r["i"],r["ext"],r["hv"],r["fs"],r["cs"]))
print("\n=== TOTEXB_D descriptors near atlas (idx 83356..83370) ===")
for r in o:
    if 83350<=r["i"]<=83372 and r["ext"]=="TOTEXB_D":
        d=get(r)
        print("  idx %d hv=%d fs=%d : %s"%(r["i"],r["hv"],r["fs"], d.hex() if d else None))
print("\n=== original atlas texture (hv=3085344091) ===")
r=[x for x in o if x["hv"]==3085344091][0]
d=get(r)
print("  entry len",len(d),"prefix",d[:4].hex())
dd=d[4:] if d[:4]!=b"DDS " else d
if dd[:4]==b"DDS ":
    h,w=struct.unpack_from("<II",dd,0x0C)
    fourcc=dd[0x58:0x5C]
    mips=struct.unpack_from("<I",dd,0x1C)[0]
    print("  DDS h=%d w=%d mips=%d fourcc=%s size=%d"%(h,w,mips,fourcc,len(dd)))
