import ctypes, subprocess, time, struct, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
k32=ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_VM_READ=0x10; PROCESS_QUERY_INFORMATION=0x400
p=subprocess.Popen([os.path.join(GAME,"TOS.exe")], cwd=GAME)
print("launched pid", p.pid)
h=k32.OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION, False, p.pid)
print("handle", h, "err", ctypes.get_last_error())
def rd(addr,size):
    buf=(ctypes.c_char*size)(); n=ctypes.c_size_t(0)
    ok=k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(n))
    return buf.raw if ok else None
for t in range(5):
    time.sleep(6)
    alive = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(ctypes.c_ulong())) if h else 0
    ex=ctypes.c_ulong(); k32.GetExitCodeProcess(h, ctypes.byref(ex))
    mz=rd(0x400000,2); hook=rd(0x57A810,6); cave=rd(0x2AFF000,8); idx=rd(0x2AFF040,4)
    print("t=%ds exitcode=%d MZ=%s hook=%s cave=%s idx=%s"%(
        6*(t+1), ex.value, mz, hook.hex() if hook else None, cave.hex() if cave else None,
        hex(struct.unpack('<I',idx)[0]) if idx else None))
    if idx:
        cnt=(struct.unpack('<I',idx)[0]-0x2AFF100)//8
        print("   count=",cnt)
    if ex.value!=259:  # STILL_ACTIVE=259
        print("   process exited"); break
k32.CloseHandle(h)
p.terminate()
print("done")
