"""Find the actual Korean *text* entries (orig vs patch diff) and histogram
EUC-KR symbol codes only inside those text entries (no binary noise)."""
import struct, zlib, sys, os, re
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ORIG = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
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

SYM = Counter()
CTX = {}
HANGUL = Counter()
text_entries = []
per_ext = Counter()
sym_entries = Counter()   # ext -> symbol tokens

for i in range(len(oi)):
    a = get(fo, oi[i]); b = get(fp, pi[i])
    if a == b or a is None or b is None:
        continue
    # count hangul (syllable rows) and symbol rows in patched data
    nh = len(re.findall(rb"[\xb0-\xc8][\xa1-\xfe]", b))
    if nh < 20:
        continue
    # text-ish heuristic: EUC-KR hangul should be dense; require hangul density
    ntok_sym = 0
    j = 0; n = len(b)
    while j < n - 1:
        x, y = b[j], b[j + 1]
        if 0xA1 <= x <= 0xAF and 0xA1 <= y <= 0xFE:
            SYM[(x, y)] += 1
            ntok_sym += 1
            if (x, y) not in CTX:
                m = max(0, j - 30)
                CTX[(x, y)] = b[m:j + 24].decode("euc_kr", "replace")
            j += 2; continue
        if 0xB0 <= x <= 0xC8 and 0xA1 <= y <= 0xFE:
            HANGUL[(x, y)] += 1
            j += 2; continue
        j += 1
    text_entries.append((i, oi[i]["ext"], nh, ntok_sym, len(b)))
    per_ext[oi[i]["ext"]] += 1
    sym_entries[oi[i]["ext"]] += ntok_sym

fo.close(); fp.close()

print("text entries:", len(text_entries))
print("by ext:", per_ext.most_common())
print("symbol tokens by ext:", sym_entries.most_common())
print("hangul tokens:", sum(HANGUL.values()), "symbol tokens:", sum(SYM.values()), "distinct sym:", len(SYM))
print("\n=== distinct symbol codes per lead (from text only) ===")
lead = Counter()
for (x, y) in SYM:
    lead[x] += 1
for x in sorted(lead):
    codes = sorted(y for (a, y) in SYM if a == x)
    print("lead %02X: %d codes" % (x, len(codes)))
print("\n=== all symbol codes w/ count + context (sorted by lead,trail) ===")
for (x, y) in sorted(SYM):
    try:
        ch = bytes([x, y]).decode("euc_kr")
    except Exception:
        ch = "?"
    print("%02X%02X %-3s x%-7d %r" % (x, y, ch, SYM[(x, y)], CTX[(x, y)]))
