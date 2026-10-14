import pefile, capstone, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pe=pefile.PE(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe")
D=pe.__data__; base=0x400000
def off(v): return v-0x400000
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va,n=28):
    print("=== 0x%X ==="%va)
    c=0
    for ins in md.disasm(D[off(va):off(va)+n*8], va):
        print("  %08X  %-16s %s"%(ins.address, ins.bytes.hex(), ins.mnemonic+' '+ins.op_str)); c+=1
        if c>=n: break
for va in [0x4D77A0,0x4D7820,0x4D7C60,0x532800,0x594CC0,0x554DF0,0x57A980,0x626650]:
    dis(va, 26 if va not in (0x4D7820,0x4D7C60) else 22)
