import pefile, capstone, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pe=pefile.PE(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\korfnt\korfnt.dll"); D=pe.__data__; IMG=0x10000000
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+(r-s.VirtualAddress)
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData: return IMG+s.VirtualAddress+(o-s.PointerToRawData)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
print("=== 0x10001F80 full ===")
o=va2off(0x10001F80); c=0
for ins in md.disasm(D[o:o+0x150], 0x10001F80):
    print("  %08X  %-16s %s"%(ins.address,ins.bytes.hex(),ins.mnemonic+' '+ins.op_str)); c+=1
    if c>=110: break
print("\n=== xrefs to globals ===")
for g in [0x1003CB30,0x1003CB28,0x1003CB2C,0x1003CB20]:
    t=struct.pack("<I",g); hits=[off2va(i) for i in range(len(D)-4) if D[i:i+4]==t]
    print("  0x%X refs=%s"%(g,[hex(h) for h in hits[:12]]))
