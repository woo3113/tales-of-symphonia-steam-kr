"""Create 13 identical solid-opaque-magenta 768x576 DXT5 pages in work/mag."""
import os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
REF = os.path.join(WORK, "FONTTYPEC_PIC015.dds")
ref = open(REF, "rb").read(128)
MAG = os.path.join(WORK, "mag")
os.makedirs(MAG, exist_ok=True)
png = os.path.join(MAG, "mag.png")
subprocess.run(["magick", "-size", "768x576", "xc:rgb(255,0,255)", png], check=True)
tmp = os.path.join(MAG, "_t.dds")


def dxt5(p, W, H):
    subprocess.run(["magick", p, "-resize", "%dx%d!" % (W, H), "-define", "dds:compression=dxt5", tmp], check=True)
    return open(tmp, "rb").read()[128:]


page = ref + dxt5(png, 768, 576) + dxt5(png, 384, 288) + dxt5(png, 192, 144)
assert len(page) == 580736, len(page)
for i in range(13):
    open(os.path.join(MAG, "page_%02d.dds" % i), "wb").write(page)
print("wrote 13 magenta pages", len(page))
