import struct, os, zlib, hashlib, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
def parse_idx(path):
    d=open(path,"rb").read(); base=40+84385*8; recs={}
    for i in range((len(d)-base)//40):
        o=base+40*i
        fs,cs,off,hv=struct.unpack_from("<QQQI", d, o)
        ext=d[o+28:o+36].split(b"\x00")[0].decode("latin1")
        recs[hv]=dict(fs=fs,cs=cs,off=off,hv=hv,ext=ext)
    return recs
PATCH_TL=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
ORIG_TL=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
pi=parse_idx(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
oi=parse_idx(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
def get(tl,r):
    with open(tl,"rb") as f: f.seek(r["off"]); d=f.read(r["cs"])
    if r["cs"]==r["fs"]: return d
    return zlib.decompress(d[24:],-15) if d[:4]==b"TLZC" else None
p=get(PATCH_TL,pi[3085344091])
payload=p[4:]
print("patch entry len",len(p),"payload len",len(payload))
print("payload sha256", hashlib.sha256(payload).hexdigest())
k=open(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\korfnt\korfnt_0.dds","rb").read()
print("korfnt_0.dds len",len(k),"sha256",hashlib.sha256(k).hexdigest())
print("IDENTICAL" if payload==k else "DIFFERENT")
# DDS header parse of patch payload
if payload[:4]==b"DDS ":
    h=struct.unpack_from("<7I", payload, 4)
    flags,hgt,wid,pitch,depth,mips=struct.unpack_from("<6I", payload, 0x0c)
    print("DDS: flags=%08X h=%d w=%d mips=%d"%(flags,hgt,wid,mips))
    pf=payload[0x50:0x50+32]
    fourcc=pf[4:8]
    print("pixelformat fourcc:", fourcc)
# FontData.pac
pv=get(ORIG_TL,oi[1102414308])
print("\nFontData.pac len", len(pv) if pv else None)
if pv:
    print("  hex:", pv[:64].hex())
    print("  strings:", [s.decode('latin1') for s in re.findall(rb"[\x20-\x7e]{4,}", pv)])
