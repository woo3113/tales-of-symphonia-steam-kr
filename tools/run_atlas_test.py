"""Swap in the atlas-patched data, run with logger8, take periodic screenshots."""
import subprocess, time, struct, os, sys, shutil, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
WORK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
R01 = os.path.join(GAME, "P12E", "Data", "TOS_Server", "Archive", "Release", "R01", "WIN")
TP = os.path.join(WORK, "tp")
BAK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\backup"
OUT = os.path.join(GAME, "krcodes.bin")
RING = 4096; HDR = 8
KORFNT = os.path.join(GAME, "korfnt", "korfnt.dll")
REAL = os.path.join(GAME, "korfnt", "korfnt.dll.real")
DLL = os.path.join(WORK, "korfnt_logger8.dll")
SHOTS = os.path.join(WORK, "shots")
WAIT = int(sys.argv[1]) if len(sys.argv) > 1 else 72
os.makedirs(SHOTS, exist_ok=True)


def cp(a, b):
    for _ in range(60):
        try:
            shutil.copy2(a, b); return True
        except PermissionError:
            time.sleep(0.5)
    return False


print("swap data:", cp(os.path.join(TP, "TLFILE.TLDAT"), os.path.join(R01, "TLFILE.TLDAT")),
      cp(os.path.join(TP, "FILEHEADER.TOFHDB"), os.path.join(R01, "FILEHEADER.TOFHDB")))
if os.path.exists(OUT):
    os.remove(OUT)
if not os.path.exists(REAL):
    shutil.copy2(KORFNT, REAL)
print("install:", cp(DLL, KORFNT))
p = subprocess.Popen([os.path.join(GAME, "TOS.exe")], cwd=GAME)
print("pid", p.pid)
try:
    for t in range(WAIT // 4):
        time.sleep(4)
        el = 4 * (t + 1)
        if p.poll() is not None:
            print("EXITED early", p.returncode, hex(p.returncode & 0xffffffff)); break
        ks = ""
        if os.path.exists(OUT) and os.path.getsize(OUT) >= HDR + RING * 16:
            d = open(OUT, "rb").read(); i0, ik = struct.unpack_from("<II", d, 0)
            ks = "loop=%d korean=%d" % (i0, ik)
        if el >= 24:
            subprocess.run(["ffmpeg", "-y", "-f", "gdiGrab", "-i", "desktop", "-frames:v", "1",
                            os.path.join(SHOTS, "t%02d.png" % el)], capture_output=True)
        print("t=%ds %s" % (el, ks))
finally:
    try: p.terminate()
    except Exception: pass
    time.sleep(1.5)
    print("restore dll:", cp(REAL, KORFNT))
    print("restore data:", cp(os.path.join(BAK, "TLFILE.TLDAT.orig"), os.path.join(R01, "TLFILE.TLDAT")),
          cp(os.path.join(BAK, "FILEHEADER.TOFHDB.orig"), os.path.join(R01, "FILEHEADER.TOFHDB")))
