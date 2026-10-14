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
def find_start(v):
    o=va2off(v)
    for back in range(0, 0x600):
        if D[o-back]==0xCC and D[o-back-1]==0xCC:
            return off2va(o-back+1)
    return v-0x40
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(v,n=80):
    st=find_start(v); o=va2off(st)
    print("=== from 0x%X ==="%st)
    c=0
    for ins in md.disasm(D[o:o+n*8], st):
        print("  %08X  %-14s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str)); c+=1
        if c>=n: break
dis(0x10002B90, 70)
dis(0x10002C1F, 40)
