import pefile, capstone, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS); D=pe.__data__; IMG=0x400000
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va,n=80):
    o=va2off(va); c=0
    for ins in md.disasm(D[o:o+n*8], va):
        print("  %08X  %-8s %s"%(ins.address,ins.mnemonic,ins.op_str)); c+=1
        if c>=n: break
print("=== strings 0x87CA00..0x87CB40 ===")
o=va2off(0x87CA00)
seg=D[o:va2off(0x87CB40)]
for m in re.finditer(rb"[\x20-\x7e]{2,}", seg):
    print("   0x%08X %s"%(0x400000+ (0x87CA00-0x400000)+m.start(), m.group().decode('latin1')))
print("=== font bank parser 0x614120 ===")
dis(0x614120, 90)
print("=== 0x614210 ===")
dis(0x614210, 60)
