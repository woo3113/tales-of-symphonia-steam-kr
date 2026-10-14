import subprocess, time, sys, os, ctypes, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
TOS=os.path.join(GAME,"TOS.exe")
before=set(glob.glob(os.path.join(GAME,"**","*"), recursive=True))
k32=ctypes.WinDLL("kernel32", use_last_error=True)
p=subprocess.Popen([TOS], cwd=GAME); print("pid",p.pid)
time.sleep(25)
# new files
after=set(glob.glob(os.path.join(GAME,"**","*"), recursive=True))
new=[f for f in after-before]
print("new files in game dir:", new[:20])
# scan process memory for korfnt unique string "my_ASMHook"
h=k32.OpenProcess(0x410,False,p.pid)
class MBI(ctypes.Structure):
    _fields_=[("BaseAddress",ctypes.c_void_p),("AllocationBase",ctypes.c_void_p),("AllocationProtect",ctypes.c_ulong),("RegionSize",ctypes.c_size_t),("State",ctypes.c_ulong),("Protect",ctypes.c_ulong),("Type",ctypes.c_ulong)]
def rd(a,n):
    b=(ctypes.c_char*n)(); c=ctypes.c_size_t(0)
    return b.raw if k32.ReadProcessMemory(h,ctypes.c_void_p(a),b,n,ctypes.byref(c)) else None
needle=b"my_ASMHook"
found=[]
addr=0x10000000
while addr<0x70000000:
    mbi=MBI()
    if not k32.VirtualQueryEx(h,ctypes.c_void_p(addr),ctypes.byref(mbi),ctypes.sizeof(mbi)): break
    base=mbi.BaseAddress or 0
    if mbi.State==0x1000:
        d=rd(base,min(mbi.RegionSize,0x10000))
        if d and needle in d: found.append(hex(base))
    nxt=base+(mbi.RegionSize or 0x1000)
    if nxt<=addr: nxt=addr+0x1000
    addr=nxt
    if len(found)>3: break
print("regions containing 'my_ASMHook' (korfnt code):", found)
k32.CloseHandle(h); p.terminate(); print("done")
