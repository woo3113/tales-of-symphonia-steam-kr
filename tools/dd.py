import pefile, capstone, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe = pefile.PE(TOS); D = pe.__data__; IMG = 0x400000
def va2off(v):
    r = v - IMG
    for s in pe.sections:
        if s.VirtualAddress <= r < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (r - s.VirtualAddress)
    return None
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va, n, label=""):
    o = va2off(va)
    print("=== %s 0x%X ===" % (label, va))
    c = 0
    for ins in md.disasm(D[o:o + n * 12], va):
        print("  %08X  %-20s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic + ' ' + ins.op_str))
        c += 1
        if c >= n: break
if __name__ == "__main__":
    va = int(sys.argv[1], 16); n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    dis(va, n)
