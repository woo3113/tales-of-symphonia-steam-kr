import pefile, capstone, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pe=pefile.PE(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\korfnt\korfnt.dll"); D=pe.__data__; IMG=0x10000000
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+(r-s.VirtualAddress)
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData: return IMG+s.VirtualAddress+(o-s.PointerToRawData)
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(va,n=45):
    o=va2off(va); print("=== handler 0x%X ==="%va); c=0
    for ins in md.disasm(D[o:o+n*10], va):
        print("  %08X  %-16s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str)); c+=1
        if c>=n: break
for h in [0x100020D0,0x10002200,0x10002230,0x10002240]:
    dis(h, 40)
