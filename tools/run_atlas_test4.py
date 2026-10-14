"""Atlas test v2 (corrected page mapping): swap data, run, screenshot every 4s."""
import subprocess, time, struct, os, sys, shutil, ctypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
WORK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
R01 = os.path.join(GAME, "P12E", "Data", "TOS_Server", "Archive", "Release", "R01", "WIN")
TP = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WORK, "tp"); BAK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\backup"
OUT = os.path.join(GAME, "krcodes.bin"); KORFNT = os.path.join(GAME, "korfnt", "korfnt.dll")
REAL = os.path.join(GAME, "korfnt", "korfnt.dll.real"); DLL = os.path.join(WORK, "korfnt_logger8.dll")
SHOTS = os.path.join(WORK, sys.argv[3] if len(sys.argv) > 3 else "shots4"); os.makedirs(SHOTS, exist_ok=True)
u32 = ctypes.windll.user32
TOTAL = int(sys.argv[1]) if len(sys.argv) > 1 else 120


def cp(a, b):
    for _ in range(60):
        try:
            shutil.copy2(a, b); return True
        except PermissionError:
            time.sleep(0.5)
    return False


def key(vk):
    found = []
    EP = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(h, l):
        b = ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(h, b, 256)
        if b.value and "Symphonia" in b.value:
            found.append(h)
        return True
    u32.EnumWindows(EP(cb), 0)
    if found:
        u32.SetForegroundWindow(found[0])
    time.sleep(0.15)
    u32.keybd_event(vk, 0, 0, 0); time.sleep(0.05); u32.keybd_event(vk, 0, 2, 0)


try:
    print("swap:", cp(os.path.join(TP, "TLFILE.TLDAT"), os.path.join(R01, "TLFILE.TLDAT")),
          cp(os.path.join(TP, "FILEHEADER.TOFHDB"), os.path.join(R01, "FILEHEADER.TOFHDB")))
    if os.path.exists(OUT):
        os.remove(OUT)
    if not os.path.exists(REAL):
        shutil.copy2(KORFNT, REAL)
    print("install:", cp(DLL, KORFNT))
    p = subprocess.Popen([os.path.join(GAME, "TOS.exe")], cwd=GAME)
    print("pid", p.pid)
    for el in range(4, TOTAL + 1, 4):
        time.sleep(4)
        if p.poll() is not None:
            print("EXITED early", p.returncode, hex(p.returncode & 0xffffffff)); break
        if el in (20, 28, 36, 44, 52, 60, 68, 76, 84, 92, 100, 108, 116):
            key(0x0D)
        if el >= 24:
            subprocess.run(["ffmpeg", "-y", "-f", "gdiGrab", "-i", "desktop", "-frames:v", "1",
                            os.path.join(SHOTS, "t%03d.png" % el)], capture_output=True)
            ks = ""
            if os.path.exists(OUT) and os.path.getsize(OUT) >= 8 + 4096 * 16:
                d = open(OUT, "rb").read(); i0, ik = struct.unpack_from("<II", d, 0)
                ks = "loop=%d korean=%d" % (i0, ik)
            print("t=%ds %s" % (el, ks))
finally:
    try: p.terminate()
    except Exception: pass
    time.sleep(2)
    print("restore dll:", cp(REAL, KORFNT))
    print("restore data:", cp(os.path.join(BAK, "TLFILE.TLDAT.orig"), os.path.join(R01, "TLFILE.TLDAT")),
          cp(os.path.join(BAK, "FILEHEADER.TOFHDB.orig"), os.path.join(R01, "FILEHEADER.TOFHDB")))
    for f in (OUT, os.path.join(GAME, "korfnt", "korfnt.dll.real")):
        try: os.remove(f)
        except Exception: pass
    print("done; TLDAT:",
          __import__("hashlib").sha256(open(os.path.join(R01, "TLFILE.TLDAT"), "rb").read()).hexdigest().upper())
