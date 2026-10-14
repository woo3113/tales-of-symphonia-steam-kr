import pefile, struct, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS); D=pe.__data__; IMG=0x400000
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
d=struct.unpack_from("<d", D, va2off(0x882A30))[0]
f=struct.unpack_from("<f", D, va2off(0x882960))[0]
g=struct.unpack_from("<I", D, va2off(0xB18F9C))[0]
print("K(double@0x882A30) = %.10f  (1/16=%.10f)"%(d,1/16))
print("float@0x882960 = %.3f"%f)
print("global@0xB18F9C = 0x%08X"%g)
# per-cell occupancy of PAL_FONTB0 alpha
raw=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\pal_a.raw"
if os.path.exists(raw):
    b=open(raw,"rb").read()
    W,H=768,1728
    print("alpha bytes", len(b), "expected", W*H)
    cols,rows=16,36
    cw,ch=W//cols, H//rows
    print("cell %dx%d"%(cw,ch))
    empty=[]
    for r in range(rows):
        line=""
        for c in range(cols):
            s=0;n=0
            for y in range(r*ch+8, r*ch+ch-8, 4):
                base=y*W+c*cw
                for x in range(c*cw+8, c*cw+cw-8, 4):
                    s+=b[base+x]; n+=1
            avg=s/max(n,1)
            line += "." if avg<6 else ("+" if avg<40 else "#")
            if avg<6: empty.append((c,r))
        print("  %02d %s"%(r,line))
    print("empty cells:", len(empty), "of", cols*rows)
else:
    print("run: magick PAL_FONTB0.dds -alpha extract -depth 8 gray:pal_a.raw")
