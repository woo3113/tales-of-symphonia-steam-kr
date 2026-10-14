"""Build a patched TLDAT/TOFHDB where FONTTYPE{A,B,C} PIC002..014 are replaced by
kf13 Korean pages (768x576 DXT5). Mapping: Korean glyph code 0x4000+idx -> group 2+idx/192."""
import struct, zlib, sys, os, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

R = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
KF13 = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf13"
OUT = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\tp"
os.makedirs(OUT, exist_ok=True)
SRC_TL = os.path.join(R, "TLFILE.TLDAT")
SRC_HDR = os.path.join(R, "FILEHEADER.TOFHDB")

HDR_SIZE = 40 + 84385 * 8
raw = open(SRC_HDR, "rb").read()
head = raw[:40]
fha = raw[40:40 + 84385 * 8]
fa = raw[40 + 84385 * 8:]
assert len(raw) == HDR_SIZE + 84393 * 40, (len(raw), HDR_SIZE)

recs = []
for i in range(84393):
    o = i * 40
    fs, cs, off, hv = struct.unpack_from("<QQQI", fa, o)
    ext = fa[o + 28:o + 36].split(b"\x00")[0].decode("latin1")
    flags = struct.unpack_from("<I", fa, o + 36)[0]
    recs.append(dict(i=i, fs=fs, cs=cs, off=off, hv=hv, ext=ext, flags=flags))

# replacement map: index -> new uncompressed bytes
pages = [open(os.path.join(KF13, "page_%02d.dds" % k), "rb").read() for k in range(13)]
assert all(len(p) == 580736 for p in pages)
repl = {}
for name, base in (("A", 83242), ("B", 83282), ("C", 83322)):
    for k in range(13):
        idx = base + 2 * (k + 2)     # picture for PICnnn == base + 2*nnn ; k=0 -> PIC002
        repl[idx] = struct.pack("<I", len(pages[k])) + pages[k]
print("replacing", len(repl), "entries:", sorted(repl)[:5], "...")

src = open(SRC_TL, "rb")


def tlzc(data):
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    body = co.compress(data) + co.flush()
    return b"TLZC" + struct.pack("<IIIII", 0x201, len(body) + 24, len(data), 0, 0) + body


new_fa = bytearray()
out = open(os.path.join(OUT, "TLFILE.TLDAT"), "wb")
off = 0
for r in recs:
    if r["i"] in repl:
        data = tlzc(repl[r["i"]])
        fs = r["fs"]
        # fs == 4 + 580736 for our pages; recompute to be safe
        fs = len(repl[r["i"]])
        cs = len(data)
    else:
        src.seek(r["off"])
        data = src.read(r["cs"])
        fs = r["fs"]
        cs = r["cs"]
    out.write(data)
    new_fa += struct.pack("<QQQI", fs, cs, off, r["hv"]) + r["ext"].encode("latin1").ljust(8, b"\x00") + struct.pack("<I", r["flags"])
    off += len(data)
    if r["i"] % 10000 == 0:
        print("  ", r["i"], off)
out.close()
open(os.path.join(OUT, "FILEHEADER.TOFHDB"), "wb").write(head + fha + bytes(new_fa))
print("done. TLDAT size", off)
print("new HDR size", len(head + fha + bytes(new_fa)))
