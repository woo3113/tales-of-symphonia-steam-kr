"""Build kf13/page_XX.dds (768x576 DXT5, mips=3) from kf13/page_XX.png."""
import os, subprocess, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KF = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\kf13"
REF = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\FONTTYPEC_PIC015.dds"
ref = open(REF, "rb").read(128)
print("ref header size", len(ref), "flags", hex(struct.unpack_from('<I', ref, 8)[0]))


def dxt5(png, W, H, tmp):
    subprocess.run(["magick", png, "-resize", "%dx%d!" % (W, H), "-define", "dds:compression=dxt5", tmp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return open(tmp, "rb").read()[128:]


tmp = os.path.join(KF, "_t.dds")
n = 0
for i in range(13):
    png = os.path.join(KF, "page_%02d.png" % i)
    if not os.path.exists(png):
        print("missing", png); continue
    d0 = dxt5(png, 768, 576, tmp)
    d1 = dxt5(png, 384, 288, tmp)
    d2 = dxt5(png, 192, 144, tmp)
    out = ref + d0 + d1 + d2
    op = os.path.join(KF, "page_%02d.dds" % i)
    open(op, "wb").write(out)
    n += 1
    print("page_%02d.dds mip %d/%d/%d total=%d" % (i, len(d0), len(d1), len(d2), len(out)))
print("built", n, "dds")
