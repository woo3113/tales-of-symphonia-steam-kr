import capstone, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
d = open(TOS, "rb").read()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

def va2off(va, base=0x400000):
    return va - base

def dis(va, n, base=0x400000):
    off = va2off(va, base)
    for ins in md.disasm(d[off:off+n*8], va):
        print("  %08X  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))

print("=== full function containing 0x57A81C (start ~0x57A7E3 boundary) ===")
dis(0x57A7E3, 70)
