"""Swap atlas data, run, focus window, send keys to skip intro, screenshot periodically."""
import subprocess, time, struct, os, sys, shutil, ctypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
WORK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
R01 = os.path.join(GAME, "P12E", "Data", "TOS_Server", "Archive", "Release", "R01", "WIN")
TP = os.path.join(WORK, "tp"); BAK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\backup"
OUT = os.path.join(GAME, "krcodes.bin"); KORFNT = os.path.join(GAME, "korfnt", "korfnt.dll")
REAL = os.path.join(GAME, "korfnt", "korfnt.dll.real"); DLL = os.path.join(WORK, "korfnt_logger8.dll")
SHOTS = os.path.join(WORK, "shots2"); os.makedirs(SHOTS, exist_ok=True)
u32 = ctypes.windll.user32
u32.SetProcessDPIAware()


def cp(a, b):
    for _ in range(60):
        try:
            shutil.copy2(a, b); return True
        except PermissionError:
            time.sleep(0.5)
    return False


def focus_and_key(vk):
    h = u32.GetForegroundWindow()
    # brute force: find window whose title contains 'Symphonia'
    found = []
    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(hwnd, l):
        buf = ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(hwnd, buf, 256)
        if buf.value and ("Symphonia" in buf.value or "TOS" in buf.value):
            found.append((hwnd, buf.value))
        return True
    u32.EnumWindows(EnumProc(cb), 0)
    for hwnd, t in found:
        u32.SetForegroundWindow(hwnd)
    time.sleep(0.2)
    u32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    u32.keybd_event(vk, 0, 2, 0)
    return found


print("swap:", cp(os.path.join(TP, "TLFILE.TLDAT"), os.path.join(R01, "TLFILE.TLDAT")),
      cp(os.path.join(TP, "FILEHEADER.TOFHDB"), os.path.join(R01, "FILEHEADER.TOFHDB")))
if os.path.exists(OUT):
    os.remove(OUT)
if not os.path.exists(REAL):
    shutil.copy2(KORFNT, REAL)
print("install:", cp(DLL, KORFNT))
p = subprocess.Popen([os.path.join(GAME, "TOS.exe")], cwd=GAME)
print("pid", p.pid)
try:
    for t in range(100 // 4):
        time.sleep(4)
        el = 4 * (t + 1)
        if p.poll() is not None:
            print("EXITED early", p.returncode, hex(p.returncode & 0xffffffff)); break
        if el in (12, 20, 28, 36, 44, 52):
            f = focus_and_key(0x0D)  # Enter
            print("sent Enter; windows:", f)
        if el in (30, 40, 50, 60, 70, 80, 90):
            subprocess.run(["ffmpeg", "-y", "-f", "gdiGrab", "-i", "desktop", "-frames:v", "1",
                            os.path.join(SHOTS, "t%02d.png" % el)], capture_output=True)
            ks = ""
            if os.path.exists(OUT) and os.path.getsize(OUT) >= 8 + 4096 * 16:
                d = open(OUT, "rb").read(); i0, ik = struct.unpack_from("<II", d, 0)
                ks = "loop=%d korean=%d" % (i0, ik)
            print("t=%ds shot %s" % (el, ks))
finally:
    try: p.terminate()
    except Exception: pass
    time.sleep(1.5)
    print("restore dll:", cp(REAL, KORFNT))
    print("restore data:", cp(os.path.join(BAK, "TLFILE.TLDAT.orig"), os.path.join(R01, "TLFILE.TLDAT")),
          cp(os.path.join(BAK, "FILEHEADER.TOFHDB.orig"), os.path.join(R01, "FILEHEADER.TOFHDB")))
