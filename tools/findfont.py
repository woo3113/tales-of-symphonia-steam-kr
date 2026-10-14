import re, os, sys, zlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
xml = open(os.path.join(R,"FILEHEADER.TOFHDB.debug"),"rb").read().decode("shift_jis","replace")
entries=[]
for m in re.finditer(r"<File>\s*<FileSize>\s*(\d+)\s*</FileSize>\s*<CompressSize>\s*(\d+)\s*</CompressSize>\s*<Offset>\s*(\d+)\s*</Offset>\s*<HashValue>\s*(\d+)\s*</HashValue>\s*<Extension>\s*\"([^\"]*)\"\s*</Extension>", xml):
    fs,cs,off,hv,ext = m.groups()
    entries.append(dict(fs=int(fs),cs=int(cs),off=int(off),hv=int(hv),ext=ext))
needles = [b"TL_FONT", b"FONTB", b"fontb", b"TLFNTB", b"FONTDATA"]
f = open(os.path.join(R,"TLFILE.TLDAT"),"rb")
hits=0
for e in entries:
    if e["fs"] > 4_000_000 or e["fs"] < 512: continue
    if e["ext"] not in ("PAC","TLFNTB_D","TOTEXB_D","BIN","BIN_","TOSBIN","PAK","TMP","T","SO","SO_","MXD","TOMDLB_D"): continue
    f.seek(e["off"]); d=f.read(e["cs"])
    if e["cs"]!=e["fs"]:
        if d[:4]==b"TLZC":
            try: d=zlib.decompress(d[24:], -15)
            except Exception: continue
        else: continue
    low=d[:20000]
    for n in needles:
        if n in low:
            print("HIT %-10s hv=%-12d fs=%-8d needle=%s" % (e["ext"], e["hv"], e["fs"], n))
            print("   head:", ''.join(chr(b) if 32<=b<127 else '.' for b in low[:120]))
            hits+=1
            break
    if hits>25: break
f.close()
print("done hits", hits)
