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
def dis(va, n):
    o = va2off(va)
    for ins in md.disasm(D[o:o + n * 12], va):
        print("  %08X  %-20s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic + ' ' + ins.op_str))
sites = [0x578680]
for s in sites:
    pass
calls = [0x004609B5,0x004D7461,0x004D7A8D,0x00531FAD,0x0054BC2E,0x00553967,0x00554E74,0x005735B4,0x00576269,0x005762F8,0x0057A9E6]
for c in calls:
    print("\n########## call at %08X ##########" % c)
    dis(c - 0x40, 40)
