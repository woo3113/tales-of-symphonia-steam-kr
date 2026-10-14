"""PAL_FONTB0 = 768 x 9792 = [original pages 0,1 (1152px)] + [15 kf14 pages: 2350
hangul + 95 ASCII + 282 EUC-KR A1..A3 symbols].  Descriptor idx 83361 height -> 9792.
Layout: glyph idx G -> group = 2 + G/192, slot = G%192."""
import struct, zlib, sys, os, subprocess, io
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
BAK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\backup"
KF = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf14"
OUT = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\tppal16"
TMP = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\mag"
os.makedirs(OUT, exist_ok=True)

rawO = open(os.path.join(BAK, "FILEHEADER.TOFHDB.orig"), "rb").read()
baseO = 40 + 84385 * 8
fs, cs, off, hv = struct.unpack_from("<QQQI", rawO, baseO + 40 * 83362)
fo = open(os.path.join(BAK, "TLFILE.TLDAT.orig"), "rb"); fo.seek(off); b = fo.read(cs)
d0 = zlib.decompress(b[24:], -15) if b[:4] == b"TLZC" else b
d0 = d0[4:] if d0[:4] != b"DDS " else d0
assert d0[:4] == b"DDS "
oH, oW = struct.unpack_from("<II", d0, 12)
print("orig PAL", oW, "x", oH)
oimg = Image.open(io.BytesIO(d0)).convert("RGBA")
assert oimg.size == (oW, oH), oimg.size
top = oimg.crop((0, 0, oW, 1152))
print("orig top", top.size)

NP = 15
H = 1152 + NP * 576                          # 9792
W = 768
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
img.paste(top, (0, 0))
for i in range(NP):
    pg = Image.open(os.path.join(KF, "page_%02d.png" % i)).convert("RGBA")
    if pg.size != (768, 576):
        pg = pg.resize((768, 576))
    img.paste(pg, (0, 1152 + i * 576), pg)
png = os.path.join(TMP, "pal16.png"); img.save(png)
tmp = os.path.join(TMP, "pal16.dds")
subprocess.run(["magick", png, "-define", "dds:compression=dxt5", tmp], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
body = open(tmp, "rb").read()[128:][:W * H]
assert len(body) == W * H, (len(body), W * H)
hdr = bytearray(d0[:128])
struct.pack_into("<I", hdr, 8, 0x000A1007)
struct.pack_into("<I", hdr, 12, H)
struct.pack_into("<I", hdr, 16, W)
struct.pack_into("<I", hdr, 20, (W // 4) * (H // 4) * 16)
struct.pack_into("<I", hdr, 28, 1)
new_dds = bytes(hdr) + body
payload = struct.pack("<I", len(new_dds)) + new_dds
print("new PAL", W, "x", H, "dds len", len(new_dds))


def tlzc(data):
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    bb = co.compress(data) + co.flush()
    return b"TLZC" + struct.pack("<IIIII", 0x201, len(bb) + 24, len(data), 0, 0) + bb


srcD = open(os.path.join(SRC, "FILEHEADER.TOFHDB"), "rb").read()
baseD = 40 + 84385 * 8
oD = baseD + 40 * 83361
dfs, dcs, doff, dhv = struct.unpack_from("<QQQI", srcD, oD)
f0 = open(os.path.join(SRC, "TLFILE.TLDAT"), "rb"); f0.seek(doff); db = f0.read(dcs)
desc = bytearray(zlib.decompress(db[24:], -15) if db[:4] == b"TLZC" else db)
print("descriptor old height", struct.unpack_from("<H", desc, 20)[0])
struct.pack_into("<H", desc, 20, H)

rawp = open(os.path.join(SRC, "FILEHEADER.TOFHDB"), "rb").read()
headp = rawp[:40]; fhap = rawp[40:40 + 84385 * 8]; fap = rawp[40 + 84385 * 8:]
recs = []
for i in range(84393):
    oo = i * 40
    fs, cs, off, hv = struct.unpack_from("<QQQI", fap, oo)
    ext = fap[oo + 28:oo + 36].split(b"\x00")[0].decode("latin1")
    flags = struct.unpack_from("<I", fap, oo + 36)[0]
    recs.append(dict(i=i, fs=fs, cs=cs, off=off, hv=hv, ext=ext, flags=flags))
srcp = open(os.path.join(SRC, "TLFILE.TLDAT"), "rb")
new_fa = bytearray(); out = open(os.path.join(OUT, "TLFILE.TLDAT"), "wb"); off = 0
for r in recs:
    if r["i"] == 83362:
        data = tlzc(payload); fs = len(payload); cs = len(data)
    elif r["i"] == 83361:
        data = tlzc(bytes(desc)); fs = len(desc); cs = len(data)
    else:
        srcp.seek(r["off"]); data = srcp.read(r["cs"]); fs = r["fs"]; cs = r["cs"]
    out.write(data)
    new_fa += struct.pack("<QQQI", fs, cs, off, r["hv"]) + r["ext"].encode("latin1").ljust(8, b"\x00") + struct.pack("<I", r["flags"])
    off += len(data)
out.close()
open(os.path.join(OUT, "FILEHEADER.TOFHDB"), "wb").write(headp + fhap + bytes(new_fa))
print("done TLDAT", off)
