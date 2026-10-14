"""Install a data build + DLL only (do NOT launch the game)."""
import os, sys, shutil, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
WORK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
R01 = os.path.join(GAME, "P12E", "Data", "TOS_Server", "Archive", "Release", "R01", "WIN")
DATADIR = os.path.join(WORK, sys.argv[1] if len(sys.argv) > 1 else "tppal")
DLLNAME = sys.argv[2] if len(sys.argv) > 2 else "korfnt_logger9.dll"
KORFNT = os.path.join(GAME, "korfnt", "korfnt.dll")
REAL = os.path.join(GAME, "korfnt", "korfnt.dll.real")


def cp(a, b):
    for _ in range(60):
        try:
            shutil.copy2(a, b); return True
        except PermissionError:
            time.sleep(0.5)
    return False


print("data:", cp(os.path.join(DATADIR, "TLFILE.TLDAT"), os.path.join(R01, "TLFILE.TLDAT")),
      cp(os.path.join(DATADIR, "FILEHEADER.TOFHDB"), os.path.join(R01, "FILEHEADER.TOFHDB")))
if not os.path.exists(REAL):
    shutil.copy2(KORFNT, REAL)
print("dll:", cp(os.path.join(WORK, DLLNAME), KORFNT))
print("INSTALLED (game not launched). data=%s dll=%s" % (os.path.basename(DATADIR), DLLNAME))
