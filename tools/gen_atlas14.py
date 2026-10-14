"""Generate the extended glyph atlas (kf14): hangul(2350) + ASCII(95) + EUC-KR
symbols rows A1..A3 (282). Pages 0..12 must byte-match the verified kf13 atlas."""
import os, math, sys
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf14"
os.makedirs(OUT, exist_ok=True)

HAN_N = 2350          # idx 0..2349  (EUC-KR 0xB0A1..0xC8FE)
ASCII_BASE = 2350     # idx 2350..2444
SYM_BASE = 2445       # idx 2445..2726 (EUC-KR rows 0xA1..0xA3)
SYM_ROWS = [0xA1, 0xA2, 0xA3]
TOTAL = SYM_BASE + len(SYM_ROWS) * 94       # 2727

FONT = r"C:\Windows\Fonts\malgun.ttf"
COLS, ROWS, CELL = 16, 12, 48
PW, PH = COLS * CELL, ROWS * CELL
PER = COLS * ROWS


def glyph_char(g):
    if g < HAN_N:
        b0 = 0xB0 + g // 94; b1 = 0xA1 + g % 94
        return bytes([b0, b1]).decode("euc_kr")
    if g < SYM_BASE:
        return chr(0x20 + (g - ASCII_BASE))
    k = g - SYM_BASE
    b0 = SYM_ROWS[k // 94]; b1 = 0xA1 + k % 94
    try:
        return bytes([b0, b1]).decode("euc_kr")
    except Exception:
        return None


font = ImageFont.truetype(FONT, 40)
npages = math.ceil(TOTAL / PER)
print("total glyphs", TOTAL, "pages", npages, "height", (2 + npages) * PH)
for p in range(npages):
    img = Image.new("RGBA", (PW, PH), (255, 255, 255, 0))
    dr = ImageDraw.Draw(img)
    for k in range(PER):
        gi = p * PER + k
        if gi >= TOTAL:
            break
        ch = glyph_char(gi)
        if not ch:
            continue
        c = k % COLS; r = k // COLS
        bbox = dr.textbbox((0, 0), ch, font=font)
        w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
        dr.text((c * CELL + (CELL - w) / 2 - bbox[0], r * CELL + (CELL - h) / 2 - bbox[1]),
                ch, font=font, fill=(255, 255, 255, 255))
    img.save(os.path.join(OUT, "page_%02d.png" % p))
print("saved to", OUT)

# verify pages 0..12 against kf13
KF13 = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf13"
bad = 0
for p in range(13):
    a = Image.open(os.path.join(OUT, "page_%02d.png" % p)).convert("RGBA")
    b = Image.open(os.path.join(KF13, "page_%02d.png" % p)).convert("RGBA")
    if a.tobytes() != b.tobytes():
        print("  MISMATCH page", p); bad += 1
print("verify vs kf13: %s" % ("ALL MATCH" if not bad else "%d differ" % bad))
