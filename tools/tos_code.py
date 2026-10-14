import capstone, sys
tos = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
d = open(tos,"rb").read()
off = 0x17A81C
base = 0x400000 + off
print("=== TOS.exe @ file 0x%X (VA ~0x%X) with context ===" % (off, base))
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for ins in md.disasm(d[off-64:off+96], base-64):
    tag = "  <== AOB" if ins.address==base else ""
    print("  %08X  %-7s %s%s" % (ins.address, ins.mnemonic, ins.op_str, tag))
