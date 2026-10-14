import struct, os, zlib, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
def parse_idx(path):
    d=open(path,"rb").read(); base=40+84385*8; recs={}
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
def get(tl,r):
    with open(tl,"rb") as f: f.seek(r["off"]); d=f.read(r["cs"])
    if r["cs"]==r["fs"]: return d
    return zlib.decompress(d[24:],-15) if d[:4]==b"TLZC" else None

def hangul_count(d):
    # UTF-16LE syllables
    n16=sum(1 for i in range(0,len(d)-1,2) if 0xAC00<=struct.unpack_from("<H",d,i)[0]<=0xD7A3)
    # UTF-8 EA-ED xx xx
    n8=len(re.findall(rb"[\xea-\xed][\x80-\xbf][\x80-\xbf]", d))
    # CP949 lead 0xB0-0xC8 (Hangul syllables area) followed by trail 0xA1-0xFE
    n949=len(re.findall(rb"[\xb0-\xc8][\xa1-\xfe]", d))
    return n16,n8,n949

def samples16(d, k=5):
    out=[]
    m=re.finditer(rb"(?:[\x00-\xff][\xac-\xd7])", d)
    return out

for label,hv in [("TXB",2662614099)]:
    o=get(ORIG_TL,oi[hv]); p=get(PATCH_TL,pi[hv])
    print("== %s orig hangul(16,8,949)=%s patch=%s"%(label,hangul_count(o),hangul_count(p)))
    # dump the string area: find first region where they differ
    i=0; n=min(len(o),len(p))
    while i<n and o[i]==p[i]: i+=1
    print("  first diff at", hex(i))
    seg=p[max(0,i-8):i+120]
    print("  patch around diff (hex):", seg.hex())
    print("  patch around diff (sjis):", seg.decode('shift_jis','replace')[:80])
    print("  patch around diff (euckr):", seg.decode('euc_kr','replace')[:80])

# changed BIN
for hv in [5441981, 13605420, 603878069]:
    o=get(ORIG_TL,oi[hv]); p=get(PATCH_TL,pi[hv])
    print("\n== BIN hv=%d orig=%d patch=%d hangul orig=%s patch=%s"%(hv,len(o),len(p),hangul_count(o),hangul_count(p)))
    i=0; n=min(len(o),len(p))
    while i<n and o[i]==p[i]: i+=1
    print("  first diff at",hex(i))
    print("  orig :",o[max(0,i-16):i+96].hex())
    print("  patch:",p[max(0,i-16):i+96].hex())
    print("  patch sjis:",p[max(0,i-16):i+96].decode('shift_jis','replace')[:80])
    print("  patch euckr:",p[max(0,i-16):i+96].decode('euc_kr','replace')[:80])
