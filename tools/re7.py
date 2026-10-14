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
def dis(va,n=90):
    o=va2off(va); c=0
    for ins in md.disasm(D[o:o+n*8], va):
        print("  %08X  %-8s %s"%(ins.address,ins.mnemonic,ins.op_str)); c+=1
        if c>=n: break
# function start before 0x612dcb
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData:
            return IMG+s.VirtualAddress+(o-s.PointerToRawData)
i=va2off(0x612dcb); j=D.rfind(b'\x55\x8b\xec', max(0,i-400), i)
print("prologue near", hex(off2va(j)) if j>=0 else None)
o=va2off(0x612c80)
print("=== font loader around 0x612C80 ===")
dis(0x612C80, 120)
print("\n=== immediate magics ===")
import struct
for name,val in [("DPDF",0x46445044),("TLZC",0x435A4C54),("TOTEXB",0x42584554)]:
    b=struct.pack("<I", val)
    hits=[x for x in range(len(D)-4) if D[x:x+4]==b]
    print("  %s (0x%08X) imm occurrences: %d"%(name,val,len(hits)))
