"""Build a 4096x4096 DXT5 atlas holding kf13 pages in a 5x7 page-grid, to replace PAL_FONTB0.
Page p -> grid (col=p%5, row=p//5). Within page: cell c(0..15),r(0..11).
Output cell coords sent by the glyph stub: COL=gpcol*16+c, ROW=gprow*12+r (both *48 px)."""
import struct, zlib, sys, os, subprocess
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
KF = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf13"
OUT = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
TMP = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\mag"
os.makedirs(TMP, exist_ok=True)

raw = open(os.path.join(SRC, "FILEHEADER.TOFHDB"), "rb").read()
head = raw[:40]; fha = raw[40:40 + 84385 * 8]; fa = raw[40 + 84385 * 8:]
recs = []
for i in range(84393):
    o = i * 40
    fs, cs, off, hv = struct.unpack_from("<QQQI", fa, o)
    ext = fa[o + 28:o + 36].split(b"\x00")[0].decode("latin1")
    flags = struct.unpack_from("<I", fa, o + 36)[0]
    recs.append(dict(i=i, fs=fs, cs=cs, off=off, hv=hv, ext=ext, flags=flags))
src = open(os.path.join(SRC, "TLFILE.TLDAT"), "rb")


def dec(rec):
    src.seek(rec["off"]); b = src.read(rec["cs"])
    if rec["cs"] == rec["fs"]:
        return b
    return zlib.decompress(b[24:], -15) if b[:4] == b"TLZC" else b


pal = recs[83362]
dds_old = dec(pal)
dds_old = dds_old[4:] if dds_old[:4] != b"DDS " else dds_old
assert dds_old[:4] == b"DDS ", dds_old[:8]
H, W = struct.unpack_from("<II", dds_old, 12)
print("PAL_FONTB0 old:", W, "x", H, "len", len(dds_old), "mips", struct.unpack_from("<I", dds_old, 28)[0])

# compose 4096x4096 grid image
AW, AH = 4096, 4096
img = Image.new("RGBA", (AW, AH), (0, 0, 0, 0))
pages = sorted([f for f in os.listdir(KF) if f.startswith("page_") and f.endswith(".png") and "_view" not in f and "rgb" not in f])
print("pages:", pages)
for i, f in enumerate(pages):
    pg = Image.open(os.path.join(KF, f)).convert("RGBA")
    if pg.size != (768, 576):
        pg = pg.resize((768, 576))
    gp_c = i % 5; gp_r = i // 5
    img.paste(pg, (gp_c * 768, gp_r * 576), pg)
    print("  page", i, f, "-> grid", (gp_c, gp_r))
big = os.path.join(TMP, "pal_atlas.png")
img.save(big)
dds_png = os.path.join(TMP, "pal_atlas.dds")
subprocess.run(["magick", big, "-define", "dds:compression=dxt5", dds_png], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
body = open(dds_png, "rb").read()[128:][:AW * AH]
new_dds = dds_old[:128] + body
print("new atlas dds len", len(new_dds))
payload = struct.pack("<I", len(new_dds)) + new_dds

repl = {83362: payload}


def tlzc(data):
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    b = co.compress(data) + co.flush()
    return b"TLZC" + struct.pack("<IIIII", 0x201, len(b) + 24, len(data), 0, 0) + b


OUTDIR = os.path.join(OUT, "tppal")
os.makedirs(OUTDIR, exist_ok=True)
new_fa = bytearray(); out = open(os.path.join(OUTDIR, "TLFILE.TLDAT"), "wb"); off = 0
for r in recs:
    if r["i"] in repl:
        data = tlzc(repl[r["i"]]); fs = len(repl[r["i"]]); cs = len(data)
    else:
        src.seek(r["off"]); data = src.read(r["cs"]); fs = r["fs"]; cs = r["cs"]
    out.write(data)
    new_fa += struct.pack("<QQQI", fs, cs, off, r["hv"]) + r["ext"].encode("latin1").ljust(8, b"\x00") + struct.pack("<I", r["flags"])
    off += len(data)
out.close()
open(os.path.join(OUTDIR, "FILEHEADER.TOFHDB"), "wb").write(head + fha + bytes(new_fa))
print("done TLDAT", off)
