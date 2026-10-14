import pefile, capstone, sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe = pefile.PE(TOS); D = pe.__data__; IMG = 0x400000
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True

def va2off(v):
    r = v - IMG
    for s in pe.sections:
        if s.VirtualAddress <= r < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (r - s.VirtualAddress)
    return None

sections = [(s.Name.rstrip(b'\x00').decode('latin1'), IMG + s.VirtualAddress,
             IMG + s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData),
             s.PointerToRawData, max(s.Misc_VirtualSize, s.SizeOfRawData)) for s in pe.sections]

def find_calls(target):
    res = []
    lo, hi = 0x401000, 0x700000
    base = va2off(lo)
    buf = D[base:base + (hi - lo)]
    for i in range(len(buf) - 5):
        if buf[i] == 0xE8:
            rel = struct.unpack_from('<i', buf, i + 1)[0]
            va = lo + i
            if (va + 5 + rel) & 0xFFFFFFFF == target:
                res.append(va)
    return res

def find_addr_refs(target):
    """find instructions that reference immediate 32-bit address target"""
    res = []
    lo, hi = 0x401000, 0x700000
    base = va2off(lo)
    buf = D[base:base + (hi - lo)]
    t = struct.pack('<I', target)
    i = 0
    while True:
        i = buf.find(t, i)
        if i < 0: break
        res.append(lo + i)
        i += 1
    return res

if __name__ == "__main__":
    mode = sys.argv[1]
    tgt = int(sys.argv[2], 16)
    if mode == 'call':
        for a in find_calls(tgt): print("call %08X -> %08X" % (a, tgt))
    else:
        for a in find_addr_refs(tgt): print("addrref %08X" % a)
