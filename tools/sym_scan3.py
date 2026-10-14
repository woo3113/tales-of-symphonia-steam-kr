"""Histogram EUC-KR hangul + symbol (0xA1..0xAF) codes only in changed TXB/CSV/TXT/SO
entries (real text), with samples."""
import struct, zlib, sys, os
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ORIG = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
PATCH = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
TEXTS = ("TXB", "CSV", "TXT", "SO", "ABN", "PBD", "EVD", "TOSHDB", "TMP", "T")

def parse_idx(path):
    d = open(path, "rb").read()
    base = 40 + 84385 * 8
    recs = []
    for i in range((len(d) - base) // 40):
        o = base + 40 * i
        fs, cs, off, hv = struct.unpack_from("<QQQI", d, o)
        ext = d[o + 28:o + 36].split(b"\x00")[0].decode("latin1")
        recs.append(dict(i=i, fs=fs, cs=cs, off=off, hv=hv, ext=ext))
    return recs

oi = parse_idx(os.path.join(ORIG, "FILEHEADER.TOFHDB"))
pi = parse_idx(os.path.join(PATCH, "FILEHEADER.TOFHDB"))
fo = open(os.path.join(ORIG, "TLFILE.TLDAT"), "rb")
fp = open(os.path.join(PATCH, "TLFILE.TLDAT"), "rb")

def get(f, r):
    f.seek(r["off"]); d = f.read(r["cs"])
    if r["cs"] == r["fs"]:
        return d
    if d[:4] == b"TLZC":
        try:
            return zlib.decompress(d[24:], -15)
        except Exception:
            return None
    return None

SYM = Counter(); CTX = {}; HAN = Counter()
for i in range(len(oi)):
    if oi[i]["ext"] not in TEXTS:
        continue
    a = get(fo, oi[i]); b = get(fp, pi[i])
    if a is None or b is None or a == b:
        continue
    print("changed text entry idx=%d hv=%d ext=%s orig=%dB patch=%dB" % (i, pi[i]["hv"], oi[i]["ext"], len(a), len(b)))
    j = 0; n = len(b)
    while j < n - 1:
        x, y = b[j], b[j + 1]
        if 0xA1 <= x <= 0xAF and 0xA1 <= y <= 0xFE:
            SYM[(x, y)] += 1
            if (x, y) not in CTX:
                CTX[(x, y)] = b[max(0, j - 36):j + 36].decode("euc_kr", "replace")
            j += 2; continue
        if 0xB0 <= x <= 0xC8 and 0xA1 <= y <= 0xFE:
            HAN[(x, y)] += 1
            j += 2; continue
        j += 1
fo.close(); fp.close()

print("\nhangul tokens:", sum(HAN.values()), "distinct:", len(HAN))
print("symbol tokens:", sum(SYM.values()), "distinct:", len(SYM))
print("\n=== symbol codes per lead ===")
lead = Counter(x for (x, y) in SYM)
for x in sorted(lead):
    codes = sorted(y for (a, y) in SYM if a == x)
    s = b"".join(bytes([x, y]) for y in codes).decode("euc_kr", "replace")
    print("lead %02X: %2d  %s" % (x, len(codes), s))
print("\n=== symbol codes (count + context) ===")
for (x, y) in sorted(SYM):
    try:
        ch = bytes([x, y]).decode("euc_kr")
    except Exception:
        ch = "?"
    print("%02X%02X %-3s x%-6d %r" % (x, y, ch, SYM[(x, y)], CTX[(x, y)]))
