import struct, os, sys, glob, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
# DDS parse (correct offsets)
def dds_info(p):
    d=open(p,"rb").read()
    assert d[:4]==b"DDS "
    h,w=struct.unpack_from("<II",d,0x0C)
    mips=struct.unpack_from("<I",d,0x1C)[0]
    pf_off=0x4C
    pfsize,pfflags,fourcc,rgbbits=struct.unpack_from("<IIII",d,pf_off)
    rmask,gmask,bmask,amask=struct.unpack_from("<IIII",d,pf_off+16)
    return dict(h=h,w=w,mips=mips,pfsize=pfsize,pfflags=hex(pfflags),fourcc=fourcc,rgbbits=rgbbits,rmask=hex(rmask),gmask=hex(gmask),bmask=hex(bmask),amask=hex(amask),size=len(d))
for f in ["PAL_FONTB0.dds","FONTTYPEC_PIC015.dds","SYSTEM_PIC000.dds"]:
    p=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\%s"%f
    if os.path.exists(p): print(f, dds_info(p))
print("--- korfnt_0.dds ---")
print(dds_info(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\korfnt_0.dds"))
print("\n--- Korean fonts available ---")
for d in [r"C:\Windows\Fonts"]:
    for f in sorted(glob.glob(d+r"\*.tt*")):
        n=os.path.basename(f)
        if re.search(r"(malgun|gulim|batang|dotum|gungsuh|nanum|noto.*kr|segoe)", n, re.I):
            print("  ", n)
