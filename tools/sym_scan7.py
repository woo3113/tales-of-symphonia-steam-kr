"""Clean, exhaustive symbol histogram over ALL text-like strings (no hangul-count
heuristic): tokenize as ASCII | 2-byte with lead 0xA1..0xC8 (EUC-KR text area);
reject strings with control bytes / Hanja leads / stray high bytes."""
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
okstr = 0
for ext, fs, cs, off, hv in recs:
    if ext not in TEXTS:
        continue
    f.seek(off); b = f.read(cs)
    if b[:4] == b"TLZC":
        b = zlib.decompress(b[24:], -15)
    for s in b.split(b"\x00"):
        if len(s) < 2:
            continue
        # tokenize
        j = 0; n = len(s); toks = []; bad = False; nb2 = 0
        while j < n:
            c = s[j]
            if c == 0x09 or c == 0x0A or c == 0x0D or 0x20 <= c <= 0x7E:
                toks.append(("a", c)); j += 1; continue
            if 0xA1 <= c <= 0xC8 and j + 1 < n and 0xA1 <= s[j + 1] <= 0xFE:
                toks.append(("d", (c << 8) | s[j + 1])); nb2 += 1; j += 2; continue
            bad = True; break
        if bad or nb2 == 0:
            continue
        okstr += 1
        try:
            t = s.decode("euc_kr")
        except Exception:
            t = s.decode("euc_kr", "replace")
        for kind, v in toks:
            if kind == "d" and 0xA1A1 <= v <= 0xAFFE:
                SYM[v] += 1
                if len(SAMP[v]) < 4:
                    SAMP[v].append(t)
f.close()

lines = ["text-like strings=%d distinct symbol codes=%d tokens=%d" % (okstr, len(SYM), sum(SYM.values())), ""]
common = 0
for code, c in sorted(SYM.items(), key=lambda kv: -kv[1]):
    x, y = code >> 8, code & 0xFF
    try:
        ch = bytes([x, y]).decode("euc_kr")
    except Exception:
        ch = "?"
    lines.append("### %02X%02X '%s' x%d" % (x, y, ch, c))
    if c >= 2:
        common += 1
        for s in SAMP[code][:2]:
            lines.append("    " + s.replace("\n", "\\n")[:160])
lines.insert(1, "codes with x>=2: %d" % common)
open("sym_final.txt", "w", encoding="utf-8").write("\n".join(lines))
print("wrote sym_final.txt: okstr=%d codes=%d x>=2=%d" % (okstr, len(SYM), common))
