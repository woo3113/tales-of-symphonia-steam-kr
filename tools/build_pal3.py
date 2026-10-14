"""Build PAL_FONTB0 = 768x1728 (3 stacked kf13 pages, mips=3) to test the 'engine normalises
UV by 768x1728' hypothesis.  Mapping: gi 0..575 -> group=gi/192, slot=gi%192 (original formula)."""
import struct, zlib, sys, os, subprocess
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\backup"  # ORIGINAL data
KF = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf13"
OUT = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\tppal3"
TMP = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\mag"
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)
raw = open(os.path.join(SRC, "FILEHEADER.TOFHDB.orig"), "rb").read()
head = raw[:40]; fha = raw[40:40 + 84385 * 8]; fa = raw[40 + 84385 * 8:]
recs = []
for i in range(84393):
    o = i * 40
    fs, cs, off, hv = struct.unpack_from("<QQQI", fa, o)
    ext = fa[o + 28:o + 36].split(b"\x00")[0].decode("latin1")
    flags = struct.unpack_from("<I", fa, o + 36)[0]
    recs.append(dict(i=i, fs=fs, cs=cs, off=off, hv=hv, ext=ext, flags=flags))
src = open(os.path.join(SRC, "TLFILE.TLDAT.orig"), "rb")


def dec(r):
    src.seek(r["off"]); b = src.read(r["cs"])
    if r["cs"] == r["fs"]:
        return b
    return zlib.decompress(b[24:], -15) if b[:4] == b"TLZC" else b


d0 = dec(recs[83362])          # ORIGINAL PAL_FONTB0 (768x1728 DXT5 mips3)
d0 = d0[4:] if d0[:4] != b"DDS " else d0
H, W = struct.unpack_from("<II", d0, 12)
print("orig PAL_FONTB0", W, "x", H, "len", len(d0), "mips", struct.unpack_from("<I", d0, 28)[0])

img = Image.new("RGBA", (768, 1728), (0, 0, 0, 0))
for i in range(3):
    pg = Image.open(os.path.join(KF, "page_%02d.png" % i)).convert("RGBA")
    if pg.size != (768, 576):
        pg = pg.resize((768, 576))
    img.paste(pg, (0, i * 576), pg)
png = os.path.join(TMP, "pal3.png"); img.save(png)
tmp = os.path.join(TMP, "pal3_t.dds")
body = b""
for i, (w, h) in enumerate(((768, 1728), (384, 864), (192, 432))):
    subprocess.run(["magick", png, "-resize", "%dx%d!" % (w, h), "-define", "dds:compression=dxt5", tmp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    body += open(tmp, "rb").read()[128:][:w * h]
new_dds = d0[:128] + body
print("new dds len", len(new_dds), "expect", len(d0))
assert len(new_dds) == len(d0)
payload = struct.pack("<I", len(new_dds)) + new_dds


def tlzc(data):
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    b = co.compress(data) + co.flush()
    return b"TLZC" + struct.pack("<IIIII", 0x201, len(b) + 24, len(data), 0, 0) + b


# start from the ORIGINAL data and replace only PAL_FONTB0 (so Korean TEXT comes from... none here)
# -> we need the Korean TEXT too, so use the PATCH data as base instead.
SRCP = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
rawp = open(os.path.join(SRCP, "FILEHEADER.TOFHDB"), "rb").read()
headp = rawp[:40]; fhap = rawp[40:40 + 84385 * 8]; fap = rawp[40 + 84385 * 8:]
recs = []
for i in range(84393):
    o = i * 40
    fs, cs, off, hv = struct.unpack_from("<QQQI", fap, o)
    ext = fap[o + 28:o + 36].split(b"\x00")[0].decode("latin1")
    flags = struct.unpack_from("<I", fap, o + 36)[0]
    recs.append(dict(i=i, fs=fs, cs=cs, off=off, hv=hv, ext=ext, flags=flags))
src = open(os.path.join(SRCP, "TLFILE.TLDAT"), "rb")
new_fa = bytearray(); out = open(os.path.join(OUT, "TLFILE.TLDAT"), "wb"); off = 0
for r in recs:
    if r["i"] == 83362:
        data = tlzc(payload); fs = len(payload); cs = len(data)
    else:
        src.seek(r["off"]); data = src.read(r["cs"]); fs = r["fs"]; cs = r["cs"]
    out.write(data)
    new_fa += struct.pack("<QQQI", fs, cs, off, r["hv"]) + r["ext"].encode("latin1").ljust(8, b"\x00") + struct.pack("<I", r["flags"])
    off += len(data)
out.close()
open(os.path.join(OUT, "FILEHEADER.TOFHDB"), "wb").write(headp + fhap + bytes(new_fa))
print("done TLDAT", off)
