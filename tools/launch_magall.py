"""Install the all-magenta font TLDAT + our patch DLL and LAUNCH the game, then exit
without terminating it (user will play and capture; we restore later)."""
import subprocess, os, sys, shutil, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
WORK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
R01 = os.path.join(GAME, "P12E", "Data", "TOS_Server", "Archive", "Release", "R01", "WIN")
SRC = os.path.join(WORK, sys.argv[1] if len(sys.argv) > 1 else "tpmagall")
KORFNT = os.path.join(GAME, "korfnt", "korfnt.dll")
REAL = os.path.join(GAME, "korfnt", "korfnt.dll.real")
DLL = os.path.join(WORK, "korfnt_logger8.dll")


def cp(a, b):
    for _ in range(60):
        try:
            shutil.copy2(a, b); return True
        except PermissionError:
            time.sleep(0.5)
    return False


if os.path.exists(os.path.join(GAME, "krcodes.bin")):
    os.remove(os.path.join(GAME, "krcodes.bin"))
if not os.path.exists(REAL):
    shutil.copy2(KORFNT, REAL)
print("data swap:", cp(os.path.join(SRC, "TLFILE.TLDAT"), os.path.join(R01, "TLFILE.TLDAT")),
      cp(os.path.join(SRC, "FILEHEADER.TOFHDB"), os.path.join(R01, "FILEHEADER.TOFHDB")))
print("dll install:", cp(DLL, KORFNT))
p = subprocess.Popen([os.path.join(GAME, "TOS.exe")], cwd=GAME)
print("LAUNCHED pid", p.pid, "- NOT terminating; play, capture, then tell the assistant.")
