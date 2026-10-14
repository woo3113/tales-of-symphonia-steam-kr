"""Generic atlas injector: replace FONTTYPE{A,B,C} PIC002..014 with DDS pages from a dir.
Usage: py build_atlas_patch2.py <pages_dir> <out_dir>
Reads pages named page_00.dds .. (13 pages) from pages_dir."""
import struct, zlib, sys, os, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PAGES = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf13"
OUT = sys.argv[2] if len(sys.argv) > 2 else r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\tp"
SRC = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
os.makedirs(OUT, exist_ok=True)
SRC_TL = os.path.join(SRC, "TLFILE.TLDAT")
SRC_HDR = os.path.join(SRC, "FILEHEADER.TOFHDB")

raw = open(SRC_HDR, "rb").read()
head = raw[:40]; fha = raw[40:40 + 84385 * 8]; fa = raw[40 + 84385 * 8:]
recs = []
for i in range(84393):
    o = i * 40
    fs, cs, off, hv = struct.unpack_from("<QQQI", fa, o)
    ext = fa[o + 28:o + 36].split(b"\x00")[0].decode("latin1")
    flags = struct.unpack_from("<I", fa, o + 36)[0]
    recs.append(dict(i=i, fs=fs, cs=cs, off=off, hv=hv, ext=ext, flags=flags))

files = sorted(glob.glob(os.path.join(PAGES, "page_*.dds")))
pages = [open(f, "rb").read() for f in files]
print("pages:", [os.path.basename(f) for f in files])
assert all(len(p) == 580736 for p in pages), [len(p) for p in pages]
NP = len(pages)
repl = {}
for name, base in (("A", 83242), ("B", 83282), ("C", 83322)):
    for k in range(NP):
        idx = base + 2 * (k + 2)      # picture for PICnnn == base + 2*nnn
        repl[idx] = struct.pack("<I", len(pages[k])) + pages[k]
print("replacing", len(repl), "entries")


def tlzc(data):
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    body = co.compress(data) + co.flush()
    return b"TLZC" + struct.pack("<IIIII", 0x201, len(body) + 24, len(data), 0, 0) + body


src = open(SRC_TL, "rb")
new_fa = bytearray()
out = open(os.path.join(OUT, "TLFILE.TLDAT"), "wb")
off = 0
for r in recs:
    if r["i"] in repl:
        data = tlzc(repl[r["i"]]); fs = len(repl[r["i"]]); cs = len(data)
    else:
        src.seek(r["off"]); data = src.read(r["cs"]); fs = r["fs"]; cs = r["cs"]
    out.write(data)
    new_fa += struct.pack("<QQQI", fs, cs, off, r["hv"]) + r["ext"].encode("latin1").ljust(8, b"\x00") + struct.pack("<I", r["flags"])
    off += len(data)
out.close()
open(os.path.join(OUT, "FILEHEADER.TOFHDB"), "wb").write(head + fha + bytes(new_fa))
print("done TLDAT", off)
