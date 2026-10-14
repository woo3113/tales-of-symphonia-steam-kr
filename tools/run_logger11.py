"""Run logger8 (full pipeline prototype) and report loop text + Korean hits."""
import subprocess, time, struct, os, sys, shutil, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
WORK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
OUT = os.path.join(GAME, "krcodes.bin")
RING = 4096; HDR = 8
KORFNT = os.path.join(GAME, "korfnt", "korfnt.dll")
REAL = os.path.join(GAME, "korfnt", "korfnt.dll.real")
DLL = sys.argv[1] if len(sys.argv) > 1 else "korfnt_logger8.dll"
WAIT = int(sys.argv[2]) if len(sys.argv) > 2 else 120


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
print("install:", cp(os.path.join(WORK, DLL), KORFNT))
p = subprocess.Popen([os.path.join(GAME, "TOS.exe")], cwd=GAME)
print("pid", p.pid)
best = None
try:
    for t in range(WAIT // 4):
        time.sleep(4)
        if p.poll() is not None:
            print("EXITED early code", p.returncode, hex(p.returncode & 0xffffffff)); break
        if os.path.exists(OUT) and os.path.getsize(OUT) >= HDR + RING * 16:
            d = open(OUT, "rb").read(); i0, ik = struct.unpack_from("<II", d, 0)
            print("t=%ds loop=%d korean=%d" % (4 * (t + 1), i0, ik))
            if i0 > 0:
                best = d; break
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
print("loop idx", i0, " korean idx", ik)
for a, b in lp[:25]:
    by = struct.pack("<I", b)
    print("   ptr=%08X %s" % (a, "".join(chr(c) if 32 <= c < 127 else "." for c in by)))
if ik:
    print("KOREAN hits (code, glyph):")
    for a, b in kr[:40]:
        print("   code=%04X glyph=%s" % (a, hex(b) if b else b))
else:
    print("KOREAN hits: none (expected with original data)")
