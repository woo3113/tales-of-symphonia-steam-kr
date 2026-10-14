import pefile, capstone, sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS); D=pe.__data__; IMG=0x400000
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData:
            return IMG+s.VirtualAddress+(o-s.PointerToRawData)
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va,n=120):
    o=va2off(va); c=0
    for ins in md.disasm(D[o:o+n*8], va):
        print("  %08X  %-8s %s"%(ins.address,ins.mnemonic,ins.op_str)); c+=1
        if c>=n: break
print("=== 0x612DA0 (TL resource loader) ===")
dis(0x612DA0, 130)
# find DPDF imm compare location
b=struct.pack("<I",0x46445044)
hits=[off2va(x) for x in range(len(D)-4) if D[x:x+4]==b]
print("DPDF imm at VA:", [hex(h) for h in hits])
