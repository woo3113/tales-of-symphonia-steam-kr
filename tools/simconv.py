import pefile, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe = pefile.PE(TOS); D = pe.__data__; IMG = 0x400000
def va2off(v):
    r = v - IMG
    for s in pe.sections:
        if s.VirtualAddress <= r < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (r - s.VirtualAddress)
    return None
def u16be(v):
    o = va2off(v); return (D[o] << 8) | D[o+1]
TBL = 0x8AD868
def conv(c):
    # replicate 0x57A810 (from A_spec/analysis)
    if c < 0x80:
        return u16be(TBL + c*2)
    if c <= 0xFF:
        return c + 0x8220
    return 0x831F
def glyph(code):
    ax = code & 0xFFFF
    if ax < 0x8140: return None
    if ax < 0x9880:
        if ax < 0x8240: ecx = (ax - 0x8140) & 0xFFFFFFFF; g = 0
        elif ax < 0x8340: ecx = (ax - 0x8240) & 0xFFFFFFFF; g = 1
        elif ax < 0x8840: ecx = (ax - 0x8340) & 0xFFFFFFFF; g = 2
        else:
            e = (ax - 0x8840); e = (e + (0 if e>=0 else 0xff)) >> 8 if False else e
            g = e//256 + 3; ecx = (ax - TABLE_LEN(g)) & 0xFFFFFFFF
        return (ax, g, ecx, ecx & 0xF, (ecx >> 4) + g*12)
    return (ax, 0x13, None, None, None)
for c in [0x20, 0x41, 0x3F, 0x61, 0x74]:
    code = conv(c); print("ascii %02X -> conv %04X -> glyph %s" % (c, code, glyph(code)))
for code in [0xA3BF, 0x8140, 0x831F]:
    print("code %04X -> glyph %s" % (code, glyph(code)))
