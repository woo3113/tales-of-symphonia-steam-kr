import ctypes, subprocess, time, struct, sys, os, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ctypes import wintypes
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
k32=ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_VM_READ=0x10; PROCESS_QUERY_INFORMATION=0x400
IDX_VA=0x2AFF040; BUF_VA=0x2AFF100; END_VA=BUF_VA+0x3F0000
p=subprocess.Popen([os.path.join(GAME,"TOS.exe")], cwd=GAME)
print("launched pid", p.pid)
h=k32.OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION, False, p.pid)
print("handle", h, "err", ctypes.get_last_error())
def rd(addr,size):
    buf=(ctypes.c_char*size)(); n=ctypes.c_size_t(0)
    ok=k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(n))
    return buf.raw if ok else None
# sample periodically
for t in range(6):
    time.sleep(5)
    d=rd(IDX_VA,4)
    if d:
        idx=struct.unpack("<I",d)[0]
        cnt=(idx-BUF_VA)//8
        print("  t=%2ds idx=0x%08X count=%d"%(5*(t+1), idx, cnt))
# final read
d=rd(IDX_VA,4); idx=struct.unpack("<I",d)[0]; cnt=(idx-BUF_VA)//8
cnt=min(cnt, 400000)
data=rd(BUF_VA, cnt*8)
codes=[]; callers=[]
if data:
    for i in range(0,len(data),8):
        c,r=struct.unpack_from("<II",data,i)
        codes.append(c); callers.append(r)
print("captured", len(codes))
cc=collections.Counter(codes)
print("distinct codes:", len(cc))
print("top codes:", [(hex(k),v) for k,v in cc.most_common(25)])
# categorize
def cat(c):
    x=c&0xFFFF
    if x<0x80: return "ascii"
    if 0x8140<=x<=0x9FFC: return "sjis_hi"
    if 0xE000<=x<=0xEFFF: return "sjis_user"
    if 0xB0A1<=x<=0xC8FE: return "euckr_hangul"
    return "other"
cats=collections.Counter(cat(c) for c in codes)
print("categories:", cats.most_common())
print("callers:", collections.Counter(callers).most_common(15))
# save
open(os.path.join(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work","logcodes.txt"),"w").write(
    "\n".join("%08X %08X"%(c,r) for c,r in zip(codes,callers)))
# stop
k32.CloseHandle(h)
p.terminate()
print("terminated")
