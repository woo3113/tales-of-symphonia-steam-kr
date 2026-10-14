import capstone, struct, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
d = open(TOS, "rb").read()
BASE = 0x400000
def off(va): return va-BASE
def va(o): return o+BASE

# 1) dump table at 0x8AD868 (256 u16) and 0x8AD7B0
print("=== table[0x8AD868] (256 x u16) ===")
for i in range(0,256,16):
    row=[struct.unpack_from("<H", d, off(0x8AD868)+2*(i+j))[0] for j in range(16)]
    print("  %02X: %s" % (i, " ".join("%04X"%v for v in row)))
print("=== table[0x8AD7B0] (u32 ptrs, first 20) ===")
for i in range(20):
    v=struct.unpack_from("<I", d, off(0x8AD7B0)+4*i)[0]
    print("   [%d] %08X"%(i,v))

# 2) callers of 0x57A810 (E8 rel32)
print("=== callers of 0x57A810 ===")
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
text_lo=0x401000
found=[]
targets={0x57A810:"ConvChar"}
for o in range(0, len(d)-5):
    if d[o]==0xE8:
        rel=struct.unpack_from("<i", d, o+1)[0]
        tgt=va(o)+5+rel
        if tgt in targets:
            found.append(va(o))
print("  count", len(found), [hex(x) for x in found[:20]])

# 3) font symbols in strings
print("=== font/glyph strings in TOS.exe ===")
ss=set()
for m in re.finditer(rb"[\x20-\x7e\x80-\xff]{5,}", d):
    s=m.group()
    try: t=s.decode("shift_jis")
    except: continue
    if re.search(r"(font|FONT|Font|glyph|Glyph|TLFNT|TexBank|Char_get|DrawFont|GetChar|Fnt)", t):
        if not re.search(r"(boost|ERROR_|D3DERR|DWRITE|CRYPT|xpressive|\.cpp|source\\\\)", t):
            ss.add(t)
for s in sorted(ss)[:80]:
    print("   ", s)
