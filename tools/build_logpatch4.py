import pefile, struct, os, hashlib, sys, capstone
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
EXPECT="01cad33820c383b938452acb60eed21262152b9f85f29bfbbcee04d51d3a7104"
assert hashlib.sha256(open(TOS,"rb").read()).hexdigest()==EXPECT
pe=pefile.PE(TOS); img=pe.OPTIONAL_HEADER.ImageBase
D=bytearray(pe.__data__)
SECVA=0x1A3A000; SECRAW=0x525800
IDX_VA=0x2A7E000; CAVE_VA=0x2A7E010; BUF_VA=0x2A7E100; MASKB=0xFF
def I(v): return struct.pack("<I", v & 0xFFFFFFFF)
def fileoff(va): return SECRAW+(va-SECVA)
cave=bytearray()
def E(b): cave.extend(b)
E(b"\x52")
E(b"\x8B\x15"+I(IDX_VA))
E(b"\x89\x04\xD5"+I(BUF_VA))
E(b"\x8B\x4C\x24\x04")
E(b"\x89\x0C\xD5"+I(BUF_VA+4))
E(b"\x83\xC2\x01")
E(b"\x81\xE2"+I(MASKB))
E(b"\x89\x15"+I(IDX_VA))
E(b"\x5A")
E(b"\x66\x3D\x5E\x00")
E(b"\x75\x06")
E(b"\xB8\xA7\x81\x00\x00\xC3")
L=len(cave); E(b"\xE9\x00\x00\x00\x00")
struct.pack_into("<i", cave, L+1, (0x57A81C-(CAVE_VA+L+5)))
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
print("cave len", len(cave))
for ins in md.disasm(bytes(cave), CAVE_VA):
    print("  %08X  %-7s %s"%(ins.address,ins.mnemonic,ins.op_str))
# write cave into .dsstext area
o=fileoff(CAVE_VA); D[o:o+len(cave)]=cave
struct.pack_into("<I", D, fileoff(IDX_VA), 0)
# hook .text
def va2off(v):
    r=v-img
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
h=va2off(0x57A810)
D[h:h+6]=b"\xE9"+I(CAVE_VA-((img+0x57A810)+5))+b"\x90"
pe.close()
tmp=TOS+".new"; open(tmp,"wb").write(bytes(D)); os.replace(tmp,TOS)
print("patched (in-place .dsstext). hook:", D[h:h+6].hex())
pe2=pefile.PE(TOS); print("sections ok:", len(pe2.sections), "SizeOfImage", hex(pe2.OPTIONAL_HEADER.SizeOfImage))
