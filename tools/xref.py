import pefile, capstone, sys, os

BASE = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"

def va_to_off(pe, va):
    for s in pe.sections:
        if s.VirtualAddress <= va < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (va - s.VirtualAddress)
    return None

def off_to_va(pe, off):
    for s in pe.sections:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return s.VirtualAddress + (off - s.PointerToRawData)
    return None

def find_bytes(pe, needle):
    data = pe.__data__
    res = []
    start = 0
    while True:
        i = data.find(needle, start)
        if i < 0: break
        res.append(i)
        start = i+1
    return res

def xrefs_to_va(pe, va):
    needle = va.to_bytes(4, "little")
    hits = find_bytes(pe, needle)
    return [(off, off_to_va(pe, off)) for off in hits]

def disas(pe, va, before=0, count=40):
    off = va_to_off(pe, va)
    if off is None: return
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = False
    base = pe.OPTIONAL_HEADER.ImageBase + va
    data = pe.__data__[off: off+400]
    for ins in md.disasm(data, base):
        print("  %08X  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
        count -= 1
        if count <= 0: break

def main():
    rel = sys.argv[1]
    pe = pefile.PE(os.path.join(BASE, rel))
    targets = sys.argv[2:]
    for t in targets:
        tb = t.encode("latin1")
        # find as ascii and wide
        for enc, label in [(tb, "A"), (t.encode("utf-16-le"), "W")]:
            offs = find_bytes(pe, enc)
            for off in offs[:3]:
                va = off_to_va(pe, off)
                print("### string %s (%s) fileoff=%X VA=%X" % (t, label, off, va))
                for xoff, xva in xrefs_to_va(pe, va)[:6]:
                    secoff = off_to_va(pe, xoff)
                    print("  xref at fileoff=%X VAapprox=%X:" % (xoff, secoff))
                    # disasm from a bit before
                    if secoff is not None:
                        disas(pe, secoff - 32, count=14)
    pe.close()

main()
