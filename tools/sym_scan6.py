"""For each EUC-KR symbol code used in Korean strings, show full sample strings so
we can tell real usage from misdecoded-Japanese false positives."""
import struct, zlib, os, sys
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
TEXTS = ("TXB", "SO", "CSV", "TXT")
d = open(os.path.join(P, "FILEHEADER.TOFHDB"), "rb").read()
base = 40 + 84385 * 8
recs = []
for i in range((len(d) - base) // 40):
    o = base + 40 * i
    fs, cs, off, hv = struct.unpack_from("<QQQI", d, o)
    ext = d[o + 28:o + 36].split(b"\x00")[0].decode("latin1")
    recs.append((ext, fs, cs, off, hv))
f = open(os.path.join(P, "TLFILE.TLDAT"), "rb")

SYM = Counter(); SAMP = defaultdict(list)
for ext, fs, cs, off, hv in recs:
    if ext not in TEXTS:
        continue
    f.seek(off); b = f.read(cs)
    if b[:4] == b"TLZC":
        b = zlib.decompress(b[24:], -15)
    for s in b.split(b"\x00"):
        if len(s) < 4:
            continue
        try:
            t = s.decode("euc_kr")
        except Exception:
            continue
        nh = sum(1 for c in t if "\uac00" <= c <= "\ud7a3")
        if nh < 2:
            continue
        try:
            tj = s.decode("shift_jis")
            nk = sum(1 for c in tj if "\u3040" <= c <= "\u30ff")
        except Exception:
            nk = 0
        if nh <= nk:
            continue
        j = 0; n = len(s)
        while j < n - 1:
            x, y = s[j], s[j + 1]
            if 0xA1 <= x <= 0xAF and 0xA1 <= y <= 0xFE:
                SYM[(x, y)] += 1
                if len(SAMP[(x, y)]) < 3:
                    SAMP[(x, y)].append(t)
                j += 2; continue
            if 0xB0 <= x <= 0xC8 and 0xA1 <= y <= 0xFE:
                j += 2; continue
            j += 1
f.close()

lines = []
for (x, y), c in sorted(SYM.items()):
    if c < 1:
        continue
    try:
        ch = bytes([x, y]).decode("euc_kr")
    except Exception:
        ch = "?"
    lines.append("### %02X%02X '%s' x%d" % (x, y, ch, c))
    for s in SAMP[(x, y)]:
        lines.append("    %s" % s.replace("\n", "\\n"))
open("sym_ctx.txt", "w", encoding="utf-8").write("\n".join(lines))
print("wrote sym_ctx.txt, codes>=1:", sum(1 for v in SYM.values() if v >= 1))
