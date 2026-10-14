import os, math, sys
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf13"
os.makedirs(OUT, exist_ok=True)
# KS X 1001 Hangul: 0xB0A1..0xC8FE  -> slot = (b0-0xB0)*94 + (b1-0xA1)
entries=[]  # (slot, char, kind)
for b0 in range(0xB0,0xC9):
    for b1 in range(0xA1,0xFF):
        slot=(b0-0xB0)*94+(b1-0xA1)
        try: ch=bytes([b0,b1]).decode("euc_kr")
        except Exception: ch=None
        if ch and 0xAC00<=ord(ch)<=0xD7A3:
            entries.append((slot,ch,"han"))
# ASCII appended after 2350
ascii_base=2350
for i,c in enumerate(range(0x20,0x7F)):
    entries.append((ascii_base+i, chr(c), "ascii"))
print("total glyphs:", len(entries), "hangul:", sum(1 for e in entries if e[2]=="han"), "ascii:", sum(1 for e in entries if e[2]=="ascii"))
FONT=r"C:\Windows\Fonts\malgun.ttf"
COLS,ROWS,CELL=16,12,48; PW,PH=COLS*CELL,ROWS*CELL; PER=COLS*ROWS
font=ImageFont.truetype(FONT,40)
npages=math.ceil(len(entries)/PER)
print("pages:", npages)
by_slot={s:c for s,c,k in entries}
for p in range(npages):
    img=Image.new("RGBA",(PW,PH),(255,255,255,0)); dr=ImageDraw.Draw(img)
    for k in range(PER):
        gi=p*PER+k
        if gi>=len(entries): break
        slot,ch,kind=entries[gi]   # note: slot may not equal gi if gaps; but no gaps here
        c=k%COLS; r=k//COLS
        # for ASCII use slightly smaller glyph maybe; just same
        bbox=dr.textbbox((0,0),ch,font=font); w=bbox[2]-bbox[0]; h=bbox[3]-bbox[1]
        dr.text((c*CELL+(CELL-w)/2-bbox[0], r*CELL+(CELL-h)/2-bbox[1]), ch, font=font, fill=(255,255,255,255))
    img.save(os.path.join(OUT,"page_%02d.png"%p))
print("saved pages to", OUT)
