import pefile, capstone, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pe=pefile.PE(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\korfnt\korfnt.dll"); D=pe.__data__; IMG=0x10000000
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
    return None
o=va2off(0x100025C0)
print("off", o)
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
c=0
for ins in md.disasm(D[o:o+0xC0], 0x100025C0):
    print("%08X  %-16s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str)); c+=1
    if c>=48: break
