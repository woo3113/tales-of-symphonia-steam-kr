import pefile, struct, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
BAK=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\TOS.exe.bak"
NEWVA=0x2AFF000
SECNAME=b".krlog\x00\x00"
BUFSIZE=0x3F0000

def align(v,a): return (v+a-1)&~(a-1)

pe=pefile.PE(TOS)
img=pe.OPTIONAL_HEADER.ImageBase
D=bytearray(pe.__data__)
# cave
cave_va=NEWVA
IDX=NEWVA+0x40
BUF=NEWVA+0x100
END=BUF+BUFSIZE
def imm32(v): return struct.pack("<I", v)
code=bytearray()
def emit(b): code.extend(b)
emit(b"\x52")                       # push edx
emit(b"\x51")                       # push ecx
emit(b"\x8B\x15"+imm32(IDX))        # mov edx,[IDX]
emit(b"\x81\xFA"+imm32(END))        # cmp edx,END
emit(b"\x73\x12")                   # jae done
emit(b"\x89\x02")                   # mov [edx],eax
emit(b"\x8B\x4C\x24\x08")           # mov ecx,[esp+8]  (return addr)
emit(b"\x89\x4A\x04")               # mov [edx+4],ecx
emit(b"\x83\xC2\x08")               # add edx,8
emit(b"\x89\x15"+imm32(IDX))        # mov [IDX],edx
emit(b"\x59")                       # done: pop ecx
emit(b"\x5A")                       # pop edx
emit(b"\x66\x3D\x5E\x00")           # cmp ax,0x5E
emit(b"\x75\x06")                   # jne L
emit(b"\xB8\xA7\x81\x00\x00")       # mov eax,0x81A7
emit(b"\xC3")                       # ret
jmp_next=cave_va+len(code)+5
emit(b"\xE9"+imm32((0x57A81C-jmp_next)&0xFFFFFFFF))  # L: jmp 0x57A81C
print("cave len", len(code))
# hook at 0x57A810
def va2off(v):
    r=v-img
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
h=va2off(0x57A810)
rel=(cave_va-((img+0x57A810)+5))&0xFFFFFFFF
D[h:h+6]=b"\xE9"+imm32(rel)+b"\x90"
print("hook bytes:", D[h:h+6].hex())
# append new section raw at end
raw_off=len(D)
fileva=pe.OPTIONAL_HEADER.SizeOfImage
secva=align(max(NEWVA, fileva),0x1000)
raw_ptr=align(len(D),0x200)
secsize=align(0x100+BUFSIZE,0x1000)
# pad file to raw_ptr
if raw_ptr>len(D): D.extend(b"\x00"*(raw_ptr-len(D)))
secdata=bytearray(secsize)
secdata[0:len(code)]=code
struct.pack_into("<I", secdata, 0x40, BUF)  # IDX = BUF
D.extend(secdata)
# add section header
nsec=pe.FILE_HEADER.NumberOfSections
sec_table=0x18+pe.FILE_HEADER.SizeOfOptionalHeader
hdr_off=sec_table+40*nsec
name8=SECNAME[:8]
hdr=name8+struct.pack("<IIIIIIHHI", secsize, secva, secsize, raw_ptr, 0,0,0,0, 0xE0000020)
D[hdr_off:hdr_off+40]=hdr
# update NumberOfSections & SizeOfImage
struct.pack_into("<H", D, 0x18-0x18+0x06, nsec+1)   # FILE_HEADER.NumberOfSections at offset 0x06
struct.pack_into("<I", D, 0x18+0x38, align(secva+secsize,0x1000))  # SizeOfImage at optional header offset 0x38
open(TOS,"wb").write(D)
print("new section:", name8, hex(secva), "raw", hex(raw_ptr), "size", hex(secsize))
print("cave_va", hex(cave_va), "BUF", hex(BUF))
print("file size", len(D))
