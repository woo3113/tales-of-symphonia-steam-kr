import struct, os, zlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ORIG_TL=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
OUT=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
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
for hv,name in [(3085344091,"PAL_FONTB0"),(1450979254,"FONTTYPEC_PIC015"),(2703834565,"SYSTEM_PIC000"),(356323291,"TOTEXP_10884")]:
    r=[x for x in o if x["hv"]==hv][0]
    d=get(r)
    dd=d[4:] if d[:4]!=b"DDS " else d
    fn=os.path.join(OUT, name+".dds")
    open(fn,"wb").write(dd)
    if dd[:4]==b"DDS ":
        h,w=struct.unpack_from("<II",dd,0x0C); fourcc=dd[0x58:0x5C]; mips=struct.unpack_from("<I",dd,0x1C)[0]
        print("%-16s idx=%d hv=%d  DDS %dx%d mips=%d fourcc=%r bytes=%d"%(name,r["i"],hv,w,h,mips,fourcc,len(dd)))
