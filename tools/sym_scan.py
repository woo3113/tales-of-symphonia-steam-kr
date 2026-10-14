"""Scan the (Korean) patched TLDAT for EUC-KR 2-byte symbol codes used in text.

Reports per-code counts for lead 0xA1..0xAF (KS X 1001 symbol/jamo rows) and
context samples, so we know exactly which symbols the atlas must provide.
"""
import struct, zlib, sys, os
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PATCH = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"

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

recs = parse_idx(os.path.join(PATCH, "FILEHEADER.TOFHDB"))
print("entries", len(recs))
exts = Counter(r["ext"] for r in recs)
print(exts.most_common(30))

SYM = Counter()          # (b0,b1) -> count, lead 0xA1..0xAF
per_lead = Counter()
samples = {}             # (b0,b1) -> one context string
HANGUL = Counter()

f = open(os.path.join(PATCH, "TLFILE.TLDAT"), "rb")
def get(r):
    f.seek(r["off"]); d = f.read(r["cs"])
    if r["cs"] == r["fs"]:
        return d
    if d[:4] == b"TLZC":
        try:
            return zlib.decompress(d[24:], -15)
        except Exception:
            return None
    return None

ndef = 0
for r in recs:
    d = get(r)
    if d is None:
        ndef += 1
        continue
    n = len(d)
    i = 0
    while i < n - 1:
        b0, b1 = d[i], d[i + 1]
        if 0xA1 <= b0 <= 0xAF and 0xA1 <= b1 <= 0xFE:
            SYM[(b0, b1)] += 1
            per_lead[b0] += 1
            if (b0, b1) not in samples:
                seg = d[max(0, i - 24):i + 40]
                try:
                    samples[(b0, b1)] = seg.decode("euc_kr", "replace")
                except Exception:
                    samples[(b0, b1)] = repr(seg)
            i += 2
            continue
        if 0xB0 <= b0 <= 0xC8 and 0xA1 <= b1 <= 0xFE:
            HANGUL[(b0, b1)] += 1
            i += 2
            continue
        i += 1
f.close()

print("undecompressed entries", ndef)
print("hangul 2-byte tokens:", sum(HANGUL.values()))
print("symbol 2-byte tokens:", sum(SYM.values()), "distinct:", len(SYM))
print("per-lead:", sorted((hex(k), v) for k, v in per_lead.items()))
print("\n=== distinct symbol codes (by lead) ===")
for b0 in sorted(per_lead):
    codes = sorted(c for (a, c) in SYM if a == b0)
    try:
        s = b"".join(bytes([b0, c]) for c in codes).decode("euc_kr", "replace")
    except Exception:
        s = "?"
    print("lead %02X : %d codes  %s" % (b0, len(codes), s))

print("\n=== top 60 symbol codes w/ context ===")
for (b0, b1), c in SYM.most_common(60):
    try:
        ch = bytes([b0, b1]).decode("euc_kr")
    except Exception:
        ch = "?"
    print("%02X%02X %-3s x%-6d  %r" % (b0, b1, ch, c, samples[(b0, b1)]))
