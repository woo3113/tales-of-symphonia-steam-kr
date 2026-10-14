import pefile, capstone, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pe=pefile.PE(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"); D=pe.__data__; base=0x400000
def o(v): return v-base
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va,n):
    print("=== 0x%X ==="%va); c=0
    for ins in md.disasm(D[o(va):o(va)+n*10], va):
        print("  %08X  %-16s %s"%(ins.address, ins.bytes.hex(), ins.mnemonic+' '+ins.op_str)); c+=1
        if c>=n: break
# loop A around 0x4D77C4 (uses movzx eax,byte[edi+esi] @0x4D77E0)
dis(0x4D77B8, 40)
# loop B around 0x4D783A (movsx ax,byte[edi+esi] @0x4D783A)
dis(0x4D787F, 34)
# loop C around 0x4D7C86 (movsx ax,byte[esi+edi] @0x4D7C86)
dis(0x4D7CB8, 40)
