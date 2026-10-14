"""Clean histogram of EUC-KR symbol usage in the Korean text (TXB + SO).

A string counts as Korean text when it decodes cleanly as EUC-KR, has >=2
Hangul syllables, and those Hangul clearly outnumber any Shift-JIS kana it
would produce (so leftover untranslated Japanese is excluded)."""
import struct, zlib, os, sys, unicodedata
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
TEXTS = ("TXB", "CSV", "TXT", "SO", "ABN", "PBD", "EVD")

d = open(os.path.join(P, "FILEHEADER.TOFHDB"), "rb").read()
base = 40 + 84385 * 8
recs = []
for i in range((len(d) - base) // 40):
    o = base + 40 * i
    fs, cs, off, hv = struct.unpack_from("<QQQI", d, o)
    ext = d[o + 28:o + 36].split(b"\x00")[0].decode("latin1")
    recs.append((ext, fs, cs, off, hv))
f = open(os.path.join(P, "TLFILE.TLDAT"), "rb")

SYM = Counter(); CTX = {}
HAN = Counter()
nkr = 0; nstr = 0
samples = []
for ext, fs, cs, off, hv in recs:
    if ext not in TEXTS:
        continue
    f.seek(off); b = f.read(cs)
    if b[:4] == b"TLZC":
        b = zlib.decompress(b[24:], -15)
    for s in b.split(b"\x00"):
        if len(s) < 4:
            continue
        nstr += 1
        try:
            t = s.decode("euc_kr")
        except Exception:
            continue
        nh = sum(1 for c in t if "\uac00" <= c <= "\ud7a3")
        if nh < 2:
            continue
        # sjis kana count for confidence
        try:
            tj = s.decode("shift_jis")
            nk = sum(1 for c in tj if "\u3040" <= c <= "\u30ff")
        except Exception:
            nk = 0
        if nh <= nk:
            continue
        nkr += 1
        j = 0; n = len(s); got = []
        while j < n - 1:
            x, y = s[j], s[j + 1]
            if 0xA1 <= x <= 0xAF and 0xA1 <= y <= 0xFE:
                SYM[(x, y)] += 1; got.append(j)
                if (x, y) not in CTX:
                    CTX[(x, y)] = (ext, t)
                j += 2; continue
            if 0xB0 <= x <= 0xC8 and 0xA1 <= y <= 0xFE:
                HAN[(x, y)] += 1; j += 2; continue
            j += 1
        if got and len(samples) < 60:
            samples.append((ext, t))
f.close()

out = []
out.append("strings=%d korean=%d" % (nstr, nkr))
out.append("hangul tokens=%d distinct=%d" % (sum(HAN.values()), len(HAN)))
out.append("symbol tokens=%d distinct=%d" % (sum(SYM.values()), len(SYM)))
out.append("")
out.append("=== symbol codes present (char, unicode name, count) ===")
for (x, y), c in sorted(SYM.items()):
    try:
        ch = bytes([x, y]).decode("euc_kr")
    except Exception:
        ch = "?"
    try:
        nm = unicodedata.name(ch)
    except Exception:
        nm = "?"
    out.append("%02X%02X U+%04X %-3s x%-5d %s" % (x, y, ord(ch), ch, c, nm))
out.append("")
out.append("=== per-lead summary ===")
lead = Counter(x for (x, y) in SYM)
for x in sorted(lead):
    codes = sorted(y for (a, y) in SYM if a == x)
    s = "".join(bytes([x, y]).decode("euc_kr", "replace") for y in codes)
    out.append("lead %02X: %2d : %s" % (x, len(codes), s))
out.append("")
out.append("=== sample Korean strings containing symbols ===")
for ext, t in samples:
    out.append("[%s] %s" % (ext, t.replace("\n", "\\n")))
open("sym_scan5.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote sym_scan5.txt")
