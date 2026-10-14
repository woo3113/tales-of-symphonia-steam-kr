"""Color-code each font texture family with a distinct solid color, so one dialogue
screenshot reveals which texture the engine samples for glyphs.
  FONTTYPEDATA -> cyan   FONTTYPEA -> green   FONTTYPEB -> blue
  FONTTYPEC -> yellow    PAL_FONTB0 -> red    NUMERALFONTTEX/TL_FONT_TEST -> white
"""
import struct, zlib, sys, os, subprocess, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
OUT = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\tpcolor"
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


def find_pic(name):
    for r in recs:
        if r["ext"] == "TOTEXB_D":
            if name.encode() in dec(r):
                return r["i"] + 1
    return None


cache = {}


def solid(W, H, payload, rgb, header):
    key = (W, H, payload, rgb)
    if key not in cache:
        png = os.path.join(TMP, "c_%d_%d_%s.png" % (W, H, rgb))
        subprocess.run(["magick", "-size", "%dx%d" % (W, H), "xc:rgb(%s)" % ",".join(map(str, rgb)), png], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        levels = 0; sz = 0; w = W; h = H
        while True:
            s = max(1, w) * max(1, h)
            if sz + s > payload: break
            sz += s; levels += 1; w //= 2; h //= 2
        data = b""
        for i in range(levels):
            ww = max(1, W >> i); hh = max(1, H >> i)
            tmp = os.path.join(TMP, "c_%d_%d_%d_%d.dds" % (W, H, rgb[0], i))
            subprocess.run(["magick", png, "-resize", "%dx%d!" % (ww, hh), "-define", "dds:compression=dxt5", tmp],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            data += open(tmp, "rb").read()[128:][:ww * hh]
        assert len(data) == payload, (W, H, levels, len(data), payload)
        cache[key] = header + data
    return cache[key]


# (family base, count, rgb)
families = [(83202, 20, (0, 255, 255), "DATA"), (83242, 20, (0, 255, 0), "A"),
            (83282, 20, (0, 0, 255), "B"), (83322, 20, (255, 255, 0), "C")]
repl = {}
for base, n, rgb, nm in families:
    for k in range(n):
        idx = base + 2 * k
        r = recs[idx]; o = dec(r); dds = o[4:] if o[:4] != b"DDS " else o
        H, W = struct.unpack_from("<II", dds, 12)
        repl[idx] = struct.pack("<I", len(dds)) + solid(W, H, len(dds) - 128, rgb, dds[:128])
        if k == 0:
            print("family", nm, "idx", idx, "%dx%d" % (W, H), "rgb", rgb)
for nm, rgb in (("PAL_FONTB0.totexp_p", (255, 0, 0)), ("NUMERALFONTTEX_PIC000.totexp_p", (255, 255, 255)),
                ("TL_FONT_TEST.totexp_p", (255, 255, 255))):
    idx = find_pic(nm)
    r = recs[idx]; o = dec(r); dds = o[4:] if o[:4] != b"DDS " else o
    H, W = struct.unpack_from("<II", dds, 12)
    repl[idx] = struct.pack("<I", len(dds)) + solid(W, H, len(dds) - 128, rgb, dds[:128])
    print(nm, "idx", idx, "%dx%d" % (W, H), "rgb", rgb)
print("replaced", len(repl))


def tlzc(data):
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    body = co.compress(data) + co.flush()
    return b"TLZC" + struct.pack("<IIIII", 0x201, len(body) + 24, len(data), 0, 0) + body


new_fa = bytearray(); out = open(os.path.join(OUT, "TLFILE.TLDAT"), "wb"); off = 0
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
