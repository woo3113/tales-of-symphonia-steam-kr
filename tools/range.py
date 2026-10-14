import pefile, capstone, os, sys
BASE = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
rel = sys.argv[1]
pe = pefile.PE(os.path.join(BASE, rel))
img = pe.OPTIONAL_HEADER.ImageBase
def va2off(va):
    r = va - img
    for s in pe.sections:
        if s.VirtualAddress <= r < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (r - s.VirtualAddress)
    return None
start = int(sys.argv[2],16)
count = int(sys.argv[3]) if len(sys.argv)>3 else 80
off = va2off(start)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
data = pe.__data__[off: off+count*8]
n=0
for ins in md.disasm(data, img+start):
    print("%08X  %-7s %s" % (ins.address, ins.mnemonic, ins.op_str))
    n+=1
    if n>=count: break
