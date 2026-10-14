import pefile, capstone, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS); D=pe.__data__; IMG=0x400000
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va,n=60):
    o=va2off(va); c=0
    for ins in md.disasm(D[o:o+n*8], va):
        print("  %08X  %-8s %s"%(ins.address,ins.mnemonic,ins.op_str)); c+=1
        if c>=n: break
print("=== glyph slot calc 0x578680 full ===")
dis(0x578680, 75)
