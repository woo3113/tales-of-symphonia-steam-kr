import subprocess, time, sys, os, ctypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
TOS=os.path.join(GAME,"TOS.exe")
orig=open(TOS,"rb").read()
def origb(va,n): return orig[va-0x400000:va-0x400000+n]
k32=ctypes.WinDLL("kernel32", use_last_error=True)
SITES=[0x57A81C,0x57A990,0x554E1E,0x578680,0x57ACD0,0x57AD04,0x53281B,0x4D77C4,0x4D783A,0x4D7C86,0x594CDB,0x62666E]
p=subprocess.Popen([TOS], cwd=GAME); print("pid",p.pid)
h=k32.OpenProcess(0x410,False,p.pid)
def rd(a,n):
    b=(ctypes.c_char*n)(); c=ctypes.c_size_t(0)
    return b.raw if k32.ReadProcessMemory(h,ctypes.c_void_p(a),b,n,ctypes.byref(c)) else None
# wait until korfnt has patched (poll first site)
for t in range(20):
    time.sleep(2)
    d=rd(0x57A81C,8)
    if d and d[:1]!=origb(0x57A81C,1):
        print("patched at t=%ds"%(2*(t+1))); break
print("\n=== diff at hook sites (orig vs memory) ===")
for va in SITES:
    o=origb(va,32); m=rd(va,32)
    if m is None: print("0x%08X: <unreadable>"%va); continue
    diff = "SAME" if m==o else "DIFF"
    print("0x%08X %s"%(va,diff))
    if m!=o:
        print("   orig: %s"%o.hex())
        print("   mem : %s"%m.hex())
p.terminate(); print("done")
