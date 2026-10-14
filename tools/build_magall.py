"""Build a TLDAT where ALL font textures are solid opaque magenta (to locate the real glyph texture).
Targets: FONTDATA/A/B/C PIC000..019, PAL_FONTB0, NUMERALFONTTEX_PIC000, TL_FONT_TEST."""
import struct, zlib, sys, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
OUT = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\tpmagall"
TMP = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\mag"
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)
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


def find_desc_pic(desc_name):
    """return the picture record index for a TOTEXB_D descriptor whose name matches."""
    for r in recs:
        if r["ext"] == "TOTEXB_D":
            b = dec(r)
            if desc_name.encode() in b:
                return r["i"] + 1
    return None


cache = {}


def magenta_dds(W, H, target, header):
    key = (W, H, target)
    if key not in cache:
        import subprocess
        # how many mip levels fit the target payload?
        levels = 0; sz = 0; w = W; h = H
        while True:
            s = max(1, w) * max(1, h)
            if sz + s > target:
                break
            sz += s; levels += 1; w //= 2; h //= 2
        png = os.path.join(TMP, "m_%dx%d.png" % (W, H))
        subprocess.run(["magick", "-size", "%dx%d" % (W, H), "xc:rgb(255,0,255)", png], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        data = b""
        for i in range(levels):
            ww = max(1, W >> i); hh = max(1, H >> i)
            tmp = os.path.join(TMP, "_t_%dx%d_%d.dds" % (W, H, i))
            subprocess.run(["magick", png, "-resize", "%dx%d!" % (ww, hh), "-define", "dds:compression=dxt5", "-define", "dds:mipmaps=1", tmp],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            data += open(tmp, "rb").read()[128:][:ww * hh]
        assert len(data) == target, (W, H, levels, len(data), target)
        cache[key] = header + data
    return cache[key]


targets = []
for base in (83202, 83242, 83282, 83322):
    for n in range(20):
        targets.append(base + 2 * n)
for nm in ("PAL_FONTB0.totexp_p", "NUMERALFONTTEX_PIC000.totexp_p", "TL_FONT_TEST.totexp_p"):
    idx = find_desc_pic(nm)
    if idx is not None:
        targets.append(idx)
        print("named", nm, "-> picture idx", idx)
    else:
        print("NOT FOUND", nm)

repl = {}
for idx in targets:
    r = recs[idx]
    o = dec(r)
    dds = o[4:] if o[:4] != b"DDS " else o
    assert dds[:4] == b"DDS ", (idx, dds[:8])
    H, W = struct.unpack_from("<II", dds, 12)
    mips = struct.unpack_from("<I", dds, 28)[0]
    m = magenta_dds(W, H, len(dds) - 128, dds[:128])
    assert len(m) == len(dds), (idx, W, H, len(m), len(dds))
    repl[idx] = struct.pack("<I", len(m)) + m
print("targets:", len(targets), "replaced:", len(repl))


def tlzc(data):
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    body = co.compress(data) + co.flush()
    return b"TLZC" + struct.pack("<IIIII", 0x201, len(body) + 24, len(data), 0, 0) + body


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
