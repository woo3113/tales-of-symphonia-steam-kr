import re, os, zlib, struct

xml = open(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB.debug","rb").read().decode("shift_jis","replace")
hashes = set(int(x) for x in re.findall(r"<HashValue>\s*(\d+)\s*</HashValue>", xml))
print("num hashvalues", len(hashes))

def crc32(b): return zlib.crc32(b) & 0xffffffff
def crc32b(b): return zlib.crc32(b) & 0xffffffff
def fnv1a(b):
    h=0x811c9dc5
    for c in b: h=((h^c)*0x01000193)&0xffffffff
    return h
def fnv1(b):
    h=0x811c9dc5
    for c in b: h=((h*0x01000193)^c)&0xffffffff
    return h
def djb2(b):
    h=5381
    for c in b: h=((h*33)+c)&0xffffffff
    return h
def sdbm(b):
    h=0
    for c in b: h=(c+(h<<6)+(h<<16)-h)&0xffffffff
    return h
def djb2x(b):
    h=5381
    for c in b: h=((h*33)^c)&0xffffffff
    return h

funcs = {"crc32":crc32,"fnv1a":fnv1a,"fnv1":fnv1,"djb2":djb2,"sdbm":sdbm,"djb2x":djb2x}

names = ["fontb0.dat","fontb1.dat","gage_fontb0.dat","gage_fontb1.dat","pop_fontb0.dat","pop_fontb1.dat",
         "yug_fontb0.dat","FontData.pac","PAL_FONTB0.TOTEXB_D","PAL_FONTB1.TOTEXB_D","FONTB0.DAT","FONTB1.DAT",
         "PAL_FONTB0.TOTEXB","us_fontb0.dat","fontb0","font.dat","FONT.DAT"]
def variants(n):
    out=set()
    for s in [n, n.lower(), n.upper(), n.replace("/","\\"), "data\\"+n, "Data\\"+n]:
        out.add(s)
    return out

found=[]
for n in names:
    for v in variants(n):
        for fn,f in funcs.items():
            for b in [v.encode("ascii","ignore"), v.encode("shift_jis","ignore")]:
                h=f(b)
                if h in hashes:
                    found.append((n,v,fn,h))
for x in found: print("MATCH", x)
print("total matches", len(found))
