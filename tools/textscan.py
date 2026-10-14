import re, os, sys, zlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
def raw(off, cs):
    with open(os.path.join(R,"TLFILE.TLDAT"),"rb") as f:
        f.seek(off); return f.read(cs)
xml = open(os.path.join(R,"FILEHEADER.TOFHDB.debug"),"rb").read().decode("shift_jis","replace")
entries=[]
for m in re.finditer(r"<File>\s*<FileSize>\s*(\d+)\s*</FileSize>\s*<CompressSize>\s*(\d+)\s*</CompressSize>\s*<Offset>\s*(\d+)\s*</Offset>\s*<HashValue>\s*(\d+)\s*</HashValue>\s*<Extension>\s*\"([^\"]*)\"\s*</Extension>", xml):
    fs,cs,off,hv,ext = m.groups()
    entries.append(dict(fs=int(fs),cs=int(cs),off=int(off),hv=int(hv),ext=ext))
def dec(e):
    d = raw(e["off"], e["cs"])
    if e["cs"]==e["fs"]: return d
    if d[:4]==b"TLZC": return zlib.decompress(d[24:], -15)
    return None
# all CSV / TXB / TXT
for ext in ["CSV","TXB","TXT","BAK","T","EVD"]:
    for e in entries:
        if e["ext"]==ext:
            d=dec(e)
            print("== %s fs=%d cs=%d hv=%d declen=%s" % (ext,e["fs"],e["cs"],e["hv"],len(d) if d else None))
            if d:
                print("   head:", ''.join(chr(b) if 32<=b<127 else '.' for b in d[:150]))
                ss=set(s.decode('latin1') for s in re.findall(rb"[\x20-\x7e]{5,}", d))
                smp=[s for s in ss if 'TEXT' in s or 'font' in s.lower() or 'FONT' in s][:6]
                print("   sample strings:", list(ss)[:5], "...", smp)
