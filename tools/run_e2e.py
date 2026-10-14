"""End-to-end test: (data must already be swapped to the Korean patch) run game with
logger8, take a screenshot, collect the Korean-hit log, restore korfnt.dll."""
import subprocess, time, struct, os, sys, shutil, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
WORK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
OUT = os.path.join(GAME, "krcodes.bin")
RING = 4096; HDR = 8
KORFNT = os.path.join(GAME, "korfnt", "korfnt.dll")
REAL = os.path.join(GAME, "korfnt", "korfnt.dll.real")
DLL = os.path.join(WORK, "korfnt_logger8.dll")
SHOT = os.path.join(WORK, "e2e_shot.png")
WAIT = int(sys.argv[1]) if len(sys.argv) > 1 else 60


def cp(a, b):
    for _ in range(40):
        try:
            shutil.copy2(a, b); return True
        except PermissionError:
            time.sleep(0.5)
    return False


if os.path.exists(OUT):
    os.remove(OUT)
if not os.path.exists(REAL):
    shutil.copy2(KORFNT, REAL)
print("install:", cp(DLL, KORFNT))
p = subprocess.Popen([os.path.join(GAME, "TOS.exe")], cwd=GAME)
print("pid", p.pid)
best = None
shot_done = False
try:
    for t in range(WAIT // 4):
        time.sleep(4)
        el = 4 * (t + 1)
        if p.poll() is not None:
            print("EXITED early code", p.returncode, hex(p.returncode & 0xffffffff)); break
        if os.path.exists(OUT):
            d = open(OUT, "rb").read()
            if len(d) >= HDR + RING * 16:
                i0, ik = struct.unpack_from("<II", d, 0)
                print("t=%ds loop=%d korean=%d" % (el, i0, ik))
                if i0 > 0:
                    best = d
        if not shot_done and el >= 24:
            subprocess.run(["ffmpeg", "-y", "-f", "gdiGrab", "-i", "desktop", "-frames:v", "1", SHOT],
                           capture_output=True)
            shot_done = True
            print("screenshot:", os.path.exists(SHOT))
        if best is not None and shot_done and el >= 32:
            break
finally:
    try: p.terminate()
    except Exception: pass
    time.sleep(1.5)
    print("restore:", cp(REAL, KORFNT))
if best is None and os.path.exists(OUT):
    best = open(OUT, "rb").read()
if not best:
    print("NO LOG"); sys.exit()
open(os.path.join(WORK, "krcodes8.bin"), "wb").write(best)
i0, ik = struct.unpack_from("<II", best, 0)
lp = [struct.unpack_from("<II", best, HDR + 8 * k) for k in range(RING)]
kr = [struct.unpack_from("<II", best, HDR + RING * 8 + 8 * k) for k in range(RING)]
print("loop idx", i0, "korean idx", ik)
for a, b in lp[:10]:
    by = struct.pack("<I", b)
    print("   ptr=%08X %s" % (a, "".join(chr(c) if 32 <= c < 127 else "." for c in by)))
hit = kr[:min(ik, 600)]
res = []
for a, b in hit:
    if 0xB0A1 <= a <= 0xC8FE and 0xA1 <= (a & 0xFF) <= 0xFE:
        idx = ((a >> 8) - 0xB0) * 94 + ((a & 0xFF) - 0xA1)
        res.append((a, 0x4000 + idx))
print("valid korean codes:", len(res), "distinct:", len(set(a for a, _ in res)))
print("  sample:", [(hex(a), hex(g)) for a, g in res[:20]])
badv = [a for a, _ in hit if not (0xB0A1 <= a <= 0xC8FE and 0xA1 <= (a & 0xFF) <= 0xFE)]
print("  invalid-range hits:", len(badv), [hex(x) for x in badv[:10]])
try:
    bs = b"".join(struct.pack(">H", a) for a, _ in hit[:400])
    txt = bs.decode("cp949", "replace")
except Exception:
    txt = ""
print("  decoded(CP949) sample:", txt[:160].replace("\r", " ").replace("\n", " "))
