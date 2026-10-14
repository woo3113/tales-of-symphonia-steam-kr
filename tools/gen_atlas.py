import struct, os, zlib, json, sys
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf"
os.makedirs(OUT, exist_ok=True)
PATCH_TL=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
PATCH_HDR=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB"
ORIG_HDR=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB"
def parse(h):
    d=open(h,"rb").read(); base=40+84385*8; recs=[]
    for i in range((len(d)-base)//40):
        o=base+40*i; fs,cs,off,hv=struct.unpack_from("<QQQI",d,o)
        recs.append(dict(i=i,fs=fs,cs=cs,off=off,hv=hv,ext=d[o+28:o+36].split(b"\x00")[0].decode('latin1')))
    return recs
pl=parse(PATCH_HDR); ol=parse(ORIG_HDR); om={r["hv"]:r for r in ol}
def get(r):
    with open(PATCH_TL,"rb") as f: f.seek(r["off"]); d=f.read(r["cs"])
    return d if r["cs"]==r["fs"] else (zlib.decompress(d[24:],-15) if d[:4]==b"TLZC" else None)

# collect distinct syllables
syl=set()
def scan(b):
    for ch in b.decode("euc_kr","ignore"):
        if 0xAC00<=ord(ch)<=0xD7A3: syl.add(ch)
for r in pl:
    o=om.get(r["hv"])
    if (o and o["fs"]!=r["fs"]) or r["ext"] in ("TXB","CSV"):
        b=get(r)
        if b: scan(b)
sylls=sorted(syl, key=lambda c: c.encode("euc_kr"))
print("distinct syllables:", len(sylls))
slot_of={c:i for i,c in enumerate(sylls)}
json.dump({c:{"code":c.encode("euc_kr").hex(),"slot":i} for c,i in slot_of.items()},
          open(os.path.join(OUT,"mapping.json"),"w",encoding="utf-8"), ensure_ascii=False)
# reverse: code(int) -> slot
code2slot={int.from_bytes(c.encode("euc_kr"),"big"):i for i,c in enumerate(sylls)}
json.dump({str(k):v for k,v in code2slot.items()}, open(os.path.join(OUT,"code2slot.json"),"w"), ensure_ascii=False, indent=0)

FONT=r"C:\Windows\Fonts\malgun.ttf"
COLS,ROWS=16,12; CELL=48; PW,PH=COLS*CELL, ROWS*CELL
PERPAGE=COLS*ROWS
font=ImageFont.truetype(FONT, 40)
def render_page(page_idx):
    img=Image.new("RGBA",(PW,PH),(255,255,255,0))
    dr=ImageDraw.Draw(img)
    for k in range(PERPAGE):
        gi=page_idx*PERPAGE+k
        if gi>=len(sylls): break
        ch=sylls[gi]
        c=k%COLS; r=k//COLS
        x0,y0=c*CELL, r*CELL
        # measure and center
        bbox=dr.textbbox((0,0),ch,font=font)
        w=bbox[2]-bbox[0]; h=bbox[3]-bbox[1]
        px=x0+(CELL-w)/2 - bbox[0]
        py=y0+(CELL-h)/2 - bbox[1]
        dr.text((px,py),ch,font=font,fill=(255,255,255,255))
    return img
npages=(len(sylls)+PERPAGE-1)//PERPAGE
print("pages:", npages)
for p in range(npages):
    img=render_page(p)
    img.save(os.path.join(OUT,"page_%02d.png"%p))
# overview of page0
Image.open(os.path.join(OUT,"page_00.png")).convert("RGB").save(os.path.join(OUT,"page_00_rgb.png"))
print("done. sample chars:", ''.join(sylls[:40]))
