import ctypes, subprocess, time, struct, sys, os, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
k32=ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_VM_READ=0x10; PROCESS_QUERY_INFORMATION=0x400
IDX_VA=0x2A7E000; CAVE_VA=0x2A7E010; BUF_VA=0x2A7E100; N=256
p=subprocess.Popen([os.path.join(GAME,"TOS.exe")], cwd=GAME)
print("pid", p.pid)
h=k32.OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION, False, p.pid)
def rd(addr,size):
    buf=(ctypes.c_char*size)(); n=ctypes.c_size_t(0)
    return buf.raw if k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(n)) else None
for t in range(6):
    time.sleep(5)
    cv=rd(CAVE_VA,8); idx=rd(IDX_VA,4)
    ex=ctypes.c_ulong(); k32.GetExitCodeProcess(h, ctypes.byref(ex))
    print("t=%ds exit=%d cave=%s idx=%s"%(5*(t+1), ex.value, cv.hex() if cv else None, hex(struct.unpack('<I',idx)[0]) if idx else None))
    if ex.value!=259: break
idx=rd(IDX_VA,4)
if idx:
    i=struct.unpack("<I",idx)[0]
    data=rd(BUF_VA, N*8)
    codes=collections.Counter(); callers=collections.Counter(); allc=[]
    if data:
        for k in range(N):
            c,r=struct.unpack_from("<II",data,k*8)
            if c or r: codes[c]+=1; callers[r]+=1; allc.append((c,r))
    print("ring idx=%d"%i)
    print("distinct codes:", len(codes))
    print("top codes:", [(hex(k),v) for k,v in codes.most_common(20)])
    print("top callers:", [(hex(k),v) for k,v in callers.most_common(12)])
    def cat(c):
        x=c&0xFFFF
        if x<0x20: return "ctrl"
        if x<0x80: return "ascii"
        if 0x8140<=x<=0x9FFC: return "sjis"
        if 0xB0A1<=x<=0xC8FE: return "euckr"
        return "other"
    print("cats:", collections.Counter(cat(c) for c,_ in allc).most_common())
k32.CloseHandle(h); p.terminate(); print("done")
