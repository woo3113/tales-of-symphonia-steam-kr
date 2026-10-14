import struct, os, zlib, collections, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PATCH_TL=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
def parse(h):
    d=open(h,"rb").read(); base=40+84385*8; recs=[]
    for i in range((len(d)-base)//40):
        o=base+40*i; fs,cs,off,hv=struct.unpack_from("<QQQI",d,o)
        recs.append(dict(i=i,fs=fs,cs=cs,off=off,hv=hv,ext=d[o+28:o+36].split(b"\x00")[0].decode('latin1')))
    return recs
pl=parse(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
ol=parse(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
om={r["hv"]:r for r in ol}
def get(r):
    with open(PATCH_TL,"rb") as f: f.seek(r["off"]); d=f.read(r["cs"])
    return d if r["cs"]==r["fs"] else (zlib.decompress(d[24:],-15) if d[:4]==b"TLZC" else None)
syl=collections.Counter()
def scan(b):
    t=b.decode("euc_kr","ignore")
    for ch in t:
        if 0xAC00<=ord(ch)<=0xD7A3: syl[ch]+=1
# all changed entries + all TXB
n=0
for r in pl:
    o=om.get(r["hv"])
    changed = o and o["fs"]!=r["fs"]
    if changed or r["ext"] in ("TXB","CSV"):
        b=get(r)
        if b: scan(b); n+=1
print("scanned %d entries"%n)
print("distinct Hangul syllables:", len(syl))
print("total Hangul chars:", sum(syl.values()))
print("top 40:", ''.join(c for c,_ in syl.most_common(40)))
# how many pages at 192 glyphs/page (16x12 cells)
print("pages needed (192/page):", (len(syl)+191)//192)
