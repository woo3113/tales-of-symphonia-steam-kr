import ctypes, subprocess, time, struct, sys, os
from ctypes import wintypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
k32=ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_VM_READ=0x10; PROCESS_QUERY_INFORMATION=0x400
class MBI(ctypes.Structure):
    _fields_=[("BaseAddress",ctypes.c_void_p),("AllocationBase",ctypes.c_void_p),
              ("AllocationProtect",wintypes.DWORD),("RegionSize",ctypes.c_size_t),
              ("State",wintypes.DWORD),("Protect",wintypes.DWORD),("Type",wintypes.DWORD)]
p=subprocess.Popen([os.path.join(GAME,"TOS.exe")], cwd=GAME)
time.sleep(9)
h=k32.OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION, False, p.pid)
def rd(addr,size):
    buf=(ctypes.c_char*size)(); n=ctypes.c_size_t(0)
    if k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(n)): return buf.raw
    return None
addr=0x400000; end=0x400000+0x2F00000
found=[]
while addr<end:
    mbi=MBI()
    if not k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)): break
    base=mbi.BaseAddress or 0
    if mbi.State==0x1000:  # MEM_COMMIT
        # check first bytes for our cave signature
        d=rd(base,8)
        if d and d[:4]==b"\x52\x51\x8b\x15":
            found.append((base, mbi.RegionSize, mbi.Protect))
    nxt=(mbi.BaseAddress or 0)+(mbi.RegionSize or 0x1000)
    if nxt<=addr: nxt=addr+0x1000
    addr=nxt
print("regions with cave signature:")
for b,sz,pr in found: print("  base=0x%08X size=0x%X protect=0x%X"%(b,sz,pr))
# also report region covering 0x2AFF000
mbi=MBI(); k32.VirtualQueryEx(h, ctypes.c_void_p(0x2AFF000), ctypes.byref(mbi), ctypes.sizeof(mbi))
print("region @0x2AFF000: base=0x%08X size=0x%X state=0x%X protect=0x%X type=0x%X"%(
    mbi.BaseAddress or 0, mbi.RegionSize, mbi.State, mbi.Protect, mbi.Type))
d=rd(0x2AFF000,16); print("bytes@0x2AFF000:", d.hex() if d else None)
d=rd(0x57A810,6); print("bytes@0x57A810:", d.hex() if d else None)
k32.CloseHandle(h); p.terminate()
