import pefile, capstone, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pe=pefile.PE(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\korfnt\korfnt.dll"); D=pe.__data__; IMG=0x10000000
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+(r-s.VirtualAddress)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def dis(va,n,label):
    o=va2off(va); print("=== %s 0x%X ==="%(label,va)); c=0
    for ins in md.disasm(D[o:o+n*10], va):
        print("  %08X  %-16s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str)); c+=1
        if c>=n: break
dis(0x10002E20, 55, "mapping")
dis(0x100044e0, 25, "ctx_callback")
# which import is 0x1002e020?
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for i in e.imports:
        if i.address==0x1002e020:
            print("IAT 0x1002e020 =", e.dll.decode(), "!", i.name.decode() if i.name else i.ordinal)
