"""Extract NUL-separated strings from the changed text entries, keep clean
EUC-KR Korean strings, and histogram symbol codes inside real text only."""
import struct, zlib, sys, os, re
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PATCH = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
TEXTS = ("TXB", "CSV", "TXT", "SO", "ABN", "PBD", "EVD")

def parse_idx(path):
    d = open(path, "rb").read(); base = 40 + 84385 * 8
    recs = []
    for i in range((len(d) - base) // 40):
        o = base + 40 * i
        fs, cs, off, hv = struct.unpack_from("<QQQI", d, o)
        ext = d[o + 28:o + 36].split(b"\x00")[0].decode("latin1")
        recs.append(dict(i=i, fs=fs, cs=cs, off=off, hv=hv, ext=ext))
    return recs

pi = parse_idx(os.path.join(PATCH, "FILEHEADER.TOFHDB"))
fp = open(os.path.join(PATCH, "TLFILE.TLDAT"), "rb")

def get(r):
    fp.seek(r["off"]); d = fp.read(r["cs"])
    if r["cs"] == r["fs"]:
        return d
    return zlib.decompress(d[24:], -15) if d[:4] == b"TLZC" else None

SYM = Counter(); CTX = {}
HAN = Counter()
nstr = 0; nkr = 0; nsymstr = 0
samples = []

for r in pi:
    if r["ext"] not in TEXTS:
        continue
    d = get(r)
    if d is None:
        continue
    for s in d.split(b"\x00"):
        if len(s) < 4:
            continue
        nstr += 1
        # must be valid EUC-KR with no decode errors
        try:
            t = s.decode("euc_kr")
        except Exception:
            continue
        nh = sum(1 for c in t if "\uac00" <= c <= "\ud7a3")
        if nh < 2:
            continue
        nkr += 1
        # walk the ORIGINAL bytes to attribute codes
        j = 0; n = len(s); has_sym = False
        while j < n - 1:
            x, y = s[j], s[j + 1]
            if 0xA1 <= x <= 0xAF and 0xA1 <= y <= 0xFE:
                SYM[(x, y)] += 1; has_sym = True
                if (x, y) not in CTX:
                    CTX[(x, y)] = t[max(0, j - 20):j + 20] if False else t
                j += 2; continue
            if 0xB0 <= x <= 0xC8 and 0xA1 <= y <= 0xFE:
                HAN[(x, y)] += 1; j += 2; continue
            j += 1
        if has_sym:
            nsymstr += 1
            if len(samples) < 40:
                samples.append((r["ext"], t))
fp.close()

print("strings total=%d korean=%d with_symbol=%d" % (nstr, nkr, nsymstr))
print("hangul tokens=%d distinct=%d" % (sum(HAN.values()), len(HAN)))
print("symbol tokens=%d distinct=%d" % (sum(SYM.values()), len(SYM)))
print("\n=== symbol rows present ===")
lead = Counter(x for (x, y) in SYM)
for x in sorted(lead):
    codes = sorted(y for (a, y) in SYM if a == x)
    print("lead %02X: %2d : %s" % (x, len(codes), b"".join(bytes([x, y]) for y in codes).decode("euc_kr", "replace")))
print("\n=== symbol codes with counts ===")
for (x, y) in sorted(SYM):
    try: ch = bytes([x, y]).decode("euc_kr")
    except Exception: ch = "?"
    print("%02X%02X %-3s x%d" % (x, y, ch, SYM[(x, y)]))
print("\n=== sample Korean strings with symbols ===")
for ext, t in samples:
    print("[%s] %s" % (ext, t.replace("\n", "\\n")))
