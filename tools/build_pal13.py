"""PAL_FONTB0 = 768 x (13*576=7488) DXT5, 13 kf13 pages stacked vertically.
Mapping: gi 0..2444 -> group=gi/192, slot=gi%192 -> row=(slot>>4)+group*12 (0..155), col=slot&0xF."""
import struct, zlib, sys, os, subprocess
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
BAK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\backup"
KF = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf13"
OUT = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\tppal13"
TMP = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\mag"
os.makedirs(OUT, exist_ok=True)
NP = 13
H = NP * 576; W = 768
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
for i in range(NP):
    pg = Image.open(os.path.join(KF, "page_%02d.png" % i)).convert("RGBA")
    if pg.size != (768, 576):
        pg = pg.resize((768, 576))
    img.paste(pg, (0, i * 576), pg)
png = os.path.join(TMP, "pal13.png"); img.save(png)
tmp = os.path.join(TMP, "pal13.dds")
subprocess.run(["magick", png, "-define", "dds:compression=dxt5", tmp], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
body = open(tmp, "rb").read()[128:][:W * H]
assert len(body) == W * H
# header from original 768x1728 PAL_FONTB0, adjust height/linearsize/mips
src = open(os.path.join(BAK, "FILEHEADER.TOFHDB.orig"), "rb").read()
base = 40 + 84385 * 8
o = base + 40 * 83362
fs, cs, off, hv = struct.unpack_from("<QQQI", src, o)
f = open(os.path.join(BAK, "TLFILE.TLDAT.orig"), "rb"); f.seek(off); b = f.read(cs)
d0 = zlib.decompress(b[24:], -15) if b[:4] == b"TLZC" else b
d0 = d0[4:] if d0[:4] != b"DDS " else d0
hdr = bytearray(d0[:128])
struct.pack_into("<I", hdr, 8, 0x000A1007)          # flags: HAS HEIGHT|WIDTH|PIXELFORMAT|LINEARSIZE|MIPMAPCOUNT
struct.pack_into("<I", hdr, 12, H)                  # height
struct.pack_into("<I", hdr, 16, W)                  # width
struct.pack_into("<I", hdr, 20, (W // 4) * (H // 4) * 16)  # linear size (DXT5)
struct.pack_into("<I", hdr, 28, 1)                  # mip count
new_dds = bytes(hdr) + body
payload = struct.pack("<I", len(new_dds)) + new_dds
print("new PAL_FONTB0", W, "x", H, "dds len", len(new_dds))


def tlzc(data):
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    bb = co.compress(data) + co.flush()
    return b"TLZC" + struct.pack("<IIIII", 0x201, len(bb) + 24, len(data), 0, 0) + bb


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
    else:
        srcp.seek(r["off"]); data = srcp.read(r["cs"]); fs = r["fs"]; cs = r["cs"]
    out.write(data)
    new_fa += struct.pack("<QQQI", fs, cs, off, r["hv"]) + r["ext"].encode("latin1").ljust(8, b"\x00") + struct.pack("<I", r["flags"])
    off += len(data)
out.close()
open(os.path.join(OUT, "FILEHEADER.TOFHDB"), "wb").write(headp + fhap + bytes(new_fa))
print("done TLDAT", off)
