"""Build kf17 pages = Hangul KS X 1001 (2350) + ASCII (95) + EUC-KR symbol rows A1..AF (1410).
Positional slots (gi == index sent by the converter stub):
  Hangul  0..2349    : idx=(b0-0xB0)*94+(b1-0xA1)          (b0 B0..C8, b1 A1..FE)
  ASCII   2350..2444 : idx=2350+(c-0x20)                   (c 0x20..0x7E)
  Symbol  2445..3854 : idx=2445+(b0-0xA1)*94+(b1-0xA1)     (b0 A1..AF, b1 A1..FE)
Cell 48px, 16x12 per page."""
import os, math, sys
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
# 사용법: py gen_atlas_free.py <글꼴.ttf> <출력폴더>   (예: NanumGothic.ttf, SIL OFL 무료 글꼴)
FONT = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
COLS, ROWS, CELL = 16, 12, 48
PER = COLS * ROWS
TOTAL = 2445 + 15 * 94          # 3855
NP = math.ceil(TOTAL / PER)     # 21
print("total slots", TOTAL, "pages", NP)

mp = {}   # gi -> char
for b0 in range(0xB0, 0xC9):
    for b1 in range(0xA1, 0xFF):
        gi = (b0 - 0xB0) * 94 + (b1 - 0xA1)
        try:
            ch = bytes([b0, b1]).decode("euc_kr")
        except Exception:
            ch = None
        mp[gi] = ch
for i, c in enumerate(range(0x20, 0x7F)):
    mp[2350 + i] = chr(c)
for b0 in range(0xA1, 0xB0):
    for b1 in range(0xA1, 0xFF):
        gi = 2445 + (b0 - 0xA1) * 94 + (b1 - 0xA1)
        try:
            ch = bytes([b0, b1]).decode("euc_kr")
        except Exception:
            ch = None
        mp[gi] = ch
missing = [g for g in range(TOTAL) if mp.get(g) is None]
print("slots with no char (percent):", len(missing), "e.g.", missing[:20])

font = ImageFont.truetype(FONT, 40)
for p in range(NP):
    img = Image.new("RGBA", (COLS * CELL, ROWS * CELL), (255, 255, 255, 0))
    dr = ImageDraw.Draw(img)
    for k in range(PER):
        gi = p * PER + k
        ch = mp.get(gi)
        if not ch:
            continue
        c = k % COLS; r = k // COLS
        bbox = dr.textbbox((0, 0), ch, font=font)
        w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
        dr.text((c * CELL + (CELL - w) / 2 - bbox[0], r * CELL + (CELL - h) / 2 - bbox[1]),
                ch, font=font, fill=(255, 255, 255, 255))
    img.save(os.path.join(OUT, "page_%02d.png" % p))
print("saved", NP, "pages to", OUT)
