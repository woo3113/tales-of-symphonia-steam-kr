import struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
d = open(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\krcodes13.bin", "rb").read()
RING = 4096
i0, ik, ig = struct.unpack_from("<III", d, 0)
print("i0=%d ik=%d ig=%d" % (i0, ik, ig))
def ring(n):
    off = 12 + 8 * RING * n
    return [struct.unpack_from("<II", d, off + 8 * k) for k in range(RING)]
def kor(code):
    if 0x4000 <= code < 0x4000 + 2445:
        idx = code - 0x4000
        if idx < 2350:
            b0 = 0xB0 + idx // 94; b1 = 0xA1 + idx % 94
            try: return bytes([b0, b1]).decode('euc_kr')
            except: return '?'
        else:
            return chr(0x20 + (idx - 2350))
    return None
g = ring(2)
# print last 200 calls in order
n = min(ig, RING)
start = (ig - 200) % RING if ig >= 200 else 0
print("=== last %d glyph calls ===" % min(200, ig))
seq = []
for j in range(200):
    a, b = g[(ig - 200 + j) % RING]
    if a == 0: continue
    k = kor(a)
    seq.append((a, k))
    print("%04X %s ctx=%08X" % (a, k if k else '.', b))
# summarize non-hangul codes
from collections import Counter
cnt = Counter()
for a, b in g:
    if a == 0: continue
    if not (0x4000 <= a < 0x4000 + 2350):
        cnt[a] += 1
print("\n=== non-hangul glyph codes (counter) ===")
for a, c in cnt.most_common(40):
    print("%04X x%d" % (a, c))
