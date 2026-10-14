import struct, sys, zlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
raw = open(SRC + r"\FILEHEADER.TOFHDB", "rb").read()
base = 40 + 84385*8
recs = []
for i in range((len(raw)-base)//40):
    o = base + 40*i
    fs, cs, off, hv = struct.unpack_from("<QQQI", raw, o)
    ext = raw[o+28:o+36].split(b"\x00")[0].decode("latin1")
    recs.append(dict(i=i, fs=fs, cs=cs, off=off, hv=hv, ext=ext))
f = open(SRC + r"\TLFILE.TLDAT", "rb")
def dec(r):
    f.seek(r["off"]); b = f.read(r["cs"])
    if r["cs"] == r["fs"]: return b
    return zlib.decompress(b[24:], -15) if b[:4] == b"TLZC" else b
for i in range(83320, 83372):
    r = recs[i]
    if r["ext"] != "TOTEXP_P": continue
    d = dec(r)
    if d[:4] != b"DDS " and d[4:8] == b"DDS ":
        d = d[4:]
    if d[:4] != b"DDS ":
        print("idx %d %s n=%d not DDS: %s" % (i, r["ext"], len(d), d[:4])); continue
    h, w = struct.unpack_from("<II", d, 12)
    mips = struct.unpack_from("<I", d, 28)[0]
    # descriptor
    dr = recs[i-1] if recs[i-1]["ext"] == "TOTEXB_D" else None
    desc = dec(dr) if dr else b""
    print("idx %5d DDS %4dx%-5d mips=%d len=%-9d  desc=%s" % (i, w, h, mips, len(d), desc[16:26].hex() if desc else ""))
