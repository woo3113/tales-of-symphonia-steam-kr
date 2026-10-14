import pefile, struct, os, hashlib, subprocess, time, ctypes, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
BAK=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work\TOS.exe.bak"
EXPECT="01cad33820c383b938452acb60eed21262152b9f85f29bfbbcee04d51d3a7104"
GAME=os.path.dirname(TOS)
k32=ctypes.WinDLL("kernel32", use_last_error=True)
def align(v,a): return (v+a-1)&~(a-1)
def build(newva):
    with open(BAK,"rb") as _b: _d=_b.read()
    with open(TOS,"wb") as _f: _f.write(_d)
    pe=pefile.PE(TOS); img=pe.OPTIONAL_HEADER.ImageBase; D=bytearray(pe.__data__)
    e=struct.unpack_from("<I",D,0x3C)[0]
    IDX=newva+0x40; BUF=newva+0x100; BUFSIZE=0x3F0000; END=BUF+BUFSIZE
    def I(v): return struct.pack("<I", v & 0xFFFFFFFF)
    cave=bytearray(); c=lambda b: cave.extend(b)
    c(b"\x52\x51"); c(b"\x8B\x15"+I(IDX)); c(b"\x81\xFA"+I(END))
    jp=len(cave); c(b"\x73\x00")
    c(b"\x89\x02"); c(b"\x8B\x4C\x24\x08"); c(b"\x89\x4A\x04"); c(b"\x83\xC2\x08"); c(b"\x89\x15"+I(IDX))
    done=len(cave); c(b"\x59\x5A"); c(b"\x66\x3D\x5E\x00"); c(b"\x75\x06"); c(b"\xB8\xA7\x81\x00\x00\xC3")
    L=len(cave); c(b"\xE9\x00\x00\x00\x00")
    cave[jp+1]=(done-(jp+2))&0xFF
    struct.pack_into("<i", cave, L+1, 0x57A81C-(newva+L+5))
    def va2off(v):
        r=v-img
        for s in pe.sections:
            if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+(r-s.VirtualAddress)
    h=va2off(0x57A810); D[h:h+6]=b"\xE9"+I(newva-((img+0x57A810)+5))+b"\x90"
    raw_ptr=align(len(D),0x200); secsize=align(0x100+BUFSIZE,0x1000)
    if raw_ptr>len(D): D.extend(b"\x00"*(raw_ptr-len(D)))
    sd=bytearray(secsize); sd[:len(cave)]=cave; struct.pack_into("<I",sd,0x40,BUF); D.extend(sd)
    nsec=pe.FILE_HEADER.NumberOfSections; st=e+24+pe.FILE_HEADER.SizeOfOptionalHeader
    D[st+40*nsec:st+40*nsec+40]=b".krlog\x00\x00"+struct.pack("<IIIIIIHHI",secsize,newva,secsize,raw_ptr,0,0,0,0,0xE0000020)
    struct.pack_into("<H",D,e+6,nsec+1); struct.pack_into("<I",D,e+24+0x38,align(newva+secsize,0x1000))
    pe.close(); tmp=TOS+".new"; open(tmp,"wb").write(bytes(D)); os.replace(tmp,TOS)
def tryone(va):
    build(va)
    p=subprocess.Popen([TOS],cwd=GAME)
    h=k32.OpenProcess(0x410,False,p.pid)
    time.sleep(9)
    buf=(ctypes.c_char*6)(); n=ctypes.c_size_t(0)
    ok=k32.ReadProcessMemory(h,ctypes.c_void_p(va),buf,6,ctypes.byref(n))
    print("VA 0x%08X: launch ok, cave in mem=%s bytes=%s"%(va, bool(ok), buf.raw.hex() if ok else None))
    k32.CloseHandle(h); p.terminate(); time.sleep(1)
for va in [0x2B00000,0x2E04000,0x10000000,0x40000000]:
    try:
        tryone(va)
    except Exception as ex:
        print("VA 0x%08X: launch FAILED: %s"%(va, ex))
    with open(BAK,"rb") as _b: _d=_b.read()
    with open(TOS,"wb") as _f: _f.write(_d)
print("restored original")
