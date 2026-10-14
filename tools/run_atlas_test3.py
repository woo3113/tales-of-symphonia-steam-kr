"""Swap atlas data, run longer, press Enter periodically to advance dialogue, screenshot."""
import subprocess, time, struct, os, sys, shutil, ctypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
WORK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
R01 = os.path.join(GAME, "P12E", "Data", "TOS_Server", "Archive", "Release", "R01", "WIN")
TP = os.path.join(WORK, "tp"); BAK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\backup"
OUT = os.path.join(GAME, "krcodes.bin"); KORFNT = os.path.join(GAME, "korfnt", "korfnt.dll")
REAL = os.path.join(GAME, "korfnt", "korfnt.dll.real"); DLL = os.path.join(WORK, "korfnt_logger8.dll")
SHOTS = os.path.join(WORK, "shots3"); os.makedirs(SHOTS, exist_ok=True)
u32 = ctypes.windll.user32


def cp(a, b):
    for _ in range(60):
        try:
            shutil.copy2(a, b); return True
        except PermissionError:
            time.sleep(0.5)
    return False


def hwnd_of():
    found = []
    EP = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(h, l):
        b = ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(h, b, 256)
        if b.value and "Symphonia" in b.value:
            found.append(h)
        return True
    u32.EnumWindows(EP(cb), 0)
    return found[0] if found else None


def key(vk):
    h = hwnd_of()
    if h:
        u32.SetForegroundWindow(h)
    time.sleep(0.15)
    u32.keybd_event(vk, 0, 0, 0); time.sleep(0.06); u32.keybd_event(vk, 0, 2, 0)


print("swap:", cp(os.path.join(TP, "TLFILE.TLDAT"), os.path.join(R01, "TLFILE.TLDAT")),
      cp(os.path.join(TP, "FILEHEADER.TOFHDB"), os.path.join(R01, "FILEHEADER.TOFHDB")))
if os.path.exists(OUT):
    os.remove(OUT)
if not os.path.exists(REAL):
    shutil.copy2(KORFNT, REAL)
print("install:", cp(DLL, KORFNT))
p = subprocess.Popen([os.path.join(GAME, "TOS.exe")], cwd=GAME)
print("pid", p.pid)
TOTAL = int(sys.argv[1]) if len(sys.argv) > 1 else 200
try:
    el = 0
    for t in range(TOTAL // 2):
        time.sleep(2)
        el += 2
        if p.poll() is not None:
            print("EXITED early", p.returncode, hex(p.returncode & 0xffffffff)); break
        if el >= 10 and el % 6 == 0:
            key(0x0D)  # Enter
        if el >= 40 and el % 10 == 0:
            subprocess.run(["ffmpeg", "-y", "-f", "gdiGrab", "-i", "desktop", "-frames:v", "1",
                            os.path.join(SHOTS, "t%03d.png" % el)], capture_output=True)
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
