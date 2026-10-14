import ctypes, subprocess, time, sys, os
from ctypes import wintypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
k32=ctypes.WinDLL("kernel32", use_last_error=True)
psapi=ctypes.WinDLL("psapi")
PROCESS_VM_READ=0x10; PROCESS_QUERY_INFORMATION=0x400
class MBI(ctypes.Structure):
    _fields_=[("BaseAddress",ctypes.c_void_p),("AllocationBase",ctypes.c_void_p),
              ("AllocationProtect",wintypes.DWORD),("RegionSize",ctypes.c_size_t),
              ("State",wintypes.DWORD),("Protect",wintypes.DWORD),("Type",wintypes.DWORD)]
p=subprocess.Popen([os.path.join(GAME,"TOS.exe")], cwd=GAME)
time.sleep(9)
h=k32.OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION, False, p.pid)
# module list
mods=(ctypes.c_void_p*1024)(); needed=wintypes.DWORD()
psapi.EnumProcessModules(h, mods, ctypes.sizeof(mods), ctypes.byref(needed))
nm=ctypes.create_unicode_buffer(260)
print("modules with base >= 0x2000000:")
for i in range(needed.value//ctypes.sizeof(ctypes.c_void_p)):
    b=mods[i] or 0
    if b>=0x2000000:
        psapi.GetModuleBaseNameW(h, ctypes.c_void_p(b), nm, 260)
        mi=MBI(); k32.VirtualQueryEx(h, ctypes.c_void_p(b), ctypes.byref(mi), ctypes.sizeof(mi))
        print("  base=0x%08X size=0x%X %s"%(b, mi.RegionSize, nm.value))
# image regions near 0x2AFF000
print("image regions 0x2000000..0x3000000:")
addr=0x2000000
while addr<0x3000000:
    mi=MBI()
    if not k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mi), ctypes.sizeof(mi)): break
    b=mi.BaseAddress or 0
    if mi.State==0x1000 and mi.Type==0x1000000:
        print("  0x%08X size=0x%X prot=0x%X"%(b,mi.RegionSize,mi.Protect))
    addr=(b+(mi.RegionSize or 0x1000))
    if addr<=b: break
k32.CloseHandle(h); p.terminate()
