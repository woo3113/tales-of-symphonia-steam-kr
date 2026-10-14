import struct, zlib, sys, re
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
raw = open(SRC + r"\FILEHEADER.TOFHDB", "rb").read()
base = 40 + 84385 * 8
recs = []
for i in range((len(raw) - base) // 40):
    o = base + 40 * i
    fs, cs, off, hv = struct.unpack_from("<QQQI", raw, o)
    ext = raw[o + 28:o + 36].split(b"\x00")[0].decode("latin1")
    recs.append(dict(i=i, fs=fs, cs=cs, off=off, ext=ext))
f = open(SRC + r"\TLFILE.TLDAT", "rb")
pat = re.compile(rb'[\xa1-\xaf][\xa1-\xfe]')
cnt = Counter()
for r in recs:
    if r["ext"] not in ("BIN", "SKP", "TXB", "CSV", "TXT", "TLFNTB_D", "TLCLRB"):
        continue
    f.seek(r["off"]); b = f.read(r["cs"])
    if not b:
        continue
    d = zlib.decompress(b[24:], -15) if b[:4] == b"TLZC" else b
    for m in pat.finditer(d):
        cnt[m.group()] += 1
print("distinct 2-byte codes with lead A1..AF:", len(cnt))
rows = Counter()
for (b0, b1), n in cnt.items():
    rows[b0] += n
print("by lead row:", {hex(k): v for k, v in sorted(rows.items())})
print("\ntop symbols:")
for (b0, b1), n in cnt.most_common(40):
    try: ch = bytes([b0, b1]).decode('euc_kr')
    except: ch = '?'
    print("  %02X%02X %s x%d" % (b0, b1, ch, n))
