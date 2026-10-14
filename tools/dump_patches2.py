import subprocess, time, sys, os, ctypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"; TOS=os.path.join(GAME,"TOS.exe")
orig=open(TOS,"rb").read()
def ob(va,n): return orig[va-0x400000:va-0x400000+n]
k32=ctypes.WinDLL("kernel32", use_last_error=True)
FOUND=[0x57A81C,0x554E1E,0x57A990,0x578680,0x594CDB,0x57ACD0,0x4D783A,0x4D7C86,0x4D77C4,0x62666E,0x53281B,0x57AD04]
p=subprocess.Popen([TOS], cwd=GAME); print("pid",p.pid)
h=k32.OpenProcess(0x410,False,p.pid)
def rd(a,n):
    b=(ctypes.c_char*n)(); c=ctypes.c_size_t(0)
    return b.raw if k32.ReadProcessMemory(h,ctypes.c_void_p(a),b,n,ctypes.byref(c)) else None
time.sleep(20)
print("=== memory around each found pattern (orig vs mem, window foundAddr-16..+16) ===")
for f in FOUND:
    base=f-16
    o=ob(base,40); m=rd(base,40)
    diff=[i for i in range(40) if m and m[i]!=o[i]]
    if not diff:
        print("0x%08X (found %08X): SAME"%(base,f)); continue
    print("0x%08X (found %08X): DIFF at +%s"%(base,f,[hex(d) for d in diff]))
    print("   orig: %s"%o.hex())
    print("   mem : %s"%m.hex())
p.terminate(); print("done")
