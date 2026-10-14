import pefile, struct, os, hashlib, sys, capstone
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
WORK=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
EXPECT="01cad33820c383b938452acb60eed21262152b9f85f29bfbbcee04d51d3a7104"
cur=hashlib.sha256(open(TOS,"rb").read()).hexdigest()
print("current sha256", cur)
assert cur==EXPECT, "TOS.exe is not the known original!"
pe=pefile.PE(TOS); img=pe.OPTIONAL_HEADER.ImageBase
D=bytearray(pe.__data__)
e_lfanew=struct.unpack_from("<I",D,0x3C)[0]
def align(v,a): return (v+a-1)&~(a-1)
NEWVA=0x2AFF000
IDX=NEWVA+0x40; BUF=NEWVA+0x100; BUFSIZE=0x3F0000; END=BUF+BUFSIZE
def imm32(v): return struct.pack("<I", v & 0xFFFFFFFF)
cave=bytearray()
def E(b): cave.extend(b)
E(b"\x52\x51")
E(b"\x8B\x15"+imm32(IDX))
E(b"\x81\xFA"+imm32(END))
jae_pos=len(cave); E(b"\x73\x00")
E(b"\x89\x02")
E(b"\x8B\x4C\x24\x08")
E(b"\x89\x4A\x04")
E(b"\x83\xC2\x08")
E(b"\x89\x15"+imm32(IDX))
done=len(cave); E(b"\x59\x5A")
E(b"\x66\x3D\x5E\x00")
E(b"\x75\x06")
E(b"\xB8\xA7\x81\x00\x00\xC3")
L=len(cave)
E(b"\xE9\x00\x00\x00\x00")
cave[jae_pos+1]=(done-(jae_pos+2))&0xFF
struct.pack_into("<i", cave, L+1, (0x57A81C-(NEWVA+L+5)))
print("cave len", len(cave), "done", done, "L", L, "jae", cave[jae_pos+1])
# disasm verify
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for ins in md.disasm(bytes(cave), NEWVA):
    print("  %08X  %-7s %s"%(ins.address,ins.mnemonic,ins.op_str))
# hook
def va2off(v):
    r=v-img
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
h=va2off(0x57A810)
D[h:h+6]=b"\xE9"+imm32(NEWVA-((img+0x57A810)+5))+b"\x90"
# build section
raw_ptr=align(len(D),0x200)
secva=NEWVA
secsize=align(0x100+BUFSIZE,0x1000)
if raw_ptr>len(D): D.extend(b"\x00"*(raw_ptr-len(D)))
sd=bytearray(secsize); sd[:len(cave)]=cave; struct.pack_into("<I", sd, 0x40, BUF)
D.extend(sd)
nsec=pe.FILE_HEADER.NumberOfSections
sec_table=e_lfanew+24+pe.FILE_HEADER.SizeOfOptionalHeader   # == 0xF8
hdr_off=sec_table+40*nsec
D[hdr_off:hdr_off+40]=b".krlog\x00\x00"+struct.pack("<IIIIIIHHI", secsize, secva, secsize, raw_ptr, 0,0,0,0, 0xE0000020)
struct.pack_into("<H", D, e_lfanew+6, nsec+1)                      # NumberOfSections
struct.pack_into("<I", D, e_lfanew+24+0x38, align(secva+secsize,0x1000))  # SizeOfImage
pe.close()
tmp=TOS+".new"
with open(tmp,"wb") as f: f.write(bytes(D))
os.replace(tmp, TOS)
print("patched. section", hex(secva), "raw", hex(raw_ptr), "size", hex(secsize), "file", len(D))
# verify with pefile
pe2=pefile.PE(TOS)
print("sections:", [(s.Name.rstrip(b'\x00').decode('latin1'), hex(s.VirtualAddress)) for s in pe2.sections])
print("SizeOfImage", hex(pe2.OPTIONAL_HEADER.SizeOfImage))
