import re, os, sys, zlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
xml = open(os.path.join(R,"FILEHEADER.TOFHDB.debug"),"rb").read().decode("shift_jis","replace")
entries=[]
for m in re.finditer(r"<File>\s*<FileSize>\s*(\d+)\s*</FileSize>\s*<CompressSize>\s*(\d+)\s*</CompressSize>\s*<Offset>\s*(\d+)\s*</Offset>\s*<HashValue>\s*(\d+)\s*</HashValue>\s*<Extension>\s*\"([^\"]*)\"\s*</Extension>", xml):
    fs,cs,off,hv,ext = m.groups()
    entries.append(dict(fs=int(fs),cs=int(cs),off=int(off),hv=int(hv),ext=ext))
def raw(off, cs):
    with open(os.path.join(R,"TLFILE.TLDAT"),"rb") as f:
        f.seek(off); return f.read(cs)
for ext in ["TLFNTB_D","PAK","TOSHDB"]:
    e = [x for x in entries if x["ext"]==ext][0]
    d = raw(e["off"], e["cs"])
    print("===",ext, e)
    for i in range(0,min(96,len(d)),16):
        print("  %06X  %s  %s" % (i, " ".join("%02x"%b for b in d[i:i+16]), "".join(chr(b) if 32<=b<127 else "." for b in d[i:i+16])))
    # try lz4 / lzo if available
    for mod in ["lz4.block","lzo"]:
        try:
            __import__(mod)
            print("  (module", mod, "available)")
        except Exception as ex:
            print("  (no", mod, ")")
