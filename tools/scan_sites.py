import pefile, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe = pefile.PE(TOS); D = pe.__data__; IMG = pe.OPTIONAL_HEADER.ImageBase

secs = [(s.Name.rstrip(b"\x00").decode("latin1"), IMG + s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]


def va2off(v):
    r = v - IMG
    for n, va, vs, pr, sr in secs:
        if va <= v < va + max(vs, sr):
            return pr + (v - va)
    return None


def exec_ranges():
    out = []
    for n, va, vs, pr, sr in secs:
        if n in (".text", ".dsstext"):
            out.append((n, va, min(vs, sr) if sr else vs))
    return out


def find(pat, mask=None):
    res = []
    for n, va, size in exec_ranges():
        o = va2off(va)
        seg = D[o:o + size]
        i = 0
        L = len(pat)
        while True:
            i = seg.find(pat, i)
            if i < 0:
                break
            res.append((n, va + i))
            i += 1
    return res


print("=== converter copies (B9 80 00 00 00 66 3B C1) ===")
conv = find(b"\xB9\x80\x00\x00\x00\x66\x3B\xC1")
for n, va in conv:
    print("   %-9s %08X" % (n, va))

print()
print("=== length-rule sites (8D xx FF 7E 00 00 ... 66 3B / BA FE 00 00 00) ===")
sites = []
for n, va, size in exec_ranges():
    o = va2off(va)
    seg = D[o:o + size]
    k = 0
    while k + 12 < len(seg):
        if seg[k] == 0x8D and seg[k + 2] == 0xFF and seg[k + 3] == 0x7E and seg[k + 4] == 0x00 and seg[k + 5] == 0x00:
            modrm = seg[k + 1]
            mod = modrm >> 6
            rm = modrm & 7
            if mod == 0x2 and rm != 4:
                # look for mov edx,0xFE and cmp ax,dx within next 20 bytes
                tail = seg[k + 6:k + 24]
                if b"\xBA\xFE\x00\x00\x00" in tail and b"\x66\x3B" in tail:
                    sites.append((n, va + k, rm))
        k += 1
print("   count", len(sites))
for n, va, rm in sites:
    print("   %-9s %08X  reg=%d" % (n, va, rm))
