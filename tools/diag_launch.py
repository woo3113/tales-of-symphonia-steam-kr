"""Launch TOS.exe and watch it for N seconds; report exit code + window titles.
Does not modify anything. Usage: diag_launch.py [seconds]"""
import subprocess, time, os, sys, ctypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
SEC = int(sys.argv[1]) if len(sys.argv) > 1 else 20
u32 = ctypes.windll.user32

def titles():
    out = []
    EP = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(h, l):
        b = ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(h, b, 256)
        if b.value:
            out.append(b.value)
        return True
    u32.EnumWindows(EP(cb), 0)
    return out

p = subprocess.Popen([os.path.join(GAME, "TOS.exe")], cwd=GAME)
print("pid", p.pid)
for i in range(SEC):
    time.sleep(1)
    rc = p.poll()
    if rc is not None:
        print("exited after %ds rc=%d (0x%08X)" % (i + 1, rc, rc & 0xffffffff))
        break
    if (i + 1) % 4 == 0:
        ts = [t for t in titles() if "Symphonia" in t or "Tales" in t]
        print("t=%ds alive; symphonia-windows=%r" % (i + 1, ts))
else:
    print("still alive after %ds" % SEC)
try:
    p.terminate()
except Exception:
    pass
time.sleep(1)
print("done")
