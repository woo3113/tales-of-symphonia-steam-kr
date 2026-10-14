import pefile, capstone, sys, os

BASE = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"

def off_to_va(pe, off):
    for s in pe.sections:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return s.VirtualAddress + (off - s.PointerToRawData)
    return None

def va_to_off(pe, va):
    for s in pe.sections:
        if s.VirtualAddress <= va < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (va - s.VirtualAddress)
    return None

def find_bytes(pe, needle):
    data = pe.__data__
    res = []; start = 0
    while True:
        i = data.find(needle, start)
        if i < 0: break
        res.append(i); start = i+1
    return res

def xrefs(pe, full_va, limit=8):
    out = []
    for off in find_bytes(pe, full_va.to_bytes(4, "little")):
        va = off_to_va(pe, off)
        out.append((off, va))
    return out[:limit]

def disas(pe, va, count=40):
    off = va_to_off(pe, va)
    if off is None:
        print("   (no offset)"); return
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    base = pe.OPTIONAL_HEADER.ImageBase + va
    data = pe.__data__[off: off+count*8]
    n = 0
    for ins in md.disasm(data, base):
        print("   %08X  %-7s %s" % (ins.address, ins.mnemonic, ins.op_str))
        n += 1
        if n >= count: break

def main():
    rel = sys.argv[1]
    pe = pefile.PE(os.path.join(BASE, rel))
    img = pe.OPTIONAL_HEADER.ImageBase
    mode = sys.argv[2]
    if mode == "str":
        for t in sys.argv[3:]:
            for enc, lab in [(t.encode("latin1"), "A"), (t.encode("utf-16-le"), "W")]:
                for off in find_bytes(pe, enc)[:2]:
                    va = off_to_va(pe, off)
                    print("### '%s' %s VA=%X full=%X" % (t, lab, va, img+va))
                    for xoff, xva in xrefs(pe, img+va):
                        print("  xref VA=%X" % xva)
                        if xva: disas(pe, xva-40, 12)
    elif mode == "va":
        for a in sys.argv[3:]:
            va = int(a, 16)
            print("### disasm VA=%X" % va)
            disas(pe, va, 60)
    pe.close()

main()
